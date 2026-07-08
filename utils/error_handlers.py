"""
Error handlers for E-Council.
"""

from flask import flash, redirect, url_for
from cloudinary.exceptions import CloudinaryError


def handle_cloudinary_error(error):
    """
    Handle Cloudinary errors.
    
    Args:
        error: Cloudinary error exception
        
    Returns:
        Redirect with flash message
    """
    app.logger.error(f"Cloudinary error: {str(error)}")
    flash("An error occurred while processing images.", "error")
    return redirect(url_for('documentation_overview'))


def register_error_handlers(app):
    """
    Register all error handlers with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.errorhandler(CloudinaryError)(handle_cloudinary_error)