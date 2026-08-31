from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, Restaurant, MenuItem
from app.decorators import role_required

restaurant_bp = Blueprint("restaurant", __name__, url_prefix="/api/restaurants")


def _get_owned_restaurant_or_error(restaurant_id, user_id):
    """Fetch a restaurant and confirm the current user owns it. Returns (restaurant, error_response)."""
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return None, (jsonify({"error": "restaurant not found"}), 404)
    if str(restaurant.owner_user_id) != str(user_id):
        return None, (jsonify({"error": "you do not own this restaurant"}), 403)
    return restaurant, None


# ---------- Public browse (customers, no auth required) ----------

@restaurant_bp.route("", methods=["GET"])
def list_restaurants():
    search = request.args.get("search", "").strip()
    query = Restaurant.query.filter_by(status="active")
    if search:
        query = query.filter(Restaurant.name.ilike(f"%{search}%"))
    restaurants = query.all()
    return jsonify([r.to_dict() for r in restaurants]), 200


@restaurant_bp.route("/<int:restaurant_id>", methods=["GET"])
def get_restaurant(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"error": "restaurant not found"}), 404
    data = restaurant.to_dict()
    data["menu"] = [item.to_dict() for item in restaurant.menu_items if item.availability]
    return jsonify(data), 200


# ---------- Restaurant-role management ----------

@restaurant_bp.route("", methods=["POST"])
@role_required("restaurant")
def create_restaurant():
    user_id = get_jwt_identity()

    if Restaurant.query.filter_by(owner_user_id=user_id).first():
        return jsonify({"error": "you already have a restaurant profile"}), 409

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    location = data.get("location")

    if not all([name, location]):
        return jsonify({"error": "name and location are required"}), 400

    restaurant = Restaurant(owner_user_id=user_id, name=name, location=location)
    db.session.add(restaurant)
    db.session.commit()

    return jsonify(restaurant.to_dict()), 201


@restaurant_bp.route("/<int:restaurant_id>", methods=["PATCH"])
@role_required("restaurant")
def update_restaurant(restaurant_id):
    user_id = get_jwt_identity()
    restaurant, error = _get_owned_restaurant_or_error(restaurant_id, user_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    for field in ("name", "location", "status"):
        if field in data:
            setattr(restaurant, field, data[field])

    db.session.commit()
    return jsonify(restaurant.to_dict()), 200


# ---------- Menu CRUD (restaurant-role, own restaurant only) ----------

@restaurant_bp.route("/<int:restaurant_id>/menu", methods=["POST"])
@role_required("restaurant")
def add_menu_item(restaurant_id):
    user_id = get_jwt_identity()
    restaurant, error = _get_owned_restaurant_or_error(restaurant_id, user_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    price = data.get("price")

    if not name or price is None:
        return jsonify({"error": "name and price are required"}), 400

    item = MenuItem(restaurant_id=restaurant.id, name=name, price=price)
    db.session.add(item)
    db.session.commit()

    return jsonify(item.to_dict()), 201


@restaurant_bp.route("/<int:restaurant_id>/menu/<int:item_id>", methods=["PATCH"])
@role_required("restaurant")
def update_menu_item(restaurant_id, item_id):
    user_id = get_jwt_identity()
    restaurant, error = _get_owned_restaurant_or_error(restaurant_id, user_id)
    if error:
        return error

    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first()
    if not item:
        return jsonify({"error": "menu item not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ("name", "price", "availability"):
        if field in data:
            setattr(item, field, data[field])

    db.session.commit()
    return jsonify(item.to_dict()), 200


@restaurant_bp.route("/<int:restaurant_id>/menu/<int:item_id>", methods=["DELETE"])
@role_required("restaurant")
def delete_menu_item(restaurant_id, item_id):
    user_id = get_jwt_identity()
    restaurant, error = _get_owned_restaurant_or_error(restaurant_id, user_id)
    if error:
        return error

    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first()
    if not item:
        return jsonify({"error": "menu item not found"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "menu item deleted"}), 200
