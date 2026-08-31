from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

ALLOWED_ROLES = {"customer", "restaurant", "admin"}


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "customer")

    if not all([name, email, password]):
        return jsonify({"error": "name, email and password are required"}), 400

    if role not in ALLOWED_ROLES:
        return jsonify({"error": f"role must be one of {sorted(ALLOWED_ROLES)}"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"error": "account is disabled"}), 403

    # Embed role in the token so downstream routes can check permissions
    # without a DB lookup on every request.
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    return jsonify({"access_token": access_token, "user": user.to_dict()}), 200
