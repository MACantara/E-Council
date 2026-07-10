"""End-to-end integration tests for the FastAPI backend."""

from __future__ import annotations

import json

from api.dependencies import create_access_token


def _admin_headers(admin_user):
    """Return an Authorization header for the given admin user."""
    return {"Authorization": f"Bearer {create_access_token(admin_user.users_id)}"}


class TestPublicEndpoints:
    """Smoke tests for the public root, health, and API discovery endpoints."""

    def test_root(self, fastapi_client):
        response = fastapi_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "E-Council API"
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"

    def test_health(self, fastapi_client):
        response = fastapi_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_v1_root(self, fastapi_client):
        response = fastapi_client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v1"
        assert "features" in data
        assert "auth" in data["features"]
        assert "concept-papers" in data["features"]

    def test_openapi_docs(self, fastapi_client):
        assert fastapi_client.get("/docs").status_code == 200
        assert fastapi_client.get("/redoc").status_code == 200


class TestEndToEndFeatureFlow:
    """A single authenticated flow that touches every feature router."""

    def test_full_feature_flow(self, authenticated_client, fastapi_user):
        user_id = fastapi_user["users_id"]

        # Concept paper
        paper_response = authenticated_client.post(
            "/api/v1/concept-papers",
            json={
                "concept_paper_forms_subject": "Integration Test Concept",
                "concept_paper_forms_semester": "1st Semester",
                "concept_paper_forms_academic_year": "2025-2026",
                "concept_paper_forms_event_start_date_and_time": "2025-09-20T08:00",
                "concept_paper_forms_event_end_date_and_time": "2025-09-21T17:00",
                "concept_paper_forms_location": "Auditorium",
            },
        )
        assert paper_response.status_code == 201
        paper_id = paper_response.json()["data"]["concept_paper_forms_id"]

        # Event created from the concept paper
        event_response = authenticated_client.post(
            "/api/v1/events",
            json={
                "creation_method": "existing",
                "concept_paper_forms_id": paper_id,
            },
        )
        assert event_response.status_code == 201
        event_id = event_response.json()["data"]["events_id"]

        # Meeting
        meeting_response = authenticated_client.post(
            "/api/v1/meetings",
            data={
                "data": json.dumps(
                    {
                        "minutes_of_the_meeting_date": "2025-09-20T10:00",
                        "minutes_of_the_meeting_semester": "1st Semester",
                        "minutes_of_the_meeting_academic_year": "2025-2026",
                        "minutes_of_the_meeting_status": "Upcoming",
                        "minutes_of_the_meeting_presiding_officer": str(user_id),
                        "minutes_of_the_meeting_agenda": "Discuss integration flow",
                        "minutes_of_the_meeting_notes": "Initial notes",
                        "attendees": [user_id],
                    }
                )
            },
        )
        assert meeting_response.status_code == 201
        meeting_id = meeting_response.json()["data"]["minutes_of_the_meeting_id"]

        # Board resolution
        resolution_response = authenticated_client.post(
            "/api/v1/board-resolutions",
            json={
                "board_resolutions_date": "2025-09-20T10:00",
                "board_resolutions_title": "Integration Resolution",
                "board_resolutions_description": "A test resolution.",
                "board_resolutions_total_amount": "15000",
                "board_resolutions_academic_year": "2025-2026",
                "board_resolutions_semester": "1st Semester",
                "board_resolutions_status": "Upcoming",
                "board_resolutions_prepared_by": user_id,
                "board_resolutions_approved_by": user_id,
                "student_signatory_ids": [],
            },
        )
        assert resolution_response.status_code == 201
        resolution_id = resolution_response.json()["data"]["board_resolutions_id"]

        # Financial report
        financial_response = authenticated_client.post(
            "/api/v1/financial",
            json={
                "financial_reports_date": "2025-09-20T10:00",
                "financial_reports_academic_year": "2025-2026",
                "financial_reports_semester": "1st Semester",
                "financial_reports_status": "Upcoming",
                "financial_reports_title": "Integration Financial Report",
                "financial_reports_events_id": event_id,
            },
        )
        assert financial_response.status_code == 201
        report_id = financial_response.json()["data"]["financial_reports_id"]

        # Documentation
        documentation_response = authenticated_client.post(
            "/api/v1/documentation",
            data={
                "data": json.dumps(
                    {
                        "documentation_type": "Activity Report",
                        "documentation_status": "Done",
                        "documentation_academic_year": "2025-2026",
                        "documentation_semester": "1st Semester",
                        "documentation_date_of_submission": "2025-09-20T00:00:00",
                        "documentation_rating": 4.5,
                        "documentation_comments_suggestions": "Great integration",
                        "activity_report_items": [
                            {"item_type": "strength", "item_text": "Smooth flow"},
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
                        "evaluation_student_names": ["Alice Smith"],
                    }
                )
            },
        )
        assert documentation_response.status_code == 201
        doc_id = documentation_response.json()["data"]["documentation_id"]

        # List endpoints for every feature
        assert authenticated_client.get("/api/v1/concept-papers").status_code == 200
        assert authenticated_client.get("/api/v1/events").status_code == 200
        assert authenticated_client.get("/api/v1/meetings").status_code == 200
        assert authenticated_client.get("/api/v1/board-resolutions").status_code == 200
        assert authenticated_client.get("/api/v1/financial").status_code == 200
        assert authenticated_client.get("/api/v1/documentation").status_code == 200

        # Detail endpoints
        assert authenticated_client.get(f"/api/v1/concept-papers/{paper_id}").status_code == 200
        assert authenticated_client.get(f"/api/v1/events/{event_id}").status_code == 200
        assert authenticated_client.get(f"/api/v1/meetings/{meeting_id}").status_code == 200
        assert authenticated_client.get(f"/api/v1/board-resolutions/{resolution_id}").status_code == 200
        assert authenticated_client.get(f"/api/v1/financial/{report_id}").status_code == 200
        assert authenticated_client.get(f"/api/v1/documentation/{doc_id}").status_code == 200

        # Account
        assert authenticated_client.get("/api/v1/account/me").status_code == 200

        # AI generation endpoints
        ai_response = authenticated_client.post(
            "/api/v1/concept-papers/generate-descriptions",
            json={"subject": "Integration test"},
        )
        assert ai_response.status_code == 200
        assert "content" in ai_response.json()["data"]

        ai_resolution = authenticated_client.post(
            "/api/v1/board-resolutions/generate-description",
            json={
                "event_name": "Integration Event",
                "title": "Integration Resolution",
                "total_amount": "15000",
                "date": "2025-09-20T10:00",
            },
        )
        assert ai_resolution.status_code == 200
        assert "content" in ai_resolution.json()["data"]


class TestAdminDashboardFlow:
    """Integration coverage for the admin dashboard and audit log endpoints."""

    def test_admin_dashboard(self, fastapi_client, admin_user):
        response = fastapi_client.get(
            "/api/v1/admin/dashboard",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200

    def test_admin_audit_logs(self, fastapi_client, admin_user):
        response = fastapi_client.get(
            "/api/v1/admin/audit-logs",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 0
        assert "page" in data
        assert "per_page" in data
