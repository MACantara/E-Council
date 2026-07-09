"""
Email sending tests for the E-Council application.

These tests verify that the password reset and verification email routes
queue messages by mocking the Flask-Mail ``send`` method.
"""

import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock



def test_forgot_password_sends_email(client, sample_user, monkeypatch):
    """The forgot-password route should trigger a password reset email."""
    mock_send = MagicMock()
    from extensions import mail
    monkeypatch.setattr(mail, 'send', mock_send)

    response = client.post('/auth/forgot-password', data={
        'users-email': sample_user.users_email,
    }, follow_redirects=True)

    assert response.status_code == 200
    mock_send.assert_called_once()


def test_send_verification_email_route(client, sample_user, monkeypatch):
    """The resend verification route should trigger a verification email."""
    from extensions import db
    sample_user.users_email_verified = 0
    db.session.commit()

    mock_send = MagicMock()
    from extensions import mail
    monkeypatch.setattr(mail, 'send', mock_send)

    response = client.get(
        f'/auth/send_verification_email/{sample_user.users_email}',
        follow_redirects=True
    )

    assert response.status_code == 200
    mock_send.assert_called_once()
