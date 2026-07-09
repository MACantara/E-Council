"""Tests for the FastAPI concept paper endpoints."""

from __future__ import annotations

import pytest
from models import ConceptPaperForms


def _default_payload(**overrides):
    """Return a valid concept paper payload with optional overrides."""
    payload = {
        "concept_paper_forms_academic_year": "2025-2026",
        "concept_paper_forms_semester": "1st Semester",
        "concept_paper_forms_status": "Upcoming",
        "concept_paper_forms_subject": "FastAPI Test Concept Paper",
        "concept_paper_forms_date": "2025-09-15T10:00",
        "concept_paper_forms_body": "This is a sample concept paper body.",
        "concept_paper_forms_event_start_date_and_time": "2025-09-20T08:00",
        "concept_paper_forms_event_end_date_and_time": "2025-09-20T17:00",
        "concept_paper_forms_location": "Online",
        "concept_paper_forms_participants": "Students",
        "concept_paper_forms_budget": "1000",
        "concept_paper_forms_descriptions": "A test description.",
        "concept_paper_forms_expected_number_of_participants": "50",
        "objectives": [{"objective_text": "Objective 1"}],
        "learning_outcomes": [{"learning_outcome_text": "Learning outcome 1"}],
    }
    payload.update(overrides)
    return payload


def _create_paper(authenticated_client, **overrides):
    """Create a concept paper through the API and return the response."""
    response = authenticated_client.post("/api/v1/concept-papers", json=_default_payload(**overrides))
    assert response.status_code == 201
    return response.json()["data"]


class TestConceptPapers:
    """FastAPI concept paper endpoint tests."""

    def test_create_concept_paper(self, authenticated_client):
        response = authenticated_client.post("/api/v1/concept-papers", json=_default_payload())
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["concept_paper_forms_subject"] == "FastAPI Test Concept Paper"
        assert data["concept_paper_forms_status"] == "Upcoming"
        assert len(data["objectives"]) == 1
        assert len(data["learning_outcomes"]) == 1

    def test_list_concept_papers(self, authenticated_client, fastapi_db):
        _create_paper(authenticated_client)
        response = authenticated_client.get("/api/v1/concept-papers")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1

    def test_list_concept_papers_filtered_by_status(self, authenticated_client):
        _create_paper(authenticated_client)
        response = authenticated_client.get("/api/v1/concept-papers?status=Done")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_list_concept_papers_search(self, authenticated_client):
        _create_paper(authenticated_client)
        response = authenticated_client.get("/api/v1/concept-papers?search=FastAPI")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1

    def test_get_concept_paper(self, authenticated_client):
        paper = _create_paper(authenticated_client)
        response = authenticated_client.get(f"/api/v1/concept-papers/{paper['concept_paper_forms_id']}")
        assert response.status_code == 200
        assert response.json()["data"]["concept_paper_forms_id"] == paper["concept_paper_forms_id"]

    def test_update_concept_paper(self, authenticated_client):
        paper = _create_paper(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/concept-papers/{paper['concept_paper_forms_id']}",
            json={"concept_paper_forms_subject": "Updated Subject"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["concept_paper_forms_subject"] == "Updated Subject"

    def test_update_status(self, authenticated_client):
        paper = _create_paper(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/concept-papers/{paper['concept_paper_forms_id']}/status",
            json={"status": "Done"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["concept_paper_forms_status"] == "Done"

    def test_delete_concept_paper(self, authenticated_client, fastapi_db):
        paper = _create_paper(authenticated_client)
        response = authenticated_client.delete(
            f"/api/v1/concept-papers/{paper['concept_paper_forms_id']}"
        )
        assert response.status_code == 200
        assert fastapi_db.query(ConceptPaperForms).get(paper["concept_paper_forms_id"]) is None

    def test_generate_body(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/concept-papers/generate-body",
            json={
                "subject": "Test",
                "start_date": "2025-09-20T08:00",
                "end_date": "2025-09-21T17:00",
                "location": "Online",
            },
        )
        assert response.status_code == 200
        assert "content" in response.json()["data"]

    def test_generate_descriptions(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/concept-papers/generate-descriptions",
            json={"subject": "Test"},
        )
        assert response.status_code == 200

    def test_generate_objectives(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/concept-papers/generate-objectives",
            json={"subject": "Test"},
        )
        assert response.status_code == 200

    def test_generate_learning_outcomes(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/concept-papers/generate-learning-outcomes",
            json={"subject": "Test"},
        )
        assert response.status_code == 200

    def test_generate_participants(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/concept-papers/generate-participants",
            json={"subject": "Test"},
        )
        assert response.status_code == 200

    def test_generate_consent(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/concept-papers/generate-consent",
            json={
                "subject": "Test",
                "start_date": "2025-09-20T08:00",
                "end_date": "2025-09-21T17:00",
                "location": "Online",
            },
        )
        assert response.status_code == 200

    def test_download_pdf(self, authenticated_client):
        paper = _create_paper(authenticated_client)
        response = authenticated_client.get(
            f"/api/v1/concept-papers/{paper['concept_paper_forms_id']}/pdf"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_department_scoping(self, authenticated_client, fastapi_db):
        """Non-admin users can only see papers from their own department."""
        from models import ConceptPaperForms, Departments

        _create_paper(authenticated_client)

        other_department = Departments(departments_name="Other Department")
        fastapi_db.add(other_department)
        fastapi_db.commit()

        other_paper = ConceptPaperForms(
            concept_paper_forms_subject="Other Paper",
            concept_paper_forms_departments_id=other_department.departments_id,
            concept_paper_forms_prepared_by=999,
        )
        fastapi_db.add(other_paper)
        fastapi_db.commit()

        response = authenticated_client.get("/api/v1/concept-papers")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1
