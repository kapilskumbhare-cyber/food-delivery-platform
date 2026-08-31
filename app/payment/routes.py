import random

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from app.models import db, Order, Payment
from app.decorators import role_required

payment_bp = Blueprint("payment", __name__, url_prefix="/api/orders")


@payment_bp.route("/<int:order_id>/pay", methods=["POST"])
@role_required("customer")
def pay_order(order_id):
    """
    Simulated payment gateway. No real money moves.

    Body (optional): {"force_result": "SUCCESS" | "FAILED"}
    Without it, succeeds ~90% of the time — deliberately, so you have a
    realistic failure path to test order cancellation/retry against.
    """
    user_id = get_jwt_identity()
    order = Order.query.get(order_id)

    if not order or str(order.user_id) != str(user_id):
        return jsonify({"error": "order not found"}), 404

    if order.status != "PAYMENT_PENDING":
        return jsonify({"error": f"order is not awaiting payment (status: {order.status})"}), 400

    data = request.get_json(silent=True) or {}
    forced = data.get("force_result")

    if forced in ("SUCCESS", "FAILED"):
        result = forced
    else:
        result = "SUCCESS" if random.random() < 0.9 else "FAILED"

    payment = Payment(order_id=order.id, amount=order.total_amount, status=result)
    db.session.add(payment)

    order.status = "PAYMENT_SUCCESS" if result == "SUCCESS" else "PAYMENT_FAILED"

    db.session.commit()

    return jsonify({"order": order.to_dict(), "payment": payment.to_dict()}), 200
