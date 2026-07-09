"""
Flask extensions initialization for E-Council application.
Centralizes extension configuration and initialization.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer

# Initialize extensions without binding to app
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)
serializer = None  # Will be initialized with app config


def get_user_key():
    """Return a per-user rate limit key or fallback to remote address."""
    if current_user and current_user.is_authenticated:
        return str(current_user.users_id)
    return get_remote_address()


def init_extensions(app):
    """
    Initialize all Flask extensions with the application.

    Args:
        app: Flask application instance
    """
    global serializer

    # Initialize SQLAlchemy
    db.init_app(app)

    # Initialize Flask-Migrate
    migrate.init_app(app, db)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "You need to be logged in to access this page."
    login_manager.login_message_category = "error"

    # Initialize Flask-Mail
    mail.init_app(app)

    # Initialize CSRF Protection
    csrf.init_app(app)

    # Initialize Flask-Limiter
    limiter.init_app(app)
    limiter.enabled = app.config.get("RATELIMIT_ENABLED", True)

    # Initialize URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])


def get_serializer():
    """
    Get the URLSafeTimedSerializer instance.

    Returns:
        URLSafeTimedSerializer instance or None if not initialized
    """
    return serializer
