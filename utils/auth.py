"""
Authentication helper functions for E-Council.
"""

from flask import flash, redirect, url_for
from flask_login import LoginManager, login_required, current_user

# Note: These imports will need to be adjusted based on final model structure
# For now, importing from app.py (will be refactored later)
# from models.user import Users

# Temporary imports from app.py (will be refactored later)
from app import db, Users


def load_user(user_id):
    """
    Load a user by ID for Flask-Login.
    
    Args:
        user_id: ID of the user to load
        
    Returns:
        User object or None if not found
    """
    return db.session.get(Users, int(user_id))


def unauthorized():
    """
    Handle unauthorized access attempts.
    
    Returns:
        Redirect to login page with flash message
    """
    flash("You need to be logged in to access this page.", "error")
    return redirect(url_for("login"))


def setup_login_manager(login_manager, app):
    """
    Configure Flask-Login for the application.
    
    Args:
        login_manager: Flask-Login LoginManager instance
        app: Flask application instance
    """
    login_manager.init_app(app)
    login_manager.user_loader(load_user)
    login_manager.unauthorized_handler(unauthorized)