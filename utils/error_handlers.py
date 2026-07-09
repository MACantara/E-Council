"""
Error handlers for E-Council.
"""

import traceback
from typing import Any

from cloudinary.exceptions import Error
from flask import flash, redirect, render_template, url_for
from werkzeug.exceptions import HTTPException


def handle_cloudinary_error(error: Exception) -> Any:
    """
    Handle Cloudinary errors.

    Args:
        error: Cloudinary error exception

    Returns:
        Redirect with flash message
    """
    from flask import current_app

    current_app.logger.error("Cloudinary error: %s\n%s", error, traceback.format_exc())
    flash("An error occurred while processing images.", "error")
    return redirect(url_for("documentation.documentation_overview"))


def handle_internal_error(error: Exception) -> Any:
    """
    Handle unhandled/internal errors by logging the exception and showing a
    user-friendly 500 page without exposing tracebacks.

    Args:
        error: Exception that was raised

    Returns:
        Response or tuple of rendered template and 500 status code
    """
    from flask import current_app

    # Let non-500 HTTP exceptions (e.g. 403, 404, 429) use their normal
    # responses instead of being rendered as a 500 page.
    if isinstance(error, HTTPException) and error.code != 500:
        return error.get_response()

    current_app.logger.error("Unhandled internal error: %s\n%s", error, traceback.format_exc())
    return render_template("500.html"), 500


def register_error_handlers(app: Any) -> None:
    """
    Register all error handlers with the Flask app.

    Args:
        app: Flask application instance
    """
    app.errorhandler(Error)(handle_cloudinary_error)
    app.errorhandler(500)(handle_internal_error)
    app.errorhandler(Exception)(handle_internal_error)
