"""
AI generation route tests for the E-Council application.

These tests mock the Gemini ``model.generate_content`` method so the routes
that generate concept paper body, descriptions, consent, participant numbers,
and board resolution descriptions can be tested without making external API calls.
"""

import os
import sys

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_model(monkeypatch):
    """Replace the module-level Gemini model with a mocked instance."""
    mock = MagicMock()
    mock.generate_content.return_value = MagicMock(text="Generated AI content")
    monkeypatch.setattr("routes.concept_papers.model", mock)
    monkeypatch.setattr("routes.board_resolutions.model", mock)
    return mock


class TestConceptPaperAI:
    """AI generation tests for the concept paper routes."""

    def test_generate_body(self, auth_client, mock_model):
        response = auth_client.post(
            "/concept-papers/generate-body",
            json={
                "subject": "Seminar",
                "start_date": "2024-01-15T09:00",
                "end_date": "2024-01-15T12:00",
                "location": "Test Venue",
            },
        )
        assert response.status_code == 200
        assert response.json["content"] == "Generated AI content"
        mock_model.generate_content.assert_called()

    def test_generate_descriptions(self, auth_client, mock_model):
        response = auth_client.post("/concept-papers/generate-descriptions", json={"subject": "Workshop"})
        assert response.status_code == 200
        assert response.json["content"] == "Generated AI content"
        mock_model.generate_content.assert_called()

    def test_generate_consent(self, auth_client, mock_model):
        response = auth_client.post(
            "/concept-papers/generate-consent",
            json={
                "subject": "Workshop",
                "start_date": "2024-01-15T09:00",
                "end_date": "2024-01-15T12:00",
                "location": "Test Venue",
            },
        )
        assert response.status_code == 200
        assert response.json["content"] == "Generated AI content"
        mock_model.generate_content.assert_called()

    def test_generate_participants(self, auth_client, mock_model):
        # The route extracts digits from the AI response to return a number.
        mock_model.generate_content.return_value.text = "42 participants"
        response = auth_client.post("/concept-papers/generate-participants", json={"subject": "Workshop"})
        assert response.status_code == 200
        assert response.json["content"] == "42"
        mock_model.generate_content.assert_called()

    def test_generate_body_missing_fields(self, auth_client):
        response = auth_client.post("/concept-papers/generate-body", json={"subject": "Seminar"})
        assert response.status_code == 400


class TestBoardResolutionsAI:
    """AI generation tests for the board resolution routes."""

    def test_generate_description(self, auth_client, mock_model):
        response = auth_client.post(
            "/board-resolutions/generate-description",
            json={
                "event_name": "Test Event",
                "title": "Test Resolution",
                "date": "2024-01-15T09:00",
                "total_amount": "10000",
            },
        )
        assert response.status_code == 200
        assert response.json["description"] == "Generated AI content"
        mock_model.generate_content.assert_called()

    def test_generate_description_missing_fields(self, auth_client):
        response = auth_client.post("/board-resolutions/generate-description", json={"event_name": "Test Event"})
        assert response.status_code == 400
