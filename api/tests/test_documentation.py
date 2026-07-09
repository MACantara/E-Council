"""Tests for the FastAPI documentation endpoints."""

from __future__ import annotations

import json
from io import BytesIO

import pytest

from api.dependencies import create_access_token
from models import Documentation


def _default_payload(**overrides):
    """Return a valid documentation creation payload."""
    payload = {
        "documentation_type": "Activity Report",
        "documentation_status": "Done",
        "documentation_academic_year": "2025-2026",
        "documentation_semester": "1st Semester",
        "documentation_date_of_submission": "2025-09-20T00:00:00",
        "documentation_rating": 4.5,
        "documentation_comments_suggestions": "Great event",
        "activity_report_items": [
            {"item_type": "strength", "item_text": "Good participation"},
            {"item_type": "weakness", "item_text": "Late start"},
        ],
        "tally_items": [
            {
                "name": "Satisfaction",
                "extremely_satisfied": 5,
                "satisfied": 4,
                "neutral": 1,
                "dissatisfied": 0,
                "extremely_dissatisfied": 0,
            }
        ],
        "evaluation_forms": [{"name": "Organization", "rating": "5"}],
        "evaluation_student_names": ["Alice Smith", "Bob Jones"],
    }
    payload.update(overrides)
    return payload


def _create_documentation(authenticated_client, **overrides):
    """Create a documentation record through the API and return the response data."""
    response = authenticated_client.post(
        "/api/v1/documentation",
        data={"data": json.dumps(_default_payload(**overrides))},
    )
    assert response.status_code == 201
    return response.json()["data"]


def _register_user(client, username, email, department_name):
    """Register a user via the API and return the created user payload."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "users_first_name": "FastAPI",
            "users_last_name": "User",
            "users_username": username,
            "users_email": email,
            "users_password": "Password123!",
            "users_repeat_password": "Password123!",
            "users_role": "Faculty",
            "users_department_name": department_name,
        },
    )
    assert response.status_code == 201
    return response.json()


def _headers_for_user(user):
    """Return an Authorization header for the given user."""
    return {"Authorization": f"Bearer {create_access_token(user['users_id'])}"}


class TestDocumentation:
    """FastAPI documentation endpoint tests."""

    def test_create_documentation(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/documentation",
            data={"data": json.dumps(_default_payload())},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["documentation_type"] == "Activity Report"
        assert data["documentation_status"] == "Done"
        assert len(data["activity_report_items"]) == 2
        assert len(data["tally_items"]) == 1

    def test_list_documentation(self, authenticated_client):
        _create_documentation(authenticated_client)
        response = authenticated_client.get("/api/v1/documentation")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1

    def test_list_documentation_filter_by_status(self, authenticated_client):
        _create_documentation(authenticated_client)
        response = authenticated_client.get("/api/v1/documentation?status=Upcoming")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_list_documentation_search(self, authenticated_client):
        _create_documentation(authenticated_client)
        response = authenticated_client.get("/api/v1/documentation?search=Activity")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1

    def test_get_documentation(self, authenticated_client):
        doc = _create_documentation(authenticated_client)
        response = authenticated_client.get(
            f"/api/v1/documentation/{doc['documentation_id']}"
        )
        assert response.status_code == 200
        assert response.json()["data"]["documentation_id"] == doc["documentation_id"]

    def test_update_documentation(self, authenticated_client):
        doc = _create_documentation(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/documentation/{doc['documentation_id']}",
            data={"data": json.dumps({"documentation_status": "Upcoming"})},
        )
        assert response.status_code == 200
        assert response.json()["data"]["documentation_status"] == "Upcoming"

    def test_update_status(self, authenticated_client):
        doc = _create_documentation(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/documentation/{doc['documentation_id']}/status",
            json={"status": "Cancelled"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["documentation_status"] == "Cancelled"

    def test_delete_documentation(self, authenticated_client, fastapi_db):
        doc = _create_documentation(authenticated_client)
        response = authenticated_client.delete(
            f"/api/v1/documentation/{doc['documentation_id']}"
        )
        assert response.status_code == 200
        assert fastapi_db.get(Documentation, doc["documentation_id"]) is None

    def test_upload_file(self, authenticated_client):
        doc = _create_documentation(authenticated_client)
        response = authenticated_client.post(
            f"/api/v1/documentation/{doc['documentation_id']}/files?file_type=evaluation_image",
            files={"file": ("test.png", b"fake-image-bytes", "image/png")},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["file"]["url"]
        assert data["file"]["public_id"]

    def test_download_file(self, authenticated_client):
        doc = _create_documentation(authenticated_client)
        upload_response = authenticated_client.post(
            f"/api/v1/documentation/{doc['documentation_id']}/files?file_type=attendance_image",
            files={"file": ("test.png", b"fake-image-bytes", "image/png")},
        )
        assert upload_response.status_code == 201
        public_id = upload_response.json()["data"]["file"]["public_id"]

        response = authenticated_client.get(
            f"/api/v1/documentation/{doc['documentation_id']}/files/{public_id}"
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["download_url"]

    def test_download_pdf(self, authenticated_client):
        doc = _create_documentation(authenticated_client)
        response = authenticated_client.get(
            f"/api/v1/documentation/{doc['documentation_id']}/pdf"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_department_scoping(self, authenticated_client, fastapi_client):
        """Users can only see documentation from their own department or prepared by them."""
        _create_documentation(authenticated_client)
        other_user = _register_user(
            fastapi_client, "scopedoc", "scopedoc@example.com", "Scoped Doc Department"
        )

        response = fastapi_client.get(
            "/api/v1/documentation", headers=_headers_for_user(other_user)
        )
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_unauthorized_access(self, authenticated_client, fastapi_client):
        """A user cannot access documentation from another department."""
        doc = _create_documentation(authenticated_client)
        other_user = _register_user(
            fastapi_client, "unauthorized", "unauthorized@example.com", "Unauthorized Department"
        )

        response = fastapi_client.get(
            f"/api/v1/documentation/{doc['documentation_id']}",
            headers=_headers_for_user(other_user),
        )
        assert response.status_code == 403
