"""
Logging and error handling tests for the E-Council system.
"""

import os
import sys

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloudinary.exceptions import Error as CloudinaryError

from app import init_database
from extensions import db
from utils.error_handlers import handle_cloudinary_error, handle_internal_error


def test_init_database_logs_connection_error(app, monkeypatch, caplog):
    """init_database should log an error when the database connection fails."""
    import sqlalchemy

    def _broken_connect(*args, **kwargs):
        raise sqlalchemy.exc.OperationalError("db down", None, None)

    monkeypatch.setattr(db.engine, "connect", _broken_connect)

    try:
        with caplog.at_level("ERROR", logger="app"):
            result = init_database(app)
    finally:
        monkeypatch.undo()

    assert result is False
    assert "Database connection failed" in caplog.text


def test_handle_cloudinary_error_logs_and_redirects(app, caplog):
    """Cloudinary errors should be logged and the user redirected."""
    with app.test_request_context("/"), caplog.at_level("ERROR", logger="app"):
        response = handle_cloudinary_error(CloudinaryError("cloud failure"))

    assert response.status_code == 302
    assert "Cloudinary error" in caplog.text


def test_handle_internal_error_logs_and_returns_500(app, caplog):
    """Internal errors should be logged and a user-friendly 500 page returned."""
    with app.test_request_context("/"), caplog.at_level("ERROR", logger="app"):
        response, status_code = handle_internal_error(RuntimeError("boom"))

    assert status_code == 500
    assert "Internal Server Error" in response
    assert "Unhandled internal error" in caplog.text
