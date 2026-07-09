"""
Authentication helper functions for E-Council.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import LoginManager, current_user

from models import (
    ConceptPaperForms,
    DepartmentsEvents,
    Events,
    Documentation,
    FinancialReports,
    MinutesOfTheMeeting,
    BoardResolutions,
)

# Note: These imports will need to be adjusted based on final model structure
# For now, importing from app.py (will be refactored later)
# from models.user import Users

# Temporary imports from app.py (will be refactored later)
# Using lazy imports to avoid circular dependency with app.py


def load_user(user_id):
    """
    Load a user by ID for Flask-Login.
    
    Args:
        user_id: ID of the user to load
        
    Returns:
        User object or None if not found
    """
    from app import db, Users
    
    return db.session.get(Users, int(user_id))


def unauthorized():
    """
    Handle unauthorized access attempts.
    
    Returns:
        Redirect to login page with flash message
    """
    flash("You need to be logged in to access this page.", "error")
    return redirect(url_for("auth.login"))


def setup_login_manager(login_manager, app):
    """
    Configure Flask-Login for the application.
    
    Args:
        login_manager: Flask-Login LoginManager instance
        app: Flask application instance
    """
    login_manager.init_app(app)
    login_manager.user_loader(load_user)
    login_manager.unauthorized_handler(unauthorized)


def is_admin(user):
    """Return True if the user is authenticated and has the Admin role."""
    return user and user.is_authenticated and getattr(user, 'users_role', None) == 'Admin'


def _user_department_id(user):
    """Return the user's department id, or None if unavailable."""
    return getattr(user, 'users_departments_id', None)


def belongs_to_user_or_department(record, user):
    """
    Determine whether a user may access a resource.

    Admins are always allowed. Otherwise, the check is based on the model:

    - ConceptPaperForms: departments_id or prepared_by
    - Events: linked via DepartmentsEvents
    - Documentation: departments_id or prepared_by or the parent event
    - FinancialReports: departments_id or audited_and_prepared_by or the parent event
    - MinutesOfTheMeeting: departments_id or prepared_by
    - BoardResolutions: departments_id or prepared_by or the parent event
    """
    if not user or not user.is_authenticated:
        return False

    if is_admin(user):
        return True

    user_dept_id = _user_department_id(user)
    user_id = getattr(user, 'users_id', None)

    # Generic user ownership for account-level records
    if hasattr(record, 'users_id') and record.users_id is not None and record.users_id == user_id:
        return True

    # Generic department ownership if present
    if hasattr(record, 'departments_id') and record.departments_id is not None:
        return record.departments_id == user_dept_id

    # Generic prepared_by ownership if present
    if hasattr(record, 'prepared_by') and record.prepared_by is not None and record.prepared_by == user_id:
        return True

    if isinstance(record, ConceptPaperForms):
        if record.concept_paper_forms_departments_id and record.concept_paper_forms_departments_id == user_dept_id:
            return True
        if record.concept_paper_forms_prepared_by and record.concept_paper_forms_prepared_by == user_id:
            return True
        return False

    if isinstance(record, Events):
        if DepartmentsEvents.query.filter_by(events_id=record.events_id, departments_id=user_dept_id).first():
            return True
        if record.events_concept_paper_forms_id:
            concept_paper = ConceptPaperForms.query.get(record.events_concept_paper_forms_id)
            if concept_paper and belongs_to_user_or_department(concept_paper, user):
                return True
        return False

    if isinstance(record, Documentation):
        if record.documentation_departments_id and record.documentation_departments_id == user_dept_id:
            return True
        if record.documentation_prepared_by and record.documentation_prepared_by == user_id:
            return True
        if record.documentation_events_id:
            return belongs_to_user_or_department(record.events, user)
        return False

    if isinstance(record, FinancialReports):
        if record.financial_reports_departments_id and record.financial_reports_departments_id == user_dept_id:
            return True
        if record.financial_reports_audited_and_prepared_by and record.financial_reports_audited_and_prepared_by == user_id:
            return True
        if record.financial_reports_events_id:
            return belongs_to_user_or_department(record.events, user)
        return False

    if isinstance(record, MinutesOfTheMeeting):
        if record.minutes_of_the_meeting_departments_id and record.minutes_of_the_meeting_departments_id == user_dept_id:
            return True
        if record.minutes_of_the_meeting_prepared_by and record.minutes_of_the_meeting_prepared_by == user_id:
            return True
        return False

    if isinstance(record, BoardResolutions):
        if record.board_resolutions_departments_id and record.board_resolutions_departments_id == user_dept_id:
            return True
        if record.board_resolutions_prepared_by and record.board_resolutions_prepared_by == user_id:
            return True
        if record.board_resolutions_events_id:
            return belongs_to_user_or_department(record.events, user)
        return False

    return False


def department_or_403(model, id_param='id'):
    """
    Decorator that authorizes access to a record for the current user.

    If the current user is not an admin and the record does not belong to the
    user or their department, the route aborts with 403.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            record_id = kwargs.get(id_param)
            record = model.query.get_or_404(record_id)
            if not belongs_to_user_or_department(record, current_user):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator