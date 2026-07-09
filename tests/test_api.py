"""Tests for the FastAPI auth prototype."""

import os

import pytest
from fastapi.testclient import TestClient

# Set environment variables before importing FastAPI modules and restore them
# afterwards so the global environment is not affected for other tests.
_original_flask_env = os.environ.get("FLASK_ENV")
os.environ["FASTAPI_DATABASE_URI"] = "sqlite:///./fastapi_test.db"
os.environ["FLASK_ENV"] = "testing"

from api.database import create_tables, engine
from api.main import app
from models import db

if _original_flask_env is None:
    os.environ.pop("FLASK_ENV", None)
else:
    os.environ["FLASK_ENV"] = _original_flask_env


def _create_client():
    """Create a test client with fresh tables."""
    create_tables()
    with TestClient(app) as client:
        yield client
    db.metadata.drop_all(bind=engine)


class TestFastAPIAuth:
    """FastAPI auth prototype tests."""

    @pytest.fixture(autouse=True, scope="class")
    def client(self):
        """Provide a FastAPI test client."""
        yield from _create_client()

    def _register_user(self, client, username, email):
        """Helper to register a new user."""
        return client.post(
            "/api/v1/auth/register",
            json={
                "users_first_name": "Test",
                "users_last_name": "User",
                "users_username": username,
                "users_email": email,
                "users_password": "Password123!",
                "users_role": "Student Council Officer",
                "users_department_name": "FastAPI Test Department",
            },
        )

    def test_register(self, client):
        """A user can register through the FastAPI auth endpoint."""
        response = self._register_user(client, "fastapiuser", "fastapi@example.com")
        assert response.status_code == 201
        data = response.json()
        assert data["users_username"] == "fastapiuser"
        assert data["users_email"] == "fastapi@example.com"
        assert data["users_department_name"] == "FastAPI Test Department"
        assert "users_id" in data

    def test_register_duplicate_username(self, client):
        """Duplicate usernames are rejected during registration."""
        self._register_user(client, "dupuser", "dup1@example.com")
        response = self._register_user(client, "dupuser", "dup2@example.com")
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    def test_login_and_access_me(self, client):
        """A registered user can log in and access the protected /me endpoint."""
        self._register_user(client, "loginuser", "login@example.com")
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "users_username_or_email": "loginuser",
                "users_password": "Password123!",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["users_username"] == "loginuser"

    def test_login_with_email(self, client):
        """A user can log in using their email address."""
        self._register_user(client, "emailuser", "email@example.com")
        response = client.post(
            "/api/v1/auth/login",
            json={
                "users_username_or_email": "email@example.com",
                "users_password": "Password123!",
            },
        )
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Invalid credentials are rejected."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "users_username_or_email": "nouser",
                "users_password": "Password123!",
            },
        )
        assert response.status_code == 401

    def test_refresh_token(self, client):
        """A refresh token can be used to obtain a new access token."""
        self._register_user(client, "refreshuser", "refresh@example.com")
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "users_username_or_email": "refreshuser",
                "users_password": "Password123!",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

    def test_me_without_token(self, client):
        """The /me endpoint requires a valid token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
