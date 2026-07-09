"""
General helper functions for E-Council.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from extensions import db
from models import ConceptPaperForms, Events


def get_distinct_academic_years() -> list[Any]:
    """
    Get distinct academic years from events.

    Returns:
        List of distinct academic years ordered by most recent
    """
    return db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()


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
