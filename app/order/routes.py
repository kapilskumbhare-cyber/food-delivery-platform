from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from app.models import db, Order, OrderItem, MenuItem, Restaurant
from app.decorators import role_required

order_bp = Blueprint("order", __name__, url_prefix="/api/orders")

# Valid forward transitions a restaurant can make on a paid order.
NEXT_STATUS = {
    "PAYMENT_SUCCESS": {"RESTAURANT_ACCEPTED", "ORDER_REJECTED"},
    "RESTAURANT_ACCEPTED": {"PREPARING"},
    "PREPARING": {"READY"},
    "READY": {"DELIVERED"},
}


# ---------- Customer: place an order from cart items ----------

@order_bp.route("", methods=["POST"])
@role_required("customer")
def place_order():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    restaurant_id = data.get("restaurant_id")
    cart_items = data.get("items", [])  # [{menu_item_id, quantity}, ...]

    if not restaurant_id or not cart_items:
        return jsonify({"error": "restaurant_id and a non-empty items list are required"}), 400

    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant or restaurant.status != "active":
        return jsonify({"error": "restaurant not available"}), 404

    order = Order(user_id=user_id, restaurant_id=restaurant.id, status="PAYMENT_PENDING")
    total = 0

    for entry in cart_items:
        menu_item = MenuItem.query.filter_by(
            id=entry.get("menu_item_id"), restaurant_id=restaurant.id
        ).first()
        quantity = int(entry.get("quantity", 1))

        if not menu_item or not menu_item.availability or quantity < 1:
            return jsonify({"error": f"invalid or unavailable item: {entry.get('menu_item_id')}"}), 400

        line_total = float(menu_item.price) * quantity
        total += line_total
        order.items.append(
            OrderItem(menu_item_id=menu_item.id, quantity=quantity, price_at_order=menu_item.price)
        )

    order.total_amount = total
    db.session.add(order)
    db.session.commit()

    return jsonify(order.to_dict()), 201


# ---------- Views ----------

@order_bp.route("/my", methods=["GET"])
@role_required("customer")
def my_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


@order_bp.route("/restaurant", methods=["GET"])
@role_required("restaurant")
def incoming_orders():
    user_id = get_jwt_identity()
    restaurant = Restaurant.query.filter_by(owner_user_id=user_id).first()
    if not restaurant:
        return jsonify({"error": "you do not have a restaurant profile"}), 404

    orders = (
        Order.query.filter_by(restaurant_id=restaurant.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return jsonify([o.to_dict() for o in orders]), 200


@order_bp.route("/<int:order_id>", methods=["GET"])
@role_required("customer", "restaurant", "admin")
def get_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404

    is_owner_customer = str(order.user_id) == str(user_id)
    is_owner_restaurant = order.restaurant and str(order.restaurant.owner_user_id) == str(user_id)

    from flask_jwt_extended import get_jwt
    role = get_jwt().get("role")

    if not (is_owner_customer or is_owner_restaurant or role == "admin"):
        return jsonify({"error": "not authorized to view this order"}), 403

    return jsonify(order.to_dict()), 200


# ---------- Restaurant: advance order status ----------

@order_bp.route("/<int:order_id>/status", methods=["PATCH"])
@role_required("restaurant")
def update_order_status(order_id):
    user_id = get_jwt_identity()
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404

    if not order.restaurant or str(order.restaurant.owner_user_id) != str(user_id):
        return jsonify({"error": "not your order to update"}), 403

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    allowed = NEXT_STATUS.get(order.status, set())
    if new_status not in allowed:
        return jsonify({
            "error": f"cannot move from {order.status} to {new_status}",
            "allowed_next": sorted(allowed),
        }), 400

    order.status = new_status
    db.session.commit()
    return jsonify(order.to_dict()), 200


# ---------- Customer: cancel before payment succeeds ----------

@order_bp.route("/<int:order_id>/cancel", methods=["PATCH"])
@role_required("customer")
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.get(order_id)
    if not order or str(order.user_id) != str(user_id):
        return jsonify({"error": "order not found"}), 404

    if order.status not in ("PAYMENT_PENDING", "PAYMENT_FAILED"):
        return jsonify({"error": f"cannot cancel an order in status {order.status}"}), 400

    order.status = "CANCELLED"
    db.session.commit()
    return jsonify(order.to_dict()), 200
