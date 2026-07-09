"""
General helper functions for E-Council.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from flask import request

from models import ConceptPaperForms, Events
from repositories import repo


def get_distinct_academic_years() -> list[Any]:
    """
    Get distinct academic years from events.

    Returns:
        List of distinct academic years ordered by most recent
    """
    return repo.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()


def get_concept_papers() -> list[ConceptPaperForms]:
    """
    Get all concept papers.

    Returns:
        List of all concept paper forms
    """
    return ConceptPaperForms.query.all()


def safe_decimal_conversion(value: Any) -> Decimal | str:
    """
    Safely convert a value to Decimal.

    Args:
        value: Value to convert

    Returns:
        Decimal representation of the value, or string if conversion fails
    """
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return str(value)


def allowed_image_file(filename: str) -> bool:
    """
    Check if a file has an allowed image extension.

    Args:
        filename: Name of the file to check

    Returns:
        True if file has allowed extension, False otherwise
    """
    allowed_extensions = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def get_pagination_args(default_per_page: int = 10) -> tuple[int, int]:
    """
    Retrieve page and per_page query parameters for pagination.

    Args:
        default_per_page: Default number of items per page

    Returns:
        Tuple of (page, per_page)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", default_per_page, type=int)

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = default_per_page

    return page, per_page
