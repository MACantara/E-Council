"""Shared FastAPI test fixtures and configuration."""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Set environment variables before the FastAPI app or its dependencies are imported.
# Use an in-memory SQLite database with StaticPool so tests run quickly.
os.environ["FASTAPI_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["STORAGE_PROVIDER"] = "memory"
os.environ["EMAIL_PROVIDER"] = "memory"
os.environ["AI_PROVIDER"] = "mock"

import api.database
from api.dependencies import reset_email_backend
from api.main import app
from models import Departments, Users, db

_MEMORY_DATABASE_URI = "sqlite:///:memory:"


def _rebind_engine():
    """Rebind the global API database engine to the in-memory test database."""
    os.environ["FASTAPI_DATABASE_URI"] = _MEMORY_DATABASE_URI
    api.database.set_engine(_MEMORY_DATABASE_URI)


@pytest.fixture
def email_backend():
    """Reset and expose the cached email backend for assertions."""
    reset_email_backend()
    from api.dependencies import get_email

    backend = get_email()
    backend.clear()
    return backend


@pytest.fixture
def fastapi_client():
    """FastAPI TestClient with a fresh in-memory database for each test."""
    _rebind_engine()
    api.database.create_tables()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def fastapi_db():
    """A SQLAlchemy session that is rolled back after the test."""
    _rebind_engine()
    api.database.create_tables()
    session = api.database.SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        db.metadata.drop_all(bind=api.database.get_engine())


@pytest.fixture
def fastapi_user(fastapi_client, fastapi_db):
    """A registered and verified user created through the FastAPI auth API."""
    from api.emails import verify_email_token
    from models import EmailVerification

    response = fastapi_client.post(
        "/api/v1/auth/register",
        json={
            "users_first_name": "FastAPI",
            "users_last_name": "User",
            "users_username": "fastapiuser",
            "users_email": "fastapi@example.com",
            "users_password": "Password123!",
            "users_repeat_password": "Password123!",
            "users_role": "Faculty",
            "users_department_name": "FastAPI Test Department",
        },
    )
    assert response.status_code == 201

    verification = (
        fastapi_db.query(EmailVerification).filter_by(email_verification_new_email="fastapi@example.com").first()
    )
    assert verification is not None
    verify_email_token(fastapi_db, verification.email_verification_token)

    return response.json()


@pytest.fixture
def authenticated_client(fastapi_client, fastapi_user):
    """A TestClient wrapper authenticated as ``fastapi_user``."""
    login_response = fastapi_client.post(
        "/api/v1/auth/login",
        json={
            "users_username_or_email": fastapi_user["users_username"],
            "users_password": "Password123!",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    class _AuthenticatedClient:
        def __init__(self, client: TestClient, token: str) -> None:
            self.client = client
            self.token = token

        def _headers(self, kwargs: dict[str, Any]) -> dict[str, Any]:
            headers = kwargs.pop("headers", {}) or {}
            headers["Authorization"] = f"Bearer {self.token}"
            return {"headers": headers, **kwargs}

        def get(self, *args, **kwargs):
            return self.client.get(*args, **self._headers(kwargs))

        def post(self, *args, **kwargs):
            return self.client.post(*args, **self._headers(kwargs))

        def put(self, *args, **kwargs):
            return self.client.put(*args, **self._headers(kwargs))

        def patch(self, *args, **kwargs):
            return self.client.patch(*args, **self._headers(kwargs))

        def delete(self, *args, **kwargs):
            return self.client.delete(*args, **self._headers(kwargs))

        def request(self, method, *args, **kwargs):
            return self.client.request(method, *args, **self._headers(kwargs))

    return _AuthenticatedClient(fastapi_client, token)


@pytest.fixture
def admin_user(fastapi_db):
    """Create an admin user directly in the database."""
    department = Departments(departments_name="Admin Department")
    fastapi_db.add(department)
    fastapi_db.commit()

    user = Users(
        users_first_name="Admin",
        users_last_name="User",
        users_username="adminuser",
        users_email="admin@example.com",
        users_departments_id=department.departments_id,
        users_role="Admin",
        users_email_verified=1,
    )
    user.set_password("Password123!")
    fastapi_db.add(user)
    fastapi_db.commit()
    fastapi_db.refresh(user)
    return user
