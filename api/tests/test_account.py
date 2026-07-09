"""Tests for the FastAPI account endpoints."""

from __future__ import annotations

import pytest
from models import Departments, EmailVerification, StudentOrganizations, Users


def _register_and_verify(client, db, **overrides):
    """Register a user, verify the email, and return the user."""
    from api.emails import verify_email_token

    payload = {
        "users_first_name": "Account",
        "users_last_name": "User",
        "users_username": "accountuser",
        "users_email": "account@example.com",
        "users_password": "Password123!",
        "users_repeat_password": "Password123!",
        "users_role": "Faculty",
        "users_department_name": "Account Test Department",
    }
    payload.update(overrides)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    verification = db.query(EmailVerification).filter_by(
        email_verification_new_email=payload["users_email"]
    ).first()
    assert verification is not None
    verify_email_token(db, verification.email_verification_token)

    return db.query(Users).filter_by(users_email=payload["users_email"]).first()


def _login(client, username_or_email, password="Password123!"):
    response = client.post(
        "/api/v1/auth/login",
        json={"users_username_or_email": username_or_email, "users_password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestAccount:
    """Tests for the FastAPI account endpoints."""

    def test_get_me(self, fastapi_client, fastapi_db, authenticated_client):
        response = authenticated_client.get("/api/v1/account/me")
        assert response.status_code == 200
        assert response.json()["users_username"] == "fastapiuser"

    def test_update_account(self, fastapi_client, fastapi_db, authenticated_client):
        department = fastapi_db.query(Departments).filter_by(
            departments_name="FastAPI Test Department"
        ).first()
        assert department is not None

        response = authenticated_client.put(
            "/api/v1/account/",
            json={
                "users_first_name": "Updated",
                "users_last_name": "User",
                "users_username": "fastapiuser",
                "users_departments_id": department.departments_id,
                "users_role": "Faculty",
                "users_home_address": "New Address",
                "users_contact_number": "1234567890",
                "users_current_password": "Password123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["users_first_name"] == "Updated"
        assert data["users_home_address"] == "New Address"

    def test_update_account_wrong_password(self, fastapi_client, fastapi_db, authenticated_client):
        department = fastapi_db.query(Departments).first()
        response = authenticated_client.put(
            "/api/v1/account/",
            json={
                "users_first_name": "Updated",
                "users_last_name": "User",
                "users_username": "fastapiuser",
                "users_departments_id": department.departments_id,
                "users_role": "Faculty",
                "users_current_password": "WrongPassword123!",
            },
        )
        assert response.status_code == 400

    def test_update_account_student_organization_required(self, fastapi_client, fastapi_db, authenticated_client):
        department = fastapi_db.query(Departments).first()
        org = StudentOrganizations(student_organizations_name="Test Org")
        fastapi_db.add(org)
        fastapi_db.commit()

        response = authenticated_client.put(
            "/api/v1/account/",
            json={
                "users_first_name": "Updated",
                "users_last_name": "User",
                "users_username": "fastapiuser",
                "users_departments_id": department.departments_id,
                "users_role": "Student Council Officer",
                "users_student_organization": org.student_organizations_id,
                "users_student_organization_position": "President",
                "users_current_password": "Password123!",
            },
        )
        assert response.status_code == 200

    def test_change_password(self, fastapi_client, fastapi_db, authenticated_client):
        response = authenticated_client.put(
            "/api/v1/account/password",
            json={
                "users_current_password": "Password123!",
                "users_new_password": "NewPassword123!",
                "users_repeat_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200

        user = fastapi_db.query(Users).filter_by(users_username="fastapiuser").first()
        assert user.check_password("NewPassword123!")

    def test_change_password_wrong_current(self, fastapi_client, fastapi_db, authenticated_client):
        response = authenticated_client.put(
            "/api/v1/account/password",
            json={
                "users_current_password": "WrongPassword123!",
                "users_new_password": "NewPassword123!",
                "users_repeat_password": "NewPassword123!",
            },
        )
        assert response.status_code == 400

    def test_change_email(self, fastapi_client, fastapi_db, authenticated_client, email_backend):
        email_backend.clear()
        response = authenticated_client.put(
            "/api/v1/account/email",
            json={
                "users_new_email": "newemail@example.com",
                "users_current_password": "Password123!",
            },
        )
        assert response.status_code == 200
        assert len(email_backend.messages) == 1

    def test_confirm_new_email(self, fastapi_client, fastapi_db, authenticated_client):
        authenticated_client.put(
            "/api/v1/account/email",
            json={
                "users_new_email": "newemail@example.com",
                "users_current_password": "Password123!",
            },
        )

        verification = fastapi_db.query(EmailVerification).filter_by(
            email_verification_new_email="newemail@example.com"
        ).first()
        assert verification is not None

        response = authenticated_client.get(
            f"/api/v1/account/confirm-new-email/{verification.email_verification_token}"
        )
        assert response.status_code == 200

        user = fastapi_db.query(Users).filter_by(users_email="newemail@example.com").first()
        assert user is not None

    def test_delete_account(self, fastapi_client, fastapi_db, authenticated_client):
        response = authenticated_client.request(
            "DELETE",
            "/api/v1/account/",
            json={"users_current_password": "Password123!"},
        )
        assert response.status_code == 200

        user = fastapi_db.query(Users).filter_by(users_username="fastapiuser").first()
        assert user is None
