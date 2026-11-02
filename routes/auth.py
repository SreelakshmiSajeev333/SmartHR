from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from models import db, User


auth_bp = Blueprint("auth", __name__)


def redirect_logged_in_user():
    """Redirect authenticated users to their respective dashboard."""

    if session.get("user_id"):

        if session.get("user_role") == "hr":
            return redirect(url_for("hr.dashboard"))

        if session.get("user_role") == "employee":
            return redirect(url_for("employee.dashboard"))

    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    existing_session = redirect_logged_in_user()

    if existing_session:
        return existing_session

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please complete all fields.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "An account with this email already exists.",
                "danger"
            )
            return redirect(url_for("auth.register"))

        user = User(
            name=name,
            email=email,
            role="employee"
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            "Registration successful! Please log in.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    existing_session = redirect_logged_in_user()

    if existing_session:
        return existing_session

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if (
            user
            and user.is_active
            and user.role in ["employee", "hr"]
            and user.check_password(password)
        ):

            session.clear()

            session["user_id"] = user.id
            session["user_role"] = user.role

            flash("Welcome to SmartHR!", "success")

            if user.role == "hr":
                return redirect(url_for("hr.dashboard"))

            return redirect(url_for("employee.dashboard"))

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("auth.login"))