"""High-level concept paper generation helpers."""

from services.base import ServiceResult

from .helpers import format_datetime_range
from .prompts import (
    concept_paper_body,
    concept_paper_consent,
    concept_paper_description,
    concept_paper_learning_outcomes,
    concept_paper_objectives,
    concept_paper_participants,
)
from .service import generate_content


def generate_concept_paper_body(subject: str, start_date: str, end_date: str, location: str) -> ServiceResult:
    """Generate a formal body text for a concept paper."""
    if not all([subject, start_date, end_date, location]):
        return ServiceResult.fail("Missing required fields")

    result = format_datetime_range(start_date, end_date)
    if not result:
        return result
    assert result.data is not None
    formatted_start, formatted_end = result.data

    prompt = concept_paper_body(subject, formatted_start, formatted_end, location)
    return generate_content(prompt)


def generate_concept_paper_descriptions(subject: str) -> ServiceResult:
    """Generate a description paragraph for a concept paper."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    return generate_content(concept_paper_description(subject))


def generate_concept_paper_objectives(subject: str) -> ServiceResult:
    """Generate SMART objectives for a concept paper."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    return generate_content(concept_paper_objectives(subject))


def generate_concept_paper_learning_outcomes(subject: str) -> ServiceResult:
    """Generate learning outcomes for a concept paper."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    return generate_content(concept_paper_learning_outcomes(subject))


def generate_concept_paper_participants(subject: str) -> ServiceResult:
    """Suggest a reasonable number of expected participants."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    result = generate_content(concept_paper_participants(subject))
    if not result:
        return result
    assert result.data is not None
    number = "".join(filter(str.isdigit, result.data))
    return ServiceResult.ok(number)


def generate_concept_paper_consent(subject: str, start_date: str, end_date: str, location: str) -> ServiceResult:
    """Generate parent/guardian consent form content."""
    if not all([subject, start_date, end_date, location]):
        return ServiceResult.fail("Missing required fields")

    result = format_datetime_range(start_date, end_date)
    if not result:
        return result
    assert result.data is not None
    formatted_start, formatted_end = result.data

    prompt = concept_paper_consent(subject, formatted_start, formatted_end, location)
    return generate_content(prompt)
