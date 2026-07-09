"""Unit tests for the AI service and provider abstraction."""

from unittest.mock import MagicMock

import pytest

from services.ai import (
    AIError,
    MockAIProvider,
    generate_concept_paper_body,
    generate_concept_paper_consent,
    generate_concept_paper_descriptions,
    generate_concept_paper_learning_outcomes,
    generate_concept_paper_objectives,
    generate_concept_paper_participants,
    generate_content,
    get_ai,
)
from services.ai.helpers import format_datetime_range


class TestFormatDatetimeRange:
    def test_valid_datetime_range(self):
        result = format_datetime_range("2024-01-15T09:00", "2024-01-15T12:00")
        assert result.success is True
        assert result.data == ("January 15, 2024 at 09:00 AM", "January 15, 2024 at 12:00 PM")

    def test_invalid_date_format(self):
        result = format_datetime_range("not-a-date", "2024-01-15T12:00")
        assert result.success is False
        assert result.error == "Invalid date format"


class TestGenerateConceptPaperBody:
    def test_success(self, mock_ai):
        result = generate_concept_paper_body("Seminar", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is True
        assert result.data == "Generated AI content"

    def test_missing_required_fields(self, mock_ai):
        result = generate_concept_paper_body("Seminar", "", "", "")
        assert result.success is False
        assert result.error == "Missing required fields"

    def test_invalid_dates(self, mock_ai):
        result = generate_concept_paper_body("Seminar", "bad-date", "2024-01-15T12:00", "Test Venue")
        assert result.success is False
        assert result.error == "Invalid date format"

    def test_handles_generation_exception(self, mock_ai, monkeypatch):
        monkeypatch.setattr(mock_ai, "generate_text", MagicMock(side_effect=RuntimeError("API down")))
        result = generate_concept_paper_body("Seminar", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is False
        assert "API down" in result.error


class TestGenerateConceptPaperDescriptions:
    def test_success(self, mock_ai):
        result = generate_concept_paper_descriptions("Workshop")
        assert result.success is True
        assert result.data == "Generated AI content"

    def test_missing_subject(self, mock_ai):
        result = generate_concept_paper_descriptions("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperObjectives:
    def test_success(self, mock_ai):
        result = generate_concept_paper_objectives("Workshop")
        assert result.success is True

    def test_missing_subject(self, mock_ai):
        result = generate_concept_paper_objectives("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperLearningOutcomes:
    def test_success(self, mock_ai):
        result = generate_concept_paper_learning_outcomes("Workshop")
        assert result.success is True

    def test_missing_subject(self, mock_ai):
        result = generate_concept_paper_learning_outcomes("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperParticipants:
    def test_extracts_digits(self, mock_ai):
        mock_ai.response = "42 participants"
        result = generate_concept_paper_participants("Workshop")
        assert result.success is True
        assert result.data == "42"

    def test_missing_subject(self, mock_ai):
        result = generate_concept_paper_participants("")
        assert result.success is False
        assert result.error == "Missing subject"


class TestGenerateConceptPaperConsent:
    def test_success(self, mock_ai):
        result = generate_concept_paper_consent("Workshop", "2024-01-15T09:00", "2024-01-15T12:00", "Test Venue")
        assert result.success is True

    def test_missing_fields(self, mock_ai):
        result = generate_concept_paper_consent("Workshop", "", "", "")
        assert result.success is False
        assert result.error == "Missing required fields"


class TestGenerateContent:
    def test_success(self, mock_ai):
        result = generate_content("Hello")
        assert result.success is True
        assert result.data == "Generated AI content"


class TestMockAIProvider:
    def test_generate_text(self):
        provider = MockAIProvider("Test response")
        assert provider.generate_text("prompt") == "Test response"

    def test_upload_file(self):
        provider = MockAIProvider()
        assert provider.upload_file("test.txt") == {"file_path": "test.txt", "mime_type": None}


class TestGetAI:
    def test_returns_configured_provider(self, app):
        app.config["AI_PROVIDER"] = "mock"
        assert isinstance(get_ai(app), MockAIProvider)

    def test_unknown_provider_raises(self, app):
        app.config["AI_PROVIDER"] = "unknown"
        with pytest.raises(AIError):
            get_ai(app)
