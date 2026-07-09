"""
Rate limiting and login lockout tests for the E-Council system.
"""
import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from extensions import db, limiter


@pytest.fixture
def rate_limit_client(client):
    """Enable rate limiting for a single test and restore defaults afterward."""
    limiter.enabled = True
    limiter.reset()
    yield client
    limiter.enabled = False
    limiter.reset()


def test_login_rate_limit(rate_limit_client):
    """Login should be limited to 5 requests per minute per IP."""
    for _ in range(5):
        response = rate_limit_client.post('/auth/login', data={
            'users-username-email': 'nonexistent',
            'users-password': 'Password123!'
        })
        assert response.status_code in (200, 302)

    # The 6th request should be rate limited
    response = rate_limit_client.post('/auth/login', data={
        'users-username-email': 'nonexistent',
        'users-password': 'Password123!'
    })
    assert response.status_code == 429


def test_login_lockout_after_five_failed_attempts(rate_limit_client, sample_user):
    """Login should lock out after 5 failed attempts using LoginAttempts."""
    from models import LoginAttempts
    from datetime import datetime

    with rate_limit_client.application.app_context():
        # Create an existing record that indicates 5 failed attempts
        lockout = LoginAttempts(
            login_attempt_ip_address='127.0.0.1',
            login_attempt_count=5,
            login_attempt_last_attempt_time=datetime.utcnow()
        )
        db.session.add(lockout)
        db.session.commit()

    # One request should trigger the lockout before a 6th failed attempt
    response = rate_limit_client.post('/auth/login', data={
        'users-username-email': sample_user.users_username,
        'users-password': 'wrong-password'
    })
    # The application flashes and redirects when locked out
    assert response.status_code == 302
    assert response.location.endswith('/auth/login')


def test_signup_rate_limit(rate_limit_client):
    """Signup should be limited to 3 requests per hour per IP."""
    for _ in range(3):
        response = rate_limit_client.post('/auth/signup', data={})
        assert response.status_code == 200

    response = rate_limit_client.post('/auth/signup', data={})
    assert response.status_code == 429


def test_forgot_password_rate_limit(rate_limit_client):
    """Forgot password should be limited to 3 requests per hour per IP."""
    for _ in range(3):
        response = rate_limit_client.post('/auth/forgot-password', data={})
        assert response.status_code == 200

    response = rate_limit_client.post('/auth/forgot-password', data={})
    assert response.status_code == 429


def test_reset_password_rate_limit_per_token(rate_limit_client):
    """Reset password should be limited to 5 requests per minute per token."""
    token = 'test-token-123'
    for _ in range(5):
        response = rate_limit_client.post(f'/auth/reset-password/sel/{token}', data={})
        assert response.status_code == 302

    response = rate_limit_client.post(f'/auth/reset-password/sel/{token}', data={})
    assert response.status_code == 429

    # A different token should not be blocked
    response = rate_limit_client.post('/auth/reset-password/sel/other-token', data={})
    assert response.status_code == 302


def test_concept_paper_ai_rate_limit(rate_limit_client, sample_user):
    """Concept paper AI generation should be limited to 10 requests per minute per user."""
    rate_limit_client.post('/auth/login', data={
        'users-username-email': sample_user.users_username,
        'users-password': 'Password123!'
    }, follow_redirects=True)

    for _ in range(10):
        response = rate_limit_client.post('/concept-papers/generate-body', json={})
        assert response.status_code in (400, 200)

    response = rate_limit_client.post('/concept-papers/generate-body', json={})
    assert response.status_code == 429


def test_board_resolution_ai_rate_limit(rate_limit_client, sample_user):
    """Board resolution AI generation should be limited to 10 requests per minute per user."""
    rate_limit_client.post('/auth/login', data={
        'users-username-email': sample_user.users_username,
        'users-password': 'Password123!'
    }, follow_redirects=True)

    for _ in range(10):
        response = rate_limit_client.post('/board-resolutions/generate-description', json={})
        assert response.status_code in (400, 200)

    response = rate_limit_client.post('/board-resolutions/generate-description', json={})
    assert response.status_code == 429
