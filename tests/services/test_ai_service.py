"""Unit tests for the AI service."""

from unittest.mock import MagicMock

import pytest

from services import ai


@pytest.fixture
def mock_client(monkeypatch):
    """Replace the Google GenAI client with a mocked instance."""
    mock = MagicMock()
    mock.models.generate_content.return_value = MagicMock(text="Generated AI content")
    monkeypatch.setattr("services.ai._client", mock)
    return mock


class TestFormatDatetimeRange:
    def test_valid_datetime_range(self):
        result = ai._format_datetime_range("2024-01-15T09:00", "2024-01-15T12:00")
        assert result.success is True
        assert result.data == ("January 15, 2024 at 09:00 AM", "January 15, 2024 at 12:00 PM")

    def test_invalid_date_format(self):
        result = ai._format_datetime_range("not-a-date", "2024-01-15T12:00")
        assert result.success is False
        assert result.error == "Invalid date format"


class TestGenerateConceptPaperBody:
    def test_success(self, mock_client):
        result = ai.generate_concept_paper_body("Seminar", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is True
        assert result.data == "Generated AI content"
        mock_client.models.generate_content.assert_called_once()

    def test_missing_required_fields(self, mock_client):
        result = ai.generate_concept_paper_body("Seminar", "", "", "")
        assert result.success is False
        assert result.error == "Missing required fields"
        mock_client.models.generate_content.assert_not_called()

    def test_invalid_dates(self, mock_client):
        result = ai.generate_concept_paper_body("Seminar", "bad-date", "2024-01-15T12:00", "Test Venue")
        assert result.success is False
        assert result.error == "Invalid date format"
        mock_client.models.generate_content.assert_not_called()

    def test_handles_generation_exception(self, mock_client):
        mock_client.models.generate_content.side_effect = RuntimeError("API down")
        result = ai.generate_concept_paper_body("Seminar", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is False
        assert "API down" in result.error


class TestGenerateConceptPaperDescriptions:
    def test_success(self, mock_client):
        result = ai.generate_concept_paper_descriptions("Workshop")
        assert result.success is True
        assert result.data == "Generated AI content"

    def test_missing_subject(self, mock_client):
        result = ai.generate_concept_paper_descriptions("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperObjectives:
    def test_success(self, mock_client):
        result = ai.generate_concept_paper_objectives("Workshop")
        assert result.success is True

    def test_missing_subject(self, mock_client):
        result = ai.generate_concept_paper_objectives("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperLearningOutcomes:
    def test_success(self, mock_client):
        result = ai.generate_concept_paper_learning_outcomes("Workshop")
        assert result.success is True

    def test_missing_subject(self, mock_client):
        result = ai.generate_concept_paper_learning_outcomes("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperParticipants:
    def test_extracts_digits(self, mock_client):
        mock_client.models.generate_content.return_value = MagicMock(text="42 participants")
        result = ai.generate_concept_paper_participants("Workshop")
        assert result.success is True
        assert result.data == "42"

    def test_missing_subject(self, mock_client):
        result = ai.generate_concept_paper_participants("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperConsent:
    def test_success(self, mock_client):
        result = ai.generate_concept_paper_consent("Workshop", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is True

    def test_missing_fields(self, mock_client):
        result = ai.generate_concept_paper_consent("Workshop", "", "", "")
        assert result.success is False
        assert result.error == "Missing required fields"


class TestSafetySettings:
    def test_returns_list(self):
        assert isinstance(ai._safety_settings(), list)
        assert len(ai._safety_settings()) > 0


class TestClient:
    def test_creates_client_with_configured_api_key(self, monkeypatch):
        mock_client_cls = MagicMock()
        monkeypatch.setattr("services.ai.genai.Client", mock_client_cls)
        monkeypatch.setattr("services.ai._client", None)
        monkeypatch.setattr("services.ai.AIConfig.GOOGLE_GEMINI_AI_API_KEY", "test-key")
        ai.get_client()
        mock_client_cls.assert_called_once_with(api_key="test-key")
