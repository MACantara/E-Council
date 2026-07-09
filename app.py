"""
E-Council Flask Application
Application factory pattern with modular structure
"""

import os
import sys

from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy import text

# Load environment variables from .env file
load_dotenv()

# Use PyMySQL as the MySQL driver if the native mysqlclient is not available
# This ensures the application runs on Windows without requiring mysqlclient.
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Import configuration
from config import AIConfig, CloudinaryConfig, DatabaseConfig, EmailConfig, get_config

# Import extensions
from extensions import db, init_extensions

# Import models for backward compatibility
# Import blueprints
from routes.account import account_bp
from routes.auth import auth_bp
from routes.board_resolutions import board_resolutions_bp
from routes.concept_papers import concept_papers_bp
from routes.dashboard import dashboard_bp
from routes.documentation import documentation_bp
from routes.events import events_bp
from routes.financial import financial_bp
from routes.meetings import meetings_bp

# Import utilities
from utils import register_error_handlers, register_filters
from utils.auth import load_user, unauthorized


def create_app(config_name=None):
    """
    Application factory function that creates and configures the Flask app.

    Args:
        config_name: Configuration environment name (development, production, testing)
                    If None, uses FLASK_ENV or defaults to development

    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__, template_folder="templates")

    # Determine the configuration class
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    config_class = get_config(config_name)

    # Load configuration from the selected class
    app.config.from_object(config_class)

    # Run any configuration-specific initialization (e.g. production logging)
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # Override SECRET_KEY with environment variable
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or app.config.get("SECRET_KEY")

    # Database configuration: use config class URI if defined, otherwise environment
    app.config["SQLALCHEMY_DATABASE_URI"] = getattr(
        config_class, "SQLALCHEMY_DATABASE_URI", DatabaseConfig.get_database_uri()
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = getattr(
        config_class, "SQLALCHEMY_TRACK_MODIFICATIONS", DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS
    )
    app.config["SQLALCHEMY_ECHO"] = getattr(config_class, "SQLALCHEMY_ECHO", DatabaseConfig.SQLALCHEMY_ECHO)

    # Mail configuration
    app.config["MAIL_SERVER"] = EmailConfig.MAIL_SERVER
    app.config["MAIL_PORT"] = EmailConfig.MAIL_PORT
    app.config["MAIL_USE_TLS"] = EmailConfig.MAIL_USE_TLS
    app.config["MAIL_USE_SSL"] = EmailConfig.MAIL_USE_SSL
    app.config["MAIL_USERNAME"] = EmailConfig.MAIL_USERNAME
    app.config["MAIL_PASSWORD"] = EmailConfig.MAIL_PASSWORD
    app.config["MAIL_DEFAULT_SENDER"] = (
        os.getenv("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_DEFAULT_SENDER") or EmailConfig.MAIL_DEFAULT_SENDER
    )

    # Initialize extensions
    init_extensions(app)

    # Configure Flask-Login
    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.user_loader(load_user)
    login_manager.unauthorized_handler(unauthorized)

    # Configure Cloudinary
    import cloudinary

    cloudinary.config(
        cloud_name=CloudinaryConfig.CLOUDINARY_CLOUD_NAME,
        api_key=CloudinaryConfig.CLOUDINARY_API_KEY,
        api_secret=CloudinaryConfig.CLOUDINARY_API_SECRET,
        secure=CloudinaryConfig.CLOUDINARY_SECURE,
    )

    # Configure Gemini AI
    import google.generativeai as genai

    genai.configure(api_key=AIConfig.GOOGLE_GEMINI_AI_API_KEY)

    # Initialize upload folder
    upload_folder = "uploads/receipts"
    os.makedirs(upload_folder, exist_ok=True)

    # Register custom Jinja2 filters
    register_filters(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    app.register_blueprint(account_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(documentation_bp)
    app.register_blueprint(financial_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(board_resolutions_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(concept_papers_bp)

    # Initialize serializer for events blueprint
    events_bp.init_serializer(app.config["SECRET_KEY"])

    # Register security headers handler
    @app.after_request
    def set_security_headers(response):
        response.headers.set("X-Frame-Options", "DENY")
        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://res.cloudinary.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers.set("Content-Security-Policy", csp)
        return response

    # Register index route
    @app.route("/")
    def index():
        return render_template("index.html")

    return app


def init_database(app):
    """
    Test the database connection and create all tables if they don't exist.

    Args:
        app: Flask application instance

    Returns:
        bool: True if the database is reachable and tables are created/verified,
              False otherwise.
    """
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            app.logger.info("Database connection successful.")
        except Exception as e:
            app.logger.error("Database connection failed: %s", e, exc_info=True)
            return False

        try:
            # Import all models so db.create_all() registers every table
            db.create_all()
            app.logger.info("Database tables created/verified successfully.")
            return True
        except Exception as e:
            app.logger.error("Failed to create database tables: %s", e, exc_info=True)
            return False


# For backward compatibility - create app instance
app = create_app()

if __name__ == "__main__":
    if not init_database(app):
        sys.exit(1)
    app.run(host="0.0.0.0", debug=True)
