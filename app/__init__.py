from flask import Flask, jsonify
from flask_jwt_extended import JWTManager

from app.config import Config
from app.models import db, bcrypt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)

    from app.auth.routes import auth_bp
    from app.restaurant.routes import restaurant_bp
    from app.order.routes import order_bp
    from app.payment.routes import payment_bp
    from app.admin.routes import admin_bp
    from app.frontend.views import frontend_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(frontend_bp)

    @app.route("/health")
    def health():
        # This is what your K8s liveness/readiness probes will hit.
        return jsonify({"status": "ok"}), 200

    with app.app_context():
        db.create_all()

    return app
