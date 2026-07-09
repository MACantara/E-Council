"""Unit tests for the AI service."""

from unittest.mock import MagicMock, patch

import pytest

from services import ai


@pytest.fixture
def mock_model(monkeypatch):
    """Replace the module-level Gemini model with a mocked instance."""
    mock = MagicMock()
    mock.generate_content.return_value = MagicMock(text="Generated AI content")
    monkeypatch.setattr("services.ai._model", lambda: mock)
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
    def test_success(self, mock_model):
        result = ai.generate_concept_paper_body("Seminar", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is True
        assert result.data == "Generated AI content"
        mock_model.generate_content.assert_called_once()

    def test_missing_required_fields(self, mock_model):
        result = ai.generate_concept_paper_body("Seminar", "", "", "")
        assert result.success is False
        assert result.error == "Missing required fields"
        mock_model.generate_content.assert_not_called()

    def test_invalid_dates(self, mock_model):
        result = ai.generate_concept_paper_body("Seminar", "bad-date", "2024-01-15T12:00", "Test Venue")
        assert result.success is False
        assert result.error == "Invalid date format"
        mock_model.generate_content.assert_not_called()

    def test_handles_generation_exception(self, mock_model):
        mock_model.generate_content.side_effect = RuntimeError("API down")
        result = ai.generate_concept_paper_body("Seminar", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is False
        assert "API down" in result.error


class TestGenerateConceptPaperDescriptions:
    def test_success(self, mock_model):
        result = ai.generate_concept_paper_descriptions("Workshop")
        assert result.success is True
        assert result.data == "Generated AI content"

    def test_missing_subject(self, mock_model):
        result = ai.generate_concept_paper_descriptions("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperObjectives:
    def test_success(self, mock_model):
        result = ai.generate_concept_paper_objectives("Workshop")
        assert result.success is True

    def test_missing_subject(self, mock_model):
        result = ai.generate_concept_paper_objectives("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperLearningOutcomes:
    def test_success(self, mock_model):
        result = ai.generate_concept_paper_learning_outcomes("Workshop")
        assert result.success is True

    def test_missing_subject(self, mock_model):
        result = ai.generate_concept_paper_learning_outcomes("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperParticipants:
    def test_extracts_digits(self, mock_model):
        mock_model.generate_content.return_value = MagicMock(text="42 participants")
        result = ai.generate_concept_paper_participants("Workshop")
        assert result.success is True
        assert result.data == "42"

    def test_missing_subject(self, mock_model):
        result = ai.generate_concept_paper_participants("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperConsent:
    def test_success(self, mock_model):
        result = ai.generate_concept_paper_consent("Workshop", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is True

    def test_missing_fields(self, mock_model):
        result = ai.generate_concept_paper_consent("Workshop", "", "", "")
        assert result.success is False
        assert result.error == "Missing required fields"


class TestSafetySettings:
    def test_returns_dict(self):
        assert isinstance(ai._safety_settings(), dict)


class TestModel:
    @patch("services.ai.genai")
    def test_configures_and_returns_model(self, mock_genai, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr("services.ai.AIConfig.GOOGLE_GEMINI_AI_API_KEY", "test-key")
            m.setattr("services.ai.AIConfig.GEMINI_MODEL", "test-model")
            ai._model()
        mock_genai.configure.assert_called_once_with(api_key="test-key")
        mock_genai.GenerativeModel.assert_called_once_with("test-model")
