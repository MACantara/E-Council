"""Tests for the FastAPI meeting endpoints."""

from __future__ import annotations

import json

import pytest

from api.dependencies import create_access_token
from models import MeetingAttendee, MinutesOfTheMeeting


def _default_meeting_payload(user_id, **overrides):
    """Return a valid meeting creation payload."""
    payload = {
        "minutes_of_the_meeting_date": "2025-09-20T10:00",
        "minutes_of_the_meeting_semester": "1st Semester",
        "minutes_of_the_meeting_academic_year": "2025-2026",
        "minutes_of_the_meeting_status": "Upcoming",
        "minutes_of_the_meeting_presiding_officer": str(user_id),
        "minutes_of_the_meeting_agenda": "Discuss budget and upcoming events",
        "minutes_of_the_meeting_notes": "Initial notes",
        "attendees": [user_id],
    }
    payload.update(overrides)
    return payload


def _create_meeting(authenticated_client, user, **overrides):
    """Create a meeting through the API and return the response data."""
    response = authenticated_client.post(
        "/api/v1/meetings",
        data={"data": json.dumps(_default_meeting_payload(user["users_id"], **overrides))},
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


class TestMeetings:
    """FastAPI meeting endpoint tests."""

    def test_create_meeting(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        assert meeting["minutes_of_the_meeting_agenda"] == "Discuss budget and upcoming events"
        assert meeting["minutes_of_the_meeting_status"] == "Upcoming"
        assert len(meeting["attendees"]) == 1

    def test_list_meetings(self, authenticated_client, fastapi_user):
        _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.get("/api/v1/meetings")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1

    def test_list_meetings_filter_by_status(self, authenticated_client, fastapi_user):
        _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.get("/api/v1/meetings?status=Done")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_list_meetings_search(self, authenticated_client, fastapi_user):
        _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.get("/api/v1/meetings?search=budget")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1

    def test_get_meeting(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.get(f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}")
        assert response.status_code == 200
        assert response.json()["data"]["minutes_of_the_meeting_id"] == meeting["minutes_of_the_meeting_id"]

    def test_update_meeting(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.put(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}",
            data={"data": json.dumps({"minutes_of_the_meeting_agenda": "Updated agenda"})},
        )
        assert response.status_code == 200
        assert response.json()["data"]["minutes_of_the_meeting_agenda"] == "Updated agenda"

    def test_update_status(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.put(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/status",
            json={"status": "Done"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["minutes_of_the_meeting_status"] == "Done"

    def test_update_agenda(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.put(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/agenda",
            json={"agenda": "New agenda items"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["minutes_of_the_meeting_agenda"] == "New agenda items"

    def test_update_minutes(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.put(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/minutes",
            json={"minutes": "Detailed minutes"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["minutes_of_the_meeting_notes"] == "Detailed minutes"

    def test_delete_meeting(self, authenticated_client, fastapi_user, fastapi_db):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.delete(f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}")
        assert response.status_code == 200
        assert fastapi_db.get(MinutesOfTheMeeting, meeting["minutes_of_the_meeting_id"]) is None

    def test_add_attendee(self, authenticated_client, fastapi_user, fastapi_client):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        other_user = _register_user(fastapi_client, "meetinguser", "meeting@example.com", "Meeting Department")

        response = authenticated_client.post(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/attendees",
            json={"users_id": other_user["users_id"]},
        )
        assert response.status_code == 201
        assert response.json()["data"]["users_id"] == other_user["users_id"]

    def test_mark_attendance(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        attendee_id = meeting["attendees"][0]["meeting_attendee_id"]

        response = authenticated_client.put(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/attendees/{attendee_id}/attendance",
            json={"attended": False},
        )
        assert response.status_code == 200
        assert response.json()["data"]["attended"] is False

    def test_remove_attendee(self, authenticated_client, fastapi_user, fastapi_client, fastapi_db):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        other_user = _register_user(fastapi_client, "removeuser", "remove@example.com", "Remove Department")

        added = authenticated_client.post(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/attendees",
            json={"users_id": other_user["users_id"]},
        )
        assert added.status_code == 201
        attendee_id = added.json()["data"]["meeting_attendee_id"]

        response = authenticated_client.delete(
            f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/attendees/{attendee_id}"
        )
        assert response.status_code == 200
        assert fastapi_db.get(MeetingAttendee, attendee_id) is None

    def test_download_pdf(self, authenticated_client, fastapi_user):
        meeting = _create_meeting(authenticated_client, fastapi_user)
        response = authenticated_client.get(f"/api/v1/meetings/{meeting['minutes_of_the_meeting_id']}/pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_department_scoping(self, authenticated_client, fastapi_user, fastapi_client):
        """Users can only see meetings linked to their department or prepared by them."""
        _create_meeting(authenticated_client, fastapi_user)
        other_user = _register_user(fastapi_client, "scopuser", "scop@example.com", "Scop Department")

        response = fastapi_client.get("/api/v1/meetings", headers=_headers_for_user(other_user))
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0
