"""
Configuration classes for E-Council application.
Provides environment-specific configuration management.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""

    # Flask Core Configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = False
    TESTING = False

    # Celery / Background task queue
    broker_url = os.getenv("BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("RESULT_BACKEND", broker_url)
    task_always_eager = os.getenv("BROKER_URL") is None

    # Upload Configuration
    UPLOAD_FOLDER = "uploads/receipts"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "1000 per minute"

    # Session Configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure upload folder exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False

    # Development-specific overrides
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False

    # Production-specific security settings
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_SAMESITE = "Strict"

    # Use Redis for rate limiting in production if available
    RATELIMIT_STORAGE_URI = os.getenv("REDIS_URL", "memory://")

    @staticmethod
    def init_app(app):
        """Initialize production configuration, logging, and optional Sentry."""
        Config.init_app(app)

        # Ensure logs directory exists and configure rotating file handler
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, "app.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

        # Optionally initialize Sentry if DSN is configured
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration

                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[FlaskIntegration()],
                    traces_sample_rate=0.1,
                )
            except ImportError:
                app.logger.warning("SENTRY_DSN is set but sentry-sdk is not installed")


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = True
    TESTING = True

    # Testing-specific overrides
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SESSION_COOKIE_SECURE = False

    # Rate limiting is enabled but disabled at runtime in conftest.py by default;
    # rate-limit tests explicitly enable it.
    RATELIMIT_ENABLED = True

    # Use an in-memory SQLite database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Provide a default secret key for tests so tokens/serializers work without env vars
    SECRET_KEY = "test-secret-key"

    # Provide a default mail sender for tests so Flask-Mail messages validate
    MAIL_DEFAULT_SENDER = "test@example.com"


class DatabaseConfig:
    """Database configuration settings."""

    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL") or "sqlite:///e_council.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL query logging

    @staticmethod
    def get_database_uri():
        """Get database URI from environment variables.

        Supports SQLALCHEMY_DATABASE_URI, DATABASE_URL, and falls back to a local
        SQLite file so the application can start without any database configuration.
        """
        return os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL") or "sqlite:///e_council.db"

    @staticmethod
    def get_engine_options(uri=None):
        """Return SQLAlchemy engine options based on the configured database URI.

        SQLite uses sensible defaults for local development. MySQL and PostgreSQL
        use connection-pool resilience options (pool_pre_ping and pool_recycle).
        """
        uri = uri or DatabaseConfig.get_database_uri()
        if not uri:
            return {}
        if uri.startswith("sqlite"):
            return {
                "connect_args": {"check_same_thread": False},
            }
        return {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }


class EmailConfig:
    """Email configuration settings."""

    # Flask Mail Configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # Email Settings
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False


class CloudinaryConfig:
    """Cloudinary configuration settings."""

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    CLOUDINARY_SECURE = True

    @staticmethod
    def configure():
        """Configure Cloudinary with environment variables."""
        import cloudinary

        cloudinary.config(
            cloud_name=CloudinaryConfig.CLOUDINARY_CLOUD_NAME,
            api_key=CloudinaryConfig.CLOUDINARY_API_KEY,
            api_secret=CloudinaryConfig.CLOUDINARY_API_SECRET,
            secure=CloudinaryConfig.CLOUDINARY_SECURE,
        )


class AIConfig:
    """AI configuration settings."""

    # Google Gemini AI Configuration
    GOOGLE_GEMINI_AI_API_KEY = os.getenv("GOOGLE_GEMINI_AI_API_KEY")
    GEMINI_MODEL = "gemini-1.5-flash"

    @staticmethod
    def _safety_settings():
        """Return default safety settings as google-genai SafetySetting objects."""
        from google.genai import types

        return [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]

    @staticmethod
    def configure():
        """Return the default safety settings for Google Gemini requests."""
        return AIConfig._safety_settings()


class LoginConfig:
    """Flask-Login configuration settings."""

    # Flask-Login Configuration
    LOGIN_VIEW = "login"
    LOGIN_MESSAGE = "You need to be logged in to access this page."
    LOGIN_MESSAGE_CATEGORY = "error"
    REFRESH_MESSAGE = "Please re-login to access this page."
    REFRESH_MESSAGE_CATEGORY = "info"


# Configuration dictionary for easy access
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(env=None):
    """
    Get configuration class based on environment.

    Args:
        env: Environment name (development, production, testing)
              If None, uses FLASK_ENV or defaults to development

    Returns:
        Configuration class for the specified environment
    """
    if env is None:
        env = os.getenv("FLASK_ENV", "development")

    return config.get(env, DevelopmentConfig)
