"""
Email sending tests for the E-Council application.

These tests verify that the password reset and verification email routes
queue messages by capturing them in the in-memory email backend.
"""

import os
import sys

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from services.email import EmailError, InMemoryEmailBackend, get_email


@pytest.fixture
def email_backend(app):
    """Provide an in-memory email backend and install it on the app."""
    backend = InMemoryEmailBackend()
    app.config["EMAIL_BACKEND"] = backend
    yield backend
    backend.clear()


def test_forgot_password_sends_email(client, sample_user, email_backend):
    """The forgot-password route should trigger a password reset email."""
    response = client.post(
        "/auth/forgot-password",
        data={"users-email": sample_user.users_email},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert len(email_backend.messages) == 1
    assert email_backend.messages[0]["subject"] == "Password Reset Request"
    assert sample_user.users_email in email_backend.messages[0]["recipients"]


def test_send_verification_email_route(client, sample_user, email_backend):
    """The resend verification route should trigger a verification email."""
    from extensions import db

    sample_user.users_email_verified = 0
    db.session.commit()

    response = client.get(f"/auth/send_verification_email/{sample_user.users_email}", follow_redirects=True)

    assert response.status_code == 200
    assert len(email_backend.messages) == 1
    assert email_backend.messages[0]["subject"] == "New Account Email Verification"


def test_get_email_respects_app_config(app):
    """get_email should return the backend configured by EMAIL_PROVIDER."""
    app.config["EMAIL_PROVIDER"] = "memory"
    backend = get_email(app)
    assert isinstance(backend, InMemoryEmailBackend)


def test_get_email_unknown_provider_raises(app):
    """get_email should raise EmailError for an unknown provider."""
    app.config["EMAIL_PROVIDER"] = "unknown"
    with pytest.raises(EmailError):
        get_email(app)
