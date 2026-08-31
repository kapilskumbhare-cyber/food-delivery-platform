import os


class Config:
    """
    All values are read from environment variables so nothing secret
    ever lives in the codebase. When you get to Docker/K8s, these become
    ConfigMap entries (non-secret) and Secret entries (SECRET_KEY, DB
    password, JWT key).
    """

    # --- Database ---
    DB_USER = os.environ.get("DB_USER", "food_user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "changeme")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "food_delivery")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-prod")

    # --- App ---
    ENV = os.environ.get("FLASK_ENV", "development")
