import os

from flask import Flask, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db

from routes.auth import auth_bp
from routes.employee import employee_bp
from routes.hr import hr_bp
from routes.hr_queries import hr_queries_bp


csrf = CSRFProtect()


def create_app():

    app = Flask(__name__)

    # Load application configuration
    app.config.from_object(Config)

    # Database initialization
    db.init_app(app)

    # CSRF protection
    csrf.init_app(app)

    # Session security settings
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Enable secure cookies only when using HTTPS
    app.config["SESSION_COOKIE_SECURE"] = (
        os.getenv("SESSION_COOKIE_SECURE", "0").lower()
        in ("1", "true", "yes")
    )

    # Ensure upload directory exists
    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    # Register application blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(hr_queries_bp)

    # Home route with role-based redirection
    @app.route("/")
    def home():

        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        if session.get("user_role") == "hr":
            return redirect(url_for("hr.dashboard"))

        if session.get("user_role") == "employee":
            return redirect(url_for("employee.dashboard"))

        session.clear()

        return redirect(url_for("auth.login"))

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":

    # Debug mode is disabled by default.
    # Set FLASK_DEBUG=1 to enable it during development.

    debug_mode = (
        os.getenv("FLASK_DEBUG", "0").lower()
        in ("1", "true", "yes")
    )

    app.run(debug=debug_mode)