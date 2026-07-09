"""Tests for the FastAPI admin endpoints."""

from __future__ import annotations

import pytest
from models import Departments, Users


def _admin_headers(admin_user):
    from api.dependencies import create_access_token

    token = create_access_token(admin_user.users_id)
    return {"Authorization": f"Bearer {token}"}


class TestAdmin:
    """Tests for the FastAPI admin endpoints."""

    def test_list_users_requires_admin(self, fastapi_client, authenticated_client):
        response = authenticated_client.get("/api/v1/admin/users")
        assert response.status_code == 403

    def test_list_users(self, fastapi_client, admin_user, fastapi_user):
        response = fastapi_client.get("/api/v1/admin/users", headers=_admin_headers(admin_user))
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 2

    def test_list_users_search(self, fastapi_client, admin_user, fastapi_user):
        response = fastapi_client.get(
            "/api/v1/admin/users",
            params={"search": "admin"},
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert all("admin" in (u["users_username"].lower() or u["users_email"].lower()) for u in data["items"])

    def test_update_user_role(self, fastapi_client, admin_user, fastapi_user, fastapi_db):
        user = fastapi_db.query(Users).filter_by(users_username="fastapiuser").first()
        assert user is not None

        response = fastapi_client.put(
            f"/api/v1/admin/users/{user.users_id}/role",
            json={"users_role": "Admin"},
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        assert response.json()["users_role"] == "Admin"

    def test_update_user_role_invalid(self, fastapi_client, admin_user, fastapi_user):
        user_id = fastapi_user["users_id"]
        response = fastapi_client.put(
            f"/api/v1/admin/users/{user_id}/role",
            json={"users_role": "InvalidRole"},
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 422

    def test_deactivate_user(self, fastapi_client, admin_user, fastapi_user, fastapi_db):
        user_id = fastapi_user["users_id"]
        response = fastapi_client.put(
            f"/api/v1/admin/users/{user_id}/deactivate",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200

        user = fastapi_db.query(Users).filter_by(users_id=user_id).first()
        assert user.users_email_verified == 0

    def test_delete_user(self, fastapi_client, admin_user, fastapi_db):
        department = Departments(departments_name="Delete User Department")
        fastapi_db.add(department)
        fastapi_db.commit()

        user = Users(
            users_first_name="Delete",
            users_last_name="User",
            users_username="deleteuser",
            users_email="delete@example.com",
            users_departments_id=department.departments_id,
            users_role="Faculty",
            users_email_verified=1,
        )
        user.set_password("Password123!")
        fastapi_db.add(user)
        fastapi_db.commit()

        response = fastapi_client.delete(
            f"/api/v1/admin/users/{user.users_id}",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        assert fastapi_db.query(Users).filter_by(users_id=user.users_id).first() is None

    def test_delete_user_not_found(self, fastapi_client, admin_user):
        response = fastapi_client.delete(
            "/api/v1/admin/users/99999",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 404
