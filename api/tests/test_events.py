"""Tests for the FastAPI event endpoints."""

from __future__ import annotations

import json

import pytest

from api.dependencies import create_access_token
from models import Events


def _default_event_payload(**overrides):
    """Return a valid event creation payload."""
    payload = {
        "events_name": "FastAPI Test Event",
        "events_semester": "1st Semester",
        "events_academic_year": "2025-2026",
        "events_start_date_and_time": "2025-09-20T08:00",
        "events_end_date_and_time": "2025-09-20T17:00",
        "events_venue": "Online",
        "events_budget": "1000",
        "events_status": "Upcoming",
        "events_description": "A test event.",
        "events_remarks": "",
    }
    payload.update(overrides)
    return payload


def _create_event(authenticated_client, **overrides):
    """Create an event through the API and return the response data."""
    response = authenticated_client.post("/api/v1/events", json=_default_event_payload(**overrides))
    assert response.status_code == 201
    return response.json()["data"]


def _transaction_payload(**overrides):
    """Return a valid transaction payload."""
    payload = {
        "transaction_name": "Catering",
        "transaction_date": "2025-09-20T10:00",
        "unit_amount": 5,
        "unit_price": "100.00",
        "category": "Food",
        "type": "Expense",
    }
    payload.update(overrides)
    return payload


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


class TestEvents:
    """FastAPI event endpoint tests."""

    def test_create_event(self, authenticated_client):
        response = authenticated_client.post("/api/v1/events", json=_default_event_payload())
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["events_name"] == "FastAPI Test Event"
        assert data["events_status"] == "Upcoming"
        assert data["events_venue"] == "Online"

    def test_create_event_from_concept_paper(self, authenticated_client):
        concept_paper = authenticated_client.post(
            "/api/v1/concept-papers",
            json={
                "concept_paper_forms_subject": "Concept for Event",
                "concept_paper_forms_semester": "1st Semester",
                "concept_paper_forms_academic_year": "2025-2026",
                "concept_paper_forms_event_start_date_and_time": "2025-09-20T08:00",
                "concept_paper_forms_event_end_date_and_time": "2025-09-20T17:00",
                "concept_paper_forms_location": "Auditorium",
            },
        )
        assert concept_paper.status_code == 201
        concept_paper_id = concept_paper.json()["data"]["concept_paper_forms_id"]

        response = authenticated_client.post(
            "/api/v1/events",
            json={
                "creation_method": "existing",
                "concept_paper_forms_id": concept_paper_id,
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["events_name"] == "Concept for Event"
        assert data["events_venue"] == "Auditorium"

    def test_list_events(self, authenticated_client):
        _create_event(authenticated_client)
        response = authenticated_client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1

    def test_list_events_filter_by_status(self, authenticated_client):
        _create_event(authenticated_client)
        response = authenticated_client.get("/api/v1/events?status=Done")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_list_events_search(self, authenticated_client):
        _create_event(authenticated_client)
        response = authenticated_client.get("/api/v1/events?search=FastAPI")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1

    def test_get_event(self, authenticated_client):
        event = _create_event(authenticated_client)
        response = authenticated_client.get(f"/api/v1/events/{event['events_id']}")
        assert response.status_code == 200
        assert response.json()["data"]["events_id"] == event["events_id"]

    def test_update_event(self, authenticated_client):
        event = _create_event(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/events/{event['events_id']}",
            json={"events_name": "Updated Event"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["events_name"] == "Updated Event"

    def test_update_status(self, authenticated_client):
        event = _create_event(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/events/{event['events_id']}/status",
            json={"status": "Done"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["events_status"] == "Done"

    def test_delete_event(self, authenticated_client, fastapi_db):
        event = _create_event(authenticated_client)
        response = authenticated_client.delete(f"/api/v1/events/{event['events_id']}")
        assert response.status_code == 200
        assert fastapi_db.get(Events, event["events_id"]) is None

    def test_add_transaction(self, authenticated_client):
        event = _create_event(authenticated_client)
        response = authenticated_client.post(
            f"/api/v1/events/{event['events_id']}/transactions",
            data={"data": json.dumps(_transaction_payload())},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["transaction_name"] == "Catering"
        assert float(data["total"]) == 500.0

    def test_update_transaction(self, authenticated_client):
        event = _create_event(authenticated_client)
        tx = authenticated_client.post(
            f"/api/v1/events/{event['events_id']}/transactions",
            data={"data": json.dumps(_transaction_payload())},
        )
        assert tx.status_code == 201
        tx_id = tx.json()["data"]["transaction_id"]

        response = authenticated_client.put(
            f"/api/v1/events/{event['events_id']}/transactions/{tx_id}",
            data={"data": json.dumps({"transaction_name": "Updated Catering"})},
        )
        assert response.status_code == 200
        assert response.json()["data"]["transaction_name"] == "Updated Catering"

    def test_invite_and_accept(self, authenticated_client, fastapi_client, fastapi_db):
        """Invite a user from another department and accept the invitation."""
        from models import EventInvitations

        event = _create_event(authenticated_client)
        other_user = _register_user(fastapi_client, "otheruser", "other@example.com", "Other Department")

        response = authenticated_client.post(
            f"/api/v1/events/{event['events_id']}/invitations",
            json={"email": other_user["users_email"]},
        )
        assert response.status_code == 201

        invitation = fastapi_db.query(EventInvitations).filter_by(
            event_invitations_events_id=event["events_id"]
        ).first()
        assert invitation is not None

        headers = _headers_for_user(other_user)

        response = fastapi_client.post(
            "/api/v1/events/invitations/accept",
            json={"token": invitation.event_invitations_token},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["event_id"] == event["events_id"]

        response = fastapi_client.get("/api/v1/events", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1

    def test_reject_invite(self, authenticated_client, fastapi_client, fastapi_db):
        """Invite a user and reject the invitation."""
        from models import EventInvitations

        event = _create_event(authenticated_client)
        other_user = _register_user(fastapi_client, "rejectuser", "reject@example.com", "Reject Department")

        response = authenticated_client.post(
            f"/api/v1/events/{event['events_id']}/invitations",
            json={"email": other_user["users_email"]},
        )
        assert response.status_code == 201

        invitation = fastapi_db.query(EventInvitations).filter_by(
            event_invitations_events_id=event["events_id"]
        ).first()

        headers = _headers_for_user(other_user)

        response = fastapi_client.post(
            "/api/v1/events/invitations/reject",
            json={"token": invitation.event_invitations_token},
            headers=headers,
        )
        assert response.status_code == 200

        assert fastapi_db.query(EventInvitations).filter_by(
            event_invitations_token=invitation.event_invitations_token
        ).first() is None

    def test_department_scoping(self, authenticated_client, fastapi_client):
        """Users can only see events linked to their department."""
        _create_event(authenticated_client)
        other_user = _register_user(fastapi_client, "scopeuser", "scope@example.com", "Scoped Department")

        response = fastapi_client.get("/api/v1/events", headers=_headers_for_user(other_user))
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0
