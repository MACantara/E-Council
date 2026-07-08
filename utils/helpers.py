"""
General helper functions for E-Council.
"""

from decimal import Decimal, InvalidOperation
# Note: These imports will need to be adjusted based on final model structure
# For now, importing from app.py (will be refactored later)
# from models.event import Events
# from models.concept_paper import ConceptPaperForms

# Temporary imports from app.py (will be refactored later)
from app import db, Events, ConceptPaperForms


def get_distinct_academic_years():
    """
    Get distinct academic years from events.
    
    Returns:
        List of distinct academic years ordered by most recent
    """
    return db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()


def get_concept_papers():
    """
    Get all concept papers.
    
    Returns:
        List of all concept paper forms
    """
    return ConceptPaperForms.query.all()


def safe_decimal_conversion(value):
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


def allowed_image_file(filename):
    """
    Check if a file has an allowed image extension.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file has allowed extension, False otherwise
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS