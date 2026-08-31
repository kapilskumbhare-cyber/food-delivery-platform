from flask import Blueprint, jsonify

from app.models import db, User, Restaurant, Order
from app.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["PATCH"])
@role_required("admin")
def toggle_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    user.is_active = not user.is_active
    db.session.commit()
    return jsonify(user.to_dict()), 200


@admin_bp.route("/restaurants", methods=["GET"])
@role_required("admin")
def list_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([r.to_dict() for r in restaurants]), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/toggle-status", methods=["PATCH"])
@role_required("admin")
def toggle_restaurant(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"error": "restaurant not found"}), 404

    restaurant.status = "inactive" if restaurant.status == "active" else "active"
    db.session.commit()
    return jsonify(restaurant.to_dict()), 200


@admin_bp.route("/stats", methods=["GET"])
@role_required("admin")
def stats():
    status_counts = {}
    for status, count in db.session.query(Order.status, db.func.count(Order.id)).group_by(Order.status):
        status_counts[status] = count

    return jsonify({
        "total_users": User.query.count(),
        "total_restaurants": Restaurant.query.count(),
        "total_orders": Order.query.count(),
        "orders_by_status": status_counts,
    }), 200
