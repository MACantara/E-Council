"""Tests for the FastAPI auth endpoints."""

from __future__ import annotations

from models import EmailVerification, LoginAttempts, PasswordReset, Users


def _register(client, **overrides):
    """Register a user with default valid data."""
    payload = {
        "users_first_name": "Auth",
        "users_last_name": "User",
        "users_username": "authuser",
        "users_email": "auth@example.com",
        "users_password": "Password123!",
        "users_repeat_password": "Password123!",
        "users_role": "Faculty",
        "users_department_name": "Auth Test Department",
    }
    payload.update(overrides)
    return client.post("/api/v1/auth/register", json=payload)


def _verify(db, email):
    """Verify the email address for a registered user."""
    from api.emails import verify_email_token

    verification = db.query(EmailVerification).filter_by(email_verification_new_email=email).first()
    assert verification is not None
    verify_email_token(db, verification.email_verification_token)


class TestAuth:
    """Tests for the FastAPI auth endpoints."""

    def test_register(self, fastapi_client, email_backend):
        response = _register(fastapi_client)
        assert response.status_code == 201
        data = response.json()
        assert data["users_username"] == "authuser"
        assert data["users_email_verified"] == 0
        assert len(email_backend.messages) == 1
        assert email_backend.messages[0]["recipients"] == ["auth@example.com"]

    def test_register_requires_repeat_password(self, fastapi_client):
        response = _register(fastapi_client, users_repeat_password="Different123!")
        assert response.status_code == 422

    def test_register_requires_student_organization_for_officer(self, fastapi_client):
        response = _register(fastapi_client, users_role="Student Council Officer")
        assert response.status_code == 422

    def test_register_duplicate_username(self, fastapi_client):
        _register(fastapi_client, users_email="u1@example.com")
        response = _register(fastapi_client, users_email="u2@example.com")
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    def test_register_duplicate_email(self, fastapi_client):
        _register(fastapi_client, users_username="emailone")
        response = _register(fastapi_client, users_username="emailtwo")
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]

    def test_login_requires_verified_email(self, fastapi_client):
        _register(fastapi_client)
        response = fastapi_client.post(
            "/api/v1/auth/login",
            json={"users_username_or_email": "authuser", "users_password": "Password123!"},
        )
        assert response.status_code == 401
        assert "verify your email" in response.json()["detail"].lower()

    def test_login_and_access_me(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")

        login_response = fastapi_client.post(
            "/api/v1/auth/login",
            json={"users_username_or_email": "authuser", "users_password": "Password123!"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        me_response = fastapi_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["users_username"] == "authuser"

    def test_login_with_email(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")

        response = fastapi_client.post(
            "/api/v1/auth/login",
            json={"users_username_or_email": "auth@example.com", "users_password": "Password123!"},
        )
        assert response.status_code == 200

    def test_login_invalid_credentials(self, fastapi_client):
        response = fastapi_client.post(
            "/api/v1/auth/login",
            json={"users_username_or_email": "nouser", "users_password": "Password123!"},
        )
        assert response.status_code == 401

    def test_login_rate_limiting(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")

        for _ in range(6):
            response = fastapi_client.post(
                "/api/v1/auth/login",
                json={"users_username_or_email": "authuser", "users_password": "Wrong123!"},
            )
        assert response.status_code == 429

        attempt = fastapi_db.query(LoginAttempts).first()
        assert attempt is not None
        assert attempt.login_attempt_count >= 5

    def test_logout(self, fastapi_client):
        response = fastapi_client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"]

    def test_refresh_token(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")

        login_response = fastapi_client.post(
            "/api/v1/auth/login",
            json={"users_username_or_email": "authuser", "users_password": "Password123!"},
        )
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = fastapi_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

    def test_resend_verification(self, fastapi_client, fastapi_db, email_backend):
        _register(fastapi_client)
        email_backend.clear()

        response = fastapi_client.post(
            "/api/v1/auth/resend-verification",
            json={"users_email": "auth@example.com"},
        )
        assert response.status_code == 200
        assert len(email_backend.messages) == 1

    def test_resend_verification_already_verified(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")

        response = fastapi_client.post(
            "/api/v1/auth/resend-verification",
            json={"users_email": "auth@example.com"},
        )
        assert response.status_code == 400

    def test_verify_email(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        verification = (
            fastapi_db.query(EmailVerification).filter_by(email_verification_new_email="auth@example.com").first()
        )

        response = fastapi_client.get(f"/api/v1/auth/verify-email/{verification.email_verification_token}")
        assert response.status_code == 200
        user = fastapi_db.query(Users).filter_by(users_email="auth@example.com").first()
        assert user.users_email_verified == 1

    def test_forgot_password(self, fastapi_client, fastapi_db, email_backend):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")
        email_backend.clear()

        response = fastapi_client.post(
            "/api/v1/auth/forgot-password",
            json={"users_email": "auth@example.com"},
        )
        assert response.status_code == 200
        assert len(email_backend.messages) == 1

        reset = fastapi_db.query(PasswordReset).filter_by(password_reset_users_id=1).first()
        assert reset is not None

    def test_forgot_password_already_requested(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")
        fastapi_client.post(
            "/api/v1/auth/forgot-password",
            json={"users_email": "auth@example.com"},
        )

        response = fastapi_client.post(
            "/api/v1/auth/forgot-password",
            json={"users_email": "auth@example.com"},
        )
        assert response.status_code == 400

    def test_reset_password(self, fastapi_client, fastapi_db):
        _register(fastapi_client)
        _verify(fastapi_db, "auth@example.com")
        fastapi_client.post(
            "/api/v1/auth/forgot-password",
            json={"users_email": "auth@example.com"},
        )

        reset = fastapi_db.query(PasswordReset).first()
        response = fastapi_client.post(
            f"/api/v1/auth/reset-password/{reset.password_reset_selector}/{reset.password_reset_token}",
            json={"users_password": "NewPassword123!", "users_repeat_password": "NewPassword123!"},
        )
        assert response.status_code == 200

        login_response = fastapi_client.post(
            "/api/v1/auth/login",
            json={"users_username_or_email": "authuser", "users_password": "NewPassword123!"},
        )
        assert login_response.status_code == 200

    def test_reset_password_invalid_token(self, fastapi_client):
        response = fastapi_client.post(
            "/api/v1/auth/reset-password/invalid/invalid",
            json={"users_password": "NewPassword123!", "users_repeat_password": "NewPassword123!"},
        )
        assert response.status_code == 400
