"""Unit tests for the board resolutions service."""

import json
from unittest.mock import MagicMock

import pytest
from werkzeug.exceptions import HTTPException

from models import BoardResolutions
from services import board_resolutions
from tests.factories import BoardResolutionsFactory, SignatoriesFactory


@pytest.fixture
def mock_board_model(monkeypatch):
    """Replace the module-level Gemini model with a mocked instance."""
    mock = MagicMock()
    mock.generate_content.return_value = MagicMock(text="Generated AI description")
    monkeypatch.setattr("services.board_resolutions.model", mock)
    return mock


class TestDeleteBoardResolution:
    def test_get_renders_delete_template(self, app_context, auth_service_context, sample_user):
        resolution = BoardResolutionsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context():
            response = board_resolutions.delete_board_resolution(resolution.board_resolutions_id)
        assert isinstance(response, str)

    def test_post_deletes_resolution(self, app_context, auth_service_context, sample_user):
        resolution = BoardResolutionsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(method="POST"):
            response = board_resolutions.delete_board_resolution(resolution.board_resolutions_id)
        assert response.status_code == 302
        assert BoardResolutions.query.get(resolution.board_resolutions_id) is None

    def test_delete_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        resolution = BoardResolutionsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with pytest.raises(HTTPException), auth_service_context(user=other_user):
            board_resolutions.delete_board_resolution(resolution.board_resolutions_id)


class TestUpdateBoardResolutionStatus:
    def test_update_status(self, app_context, auth_service_context, sample_user):
        resolution = BoardResolutionsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(
            method="POST",
            data=json.dumps({"status": "Done"}),
            content_type="application/json",
        ):
            response = board_resolutions.update_board_resolution_status(resolution.board_resolutions_id)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        updated = BoardResolutions.query.get(resolution.board_resolutions_id)
        assert updated.board_resolutions_status == "Done"

    def test_update_status_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        resolution = BoardResolutionsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with (
            pytest.raises(HTTPException),
            auth_service_context(
                method="POST",
                data=json.dumps({"status": "Done"}),
                content_type="application/json",
                user=other_user,
            ),
        ):
            board_resolutions.update_board_resolution_status(resolution.board_resolutions_id)


class TestGenerateDescription:
    def test_success(self, app_context, auth_service_context, sample_user, mock_board_model):
        with auth_service_context(
            method="POST",
            data=json.dumps(
                {"event_name": "Event", "title": "Title", "date": "2024-01-15T09:00", "total_amount": "5000"}
            ),
            content_type="application/json",
        ):
            response = board_resolutions.generate_description()
        assert response.status_code == 200
        assert response.get_json()["description"] == "Generated AI description"

    def test_missing_event_name_and_title(self, app_context, auth_service_context, sample_user):
        with auth_service_context(
            method="POST",
            data=json.dumps({"event_name": "", "title": ""}),
            content_type="application/json",
        ):
            response = board_resolutions.generate_description()
        assert response.status_code == 400


class TestGenerateBoardResolutionPdf:
    def test_generates_pdf(self, app_context, auth_service_context, sample_user):
        resolution = BoardResolutionsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            approved_by_signatory=SignatoriesFactory(),
        )
        with auth_service_context():
            response = board_resolutions.generate_board_resolution_pdf(resolution.board_resolutions_id)
        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert "Content-Length" in response.headers
