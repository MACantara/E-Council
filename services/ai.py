"""
AI service for E-Council.

Encapsulates Google Gemini interactions and returns ServiceResult objects instead
of raising HTTP exceptions.
"""

from datetime import datetime
from typing import Any

from google import genai
from google.genai import types

from config import AIConfig
from services.base import ServiceResult

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Return a configured Google GenAI client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=AIConfig.GOOGLE_GEMINI_AI_API_KEY)
    return _client


def _safety_settings() -> list[types.SafetySetting]:
    """Return the default safety settings for Gemini requests."""
    return [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]


def _generate_config() -> types.GenerateContentConfig:
    """Return a GenerateContentConfig with default safety settings."""
    return types.GenerateContentConfig(safety_settings=_safety_settings())


def generate_content(contents: str | list[Any], model: str | None = None) -> ServiceResult:
    """Generate content using Gemini and return a ServiceResult."""
    try:
        response = get_client().models.generate_content(
            model=model or AIConfig.GEMINI_MODEL,
            contents=contents,
            config=_generate_config(),
        )
        if response and response.text:
            return ServiceResult.ok(response.text.strip())
        return ServiceResult.fail("Invalid response from AI model")
    except Exception as exc:  # noqa: BLE001
        return ServiceResult.fail(str(exc))


def upload_file(file_path: str) -> ServiceResult:
    """Upload a file to Gemini and return a ServiceResult."""
    try:
        uploaded_file = get_client().files.upload(file=file_path)
        return ServiceResult.ok(uploaded_file)
    except Exception as exc:  # noqa: BLE001
        return ServiceResult.fail(str(exc))


def _format_datetime_range(start_date: str, end_date: str) -> ServiceResult[tuple[str, str]]:
    """Parse ISO-like datetime strings and return a formatted range."""
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
        formatted_start = start_date_obj.strftime("%B %d, %Y at %I:%M %p")
        formatted_end = end_date_obj.strftime("%B %d, %Y at %I:%M %p")
    except ValueError:
        return ServiceResult.fail("Invalid date format")
    return ServiceResult.ok((formatted_start, formatted_end))


def generate_concept_paper_body(subject: str, start_date: str, end_date: str, location: str) -> ServiceResult:
    """Generate a formal body text for a concept paper."""
    if not all([subject, start_date, end_date, location]):
        return ServiceResult.fail("Missing required fields")

    result = _format_datetime_range(start_date, end_date)
    if not result:
        return result
    assert result.data is not None
    formatted_start, formatted_end = result.data

    prompt = f"""Generate a formal body text for a concept paper with the following details:
    Event: {subject}
    Date and Time: From {formatted_start} to {formatted_end}
    Location: {location}

    Requirements:
    1. Use formal and professional language
    2. Explain the purpose and significance of the event
    3. Highlight key activities or components
    4. Keep it concise but informative
    5. Include relevant details about timing and location
    6. Make it engaging and well-structured
    7. Avoid any unnecessary jargon
    8. Format as a single cohesive paragraph"""

    result = generate_content(prompt)
    if not result:
        return result
    return ServiceResult.ok(result.data)


def generate_concept_paper_descriptions(subject: str) -> ServiceResult:
    """Generate a description paragraph for a concept paper."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    prompt = f"""Generate a detailed description for a concept paper about {subject}.

    Requirements:
    1. Write as a single cohesive paragraph
    2. Provide a comprehensive overview of the event/activity
    3. Include the rationale and importance
    4. Describe the target audience and potential impact
    5. Keep language formal but accessible
    6. Focus on practical and measurable aspects
    7. Do not use any text formatting or special characters
    8. Do not use bullet points or line breaks
    9. Include potential benefits to participants
    10. Keep it concise but informative"""

    result = generate_content(prompt)
    if not result:
        return result
    return ServiceResult.ok(result.data)


def generate_concept_paper_objectives(subject: str) -> ServiceResult:
    """Generate SMART objectives for a concept paper."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    prompt = f"""Generate specific objectives for {subject}.

    Requirements:
    1. Create 3-5 SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
    2. Focus on concrete outcomes
    3. Use action verbs
    4. Make them relevant to the event purpose
    5. Ensure they are realistic and achievable
    6. Format as a bullet-point list
    7. Keep each objective concise
    8. Align with academic/educational goals"""

    result = generate_content(prompt)
    if not result:
        return result
    return ServiceResult.ok(result.data)


def generate_concept_paper_learning_outcomes(subject: str) -> ServiceResult:
    """Generate learning outcomes for a concept paper."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    prompt = f"""Generate learning outcomes for {subject}.

    Requirements:
    1. Create 3-5 specific learning outcomes
    2. Use Bloom's Taxonomy verbs
    3. Focus on knowledge, skills, and attitudes
    4. Make them measurable and observable
    5. Align with event objectives
    6. Keep language clear and specific
    7. Format as a bullet-point list
    8. Consider both immediate and long-term learning"""

    result = generate_content(prompt)
    if not result:
        return result
    return ServiceResult.ok(result.data)


def generate_concept_paper_participants(subject: str) -> ServiceResult:
    """Suggest a reasonable number of expected participants."""
    if not subject:
        return ServiceResult.fail("Missing subject")

    prompt = f"""Suggest a reasonable number of expected participants for {subject}.

    Requirements:
    1. Consider the type of event
    2. Account for venue capacity
    3. Think about resource management
    4. Ensure meaningful participation
    5. Consider typical attendance patterns
    6. Return only a number between 20 and 200"""

    result = generate_content(prompt)
    if not result:
        return result
    assert result.data is not None
    # Extract just the number from the response
    number = "".join(filter(str.isdigit, result.data))
    return ServiceResult.ok(number)


def generate_concept_paper_consent(subject: str, start_date: str, end_date: str, location: str) -> ServiceResult:
    """Generate parent/guardian consent form content."""
    if not all([subject, start_date, end_date, location]):
        return ServiceResult.fail("Missing required fields")

    result = _format_datetime_range(start_date, end_date)
    if not result:
        return result
    assert result.data is not None
    formatted_start, formatted_end = result.data

    prompt = f"""Generate a parent/guardian consent form content for {subject}.

    Event Details:
    - Event: {subject}
    - Date and Time: From {formatted_start} to {formatted_end}
    - Location: {location}

    Requirements:
    1. Use formal and professional language
    2. Include clear permission statement
    3. Specify event details and purpose
    4. Mention safety measures and supervision
    5. Include contact information section
    6. Add emergency contact section
    7. Include medical information section
    8. Add signature lines for parent/guardian
    9. Keep it concise but comprehensive
    10. Include any relevant waivers or disclaimers"""

    result = generate_content(prompt)
    if not result:
        return result
    return ServiceResult.ok(result.data)
