"""
Application factory pattern for E-Council.
This module provides a create_app() function for Flask application creation.
"""

from flask import Flask
from config import get_config
from extensions import init_extensions
from utils import register_filters, register_error_handlers
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
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Override with specific configuration classes
    from config import DatabaseConfig, EmailConfig
    app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConfig.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ECHO'] = DatabaseConfig.SQLALCHEMY_ECHO
    
    app.config['MAIL_SERVER'] = EmailConfig.MAIL_SERVER
    app.config['MAIL_PORT'] = EmailConfig.MAIL_PORT
    app.config['MAIL_USE_TLS'] = EmailConfig.MAIL_USE_TLS
    app.config['MAIL_USE_SSL'] = EmailConfig.MAIL_USE_SSL
    app.config['MAIL_USERNAME'] = EmailConfig.MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = EmailConfig.MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = EmailConfig.MAIL_DEFAULT_SENDER
    
    # Initialize extensions
    init_extensions(app)
    
    # Register custom Jinja2 filters
    register_filters(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure Flask-Login user loader
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.user_loader(load_user)
    login_manager.unauthorized_handler(unauthorized)
    
    # Initialize upload folder
    config_class.init_app(app)
    
    # Note: Route registration would go here
    # For now, routes remain in app.py to maintain functionality
    # This is an intermediate step toward full application factory pattern
    
    return app


# For backward compatibility with current app.py structure
# This allows gradual migration to the factory pattern
def init_current_app(app):
    """
    Initialize current app.py structure with new configuration and extensions.
    This provides a bridge between current structure and factory pattern.
    
    Args:
        app: Existing Flask application instance from app.py
    """
    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Override with specific configuration classes
    from config import DatabaseConfig, EmailConfig
    app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConfig.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ECHO'] = DatabaseConfig.SQLALCHEMY_ECHO
    
    app.config['MAIL_SERVER'] = EmailConfig.MAIL_SERVER
    app.config['MAIL_PORT'] = EmailConfig.MAIL_PORT
    app.config['MAIL_USE_TLS'] = EmailConfig.MAIL_USE_TLS
    app.config['MAIL_USE_SSL'] = EmailConfig.MAIL_USE_SSL
    app.config['MAIL_USERNAME'] = EmailConfig.MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = EmailConfig.MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = EmailConfig.MAIL_DEFAULT_SENDER
    
    # Register custom filters
    register_filters(app)
    
    # Register error handlers
    register_error_handlers(app)