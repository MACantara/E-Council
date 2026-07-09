"""
Jinja2 custom filters for E-Council templates.
"""

from typing import Any


def truncate_text(text: str | None, length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a specified length with a suffix.

    Args:
        text: Text to truncate
        length: Maximum length before truncation
        suffix: Suffix to add when truncated

    Returns:
        Truncated text or empty string if text is None
    """
    if text is None:
        return ""
    if len(text) <= length:
        return text
    return text[: length - len(suffix)] + suffix


def has_events(events: list[Any], semester: str, academic_year: str) -> bool:
    """
    Check if there are events for a given semester and academic year.

    Args:
        events: List of events to check
        semester: Semester to filter by
        academic_year: Academic year to filter by

    Returns:
        True if events exist for the given semester and year, False otherwise
    """
    return any(event.events_semester == semester and event.events_academic_year == academic_year for event in events)


def has_resolutions(resolutions: list[Any], semester: str, academic_year: str) -> bool:
    """
    Check if there are board resolutions for a given semester and academic year.

    Args:
        resolutions: List of resolutions to check
        semester: Semester to filter by
        academic_year: Academic year to filter by

    Returns:
        True if resolutions exist for the given semester and year, False otherwise
    """
    return any(
        resolution.board_resolutions_semester == semester
        and resolution.board_resolutions_academic_year == academic_year
        for resolution in resolutions
    )


def has_meetings(meetings: list[Any], semester: str, academic_year: str) -> bool:
    """
    Check if there are meetings for a given semester and academic year.

    Args:
        meetings: List of meetings to check
        semester: Semester to filter by
        academic_year: Academic year to filter by

    Returns:
        True if meetings exist for the given semester and year, False otherwise
    """
    return any(
        meeting.minutes_of_the_meeting_semester == semester
        and meeting.minutes_of_the_meeting_academic_year == academic_year
        for meeting in meetings
    )


def has_financial_reports(reports: list[Any], semester: str, academic_year: str) -> bool:
    """
    Check if there are financial reports for a given semester and academic year.

    Args:
        reports: List of financial reports to check
        semester: Semester to filter by
        academic_year: Academic year to filter by

    Returns:
        True if financial reports exist for the given semester and year, False otherwise
    """
    return any(
        report.financial_reports_semester == semester and report.financial_reports_academic_year == academic_year
        for report in reports
    )


def has_papers(papers: list[Any], semester: str, academic_year: str) -> bool:
    """
    Check if there are concept papers for a given semester and academic year.

    Args:
        papers: List of concept papers to check
        semester: Semester to filter by
        academic_year: Academic year to filter by

    Returns:
        True if concept papers exist for the given semester and year, False otherwise
    """
    return any(
        paper.concept_paper_forms_semester == semester and paper.concept_paper_forms_academic_year == academic_year
        for paper in papers
    )


def has_documentations(documentations: list[list[Any]], semester: str, academic_year: str) -> bool:
    """
    Check if there are documentations for a given semester and academic year.

    Args:
        documentations: List of documentations to check
        semester: Semester to filter by
        academic_year: Academic year to filter by

    Returns:
        True if documentations exist for the given semester and year, False otherwise
    """
    return any(
        doc[0].documentation_semester == semester and doc[0].documentation_academic_year == academic_year
        for doc in documentations
    )


def register_filters(app: Any) -> None:
    """
    Register all custom Jinja2 filters with the Flask app.

    Args:
        app: Flask application instance
    """
    app.jinja_env.filters["truncate"] = truncate_text
    app.jinja_env.filters["has_events"] = has_events
    app.jinja_env.filters["has_resolutions"] = has_resolutions
    app.jinja_env.filters["has_meetings"] = has_meetings
    app.jinja_env.filters["has_financial_reports"] = has_financial_reports
    app.jinja_env.filters["has_papers"] = has_papers
    app.jinja_env.filters["has_documentations"] = has_documentations
