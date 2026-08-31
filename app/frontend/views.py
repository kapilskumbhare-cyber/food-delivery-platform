from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__, template_folder="../templates", static_folder="../static")


@frontend_bp.route("/")
def home():
    return render_template("login.html")


@frontend_bp.route("/register")
def register_page():
    return render_template("register.html")


@frontend_bp.route("/restaurants")
def restaurants_page():
    return render_template("restaurants.html")


@frontend_bp.route("/restaurants/<int:restaurant_id>")
def menu_page(restaurant_id):
    return render_template("menu.html", restaurant_id=restaurant_id)


@frontend_bp.route("/cart")
def cart_page():
    return render_template("cart.html")


@frontend_bp.route("/orders")
def orders_page():
    return render_template("orders.html")


@frontend_bp.route("/my-restaurant")
def my_restaurant_page():
    return render_template("my_restaurant.html")
