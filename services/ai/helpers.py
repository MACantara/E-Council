"""AI helper utilities."""

from datetime import datetime

from services.base import ServiceResult


def format_datetime_range(start_date: str, end_date: str) -> ServiceResult[tuple[str, str]]:
    """Parse ISO-like datetime strings and return a formatted range."""
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
        formatted_start = start_date_obj.strftime("%B %d, %Y at %I:%M %p")
        formatted_end = end_date_obj.strftime("%B %d, %Y at %I:%M %p")
    except ValueError:
        return ServiceResult.fail("Invalid date format")
    return ServiceResult.ok((formatted_start, formatted_end))
