"""Tests for the FastAPI board resolution endpoints."""

from __future__ import annotations

from models import BoardResolutions


def _default_payload(**overrides):
    """Return a valid board resolution payload with optional overrides."""
    payload = {
        "board_resolutions_date": "2025-09-20T10:00",
        "board_resolutions_title": "FastAPI Test Board Resolution",
        "board_resolutions_description": "A test description.",
        "board_resolutions_total_amount": "15000",
        "board_resolutions_academic_year": "2025-2026",
        "board_resolutions_semester": "1st Semester",
        "board_resolutions_status": "Upcoming",
        "board_resolutions_prepared_by": 1,
        "board_resolutions_approved_by": 1,
        "student_signatory_ids": [],
    }
    payload.update(overrides)
    return payload


def _create_resolution(authenticated_client, **overrides):
    """Create a board resolution through the API and return the response."""
    response = authenticated_client.post(
        "/api/v1/board-resolutions", json=_default_payload(**overrides)
    )
    assert response.status_code == 201
    return response.json()["data"]


class TestBoardResolutions:
    """FastAPI board resolution endpoint tests."""

    def test_create_board_resolution(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/board-resolutions", json=_default_payload()
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["board_resolutions_title"] == "FastAPI Test Board Resolution"
        assert data["board_resolutions_status"] == "Upcoming"

    def test_list_board_resolutions(self, authenticated_client):
        _create_resolution(authenticated_client)
        response = authenticated_client.get("/api/v1/board-resolutions")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1

    def test_list_board_resolutions_filtered_by_status(self, authenticated_client):
        _create_resolution(authenticated_client)
        response = authenticated_client.get("/api/v1/board-resolutions?status=Done")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_list_board_resolutions_search(self, authenticated_client):
        _create_resolution(authenticated_client)
        response = authenticated_client.get("/api/v1/board-resolutions?search=FastAPI")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1

    def test_get_board_resolution(self, authenticated_client):
        resolution = _create_resolution(authenticated_client)
        response = authenticated_client.get(
            f"/api/v1/board-resolutions/{resolution['board_resolutions_id']}"
        )
        assert response.status_code == 200
        assert response.json()["data"]["board_resolutions_id"] == resolution[
            "board_resolutions_id"
        ]

    def test_update_board_resolution(self, authenticated_client):
        resolution = _create_resolution(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/board-resolutions/{resolution['board_resolutions_id']}",
            json={"board_resolutions_title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["board_resolutions_title"] == "Updated Title"

    def test_update_status(self, authenticated_client):
        resolution = _create_resolution(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/board-resolutions/{resolution['board_resolutions_id']}/status",
            json={"status": "Done"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["board_resolutions_status"] == "Done"

    def test_delete_board_resolution(self, authenticated_client, fastapi_db):
        resolution = _create_resolution(authenticated_client)
        response = authenticated_client.delete(
            f"/api/v1/board-resolutions/{resolution['board_resolutions_id']}"
        )
        assert response.status_code == 200
        assert fastapi_db.get(BoardResolutions, resolution["board_resolutions_id"]) is None

    def test_generate_description(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/board-resolutions/generate-description",
            json={"event_name": "Test Event", "title": "Test Title"},
        )
        assert response.status_code == 200
        assert "content" in response.json()["data"]

    def test_download_pdf(self, authenticated_client):
        resolution = _create_resolution(authenticated_client)
        response = authenticated_client.get(
            f"/api/v1/board-resolutions/{resolution['board_resolutions_id']}/pdf"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_department_scoping(self, authenticated_client, fastapi_db):
        """Non-admin users can only see resolutions from their own department."""
        from models import BoardResolutions, Departments

        _create_resolution(authenticated_client)

        other_department = Departments(departments_name="Other Department")
        fastapi_db.add(other_department)
        fastapi_db.commit()

        other_resolution = BoardResolutions(
            board_resolutions_title="Other Resolution",
            board_resolutions_departments_id=other_department.departments_id,
            board_resolutions_prepared_by=999,
        )
        fastapi_db.add(other_resolution)
        fastapi_db.commit()

        response = authenticated_client.get("/api/v1/board-resolutions")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1
