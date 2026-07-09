"""
Utility functions and helpers for E-Council.
"""

from .auth import load_user, setup_login_manager, unauthorized
from .email import (
    send_account_deletion_notification_email,
    send_email_change_confirmation,
    send_email_change_notification,
    send_invite_email,
    send_new_email_verification,
    send_password_change_notification_email,
    send_reset_password_email,
    send_verification_email,
)
from .error_handlers import handle_cloudinary_error, register_error_handlers
from .filters import (
    has_documentations,
    has_events,
    has_financial_reports,
    has_meetings,
    has_papers,
    has_resolutions,
    register_filters,
    truncate_text,
)
from .helpers import allowed_image_file, get_concept_papers, get_distinct_academic_years, safe_decimal_conversion
from .processing import process_evaluation_forms, process_tally_items

__all__ = [
    # Email functions
    "send_verification_email",
    "send_reset_password_email",
    "send_password_change_notification_email",
    "send_email_change_notification",
    "send_email_change_confirmation",
    "send_new_email_verification",
    "send_account_deletion_notification_email",
    "send_invite_email",
    # Helper functions
    "get_distinct_academic_years",
    "get_concept_papers",
    "safe_decimal_conversion",
    "allowed_image_file",
    # Processing functions
    "process_tally_items",
    "process_evaluation_forms",
    # Auth functions
    "load_user",
    "unauthorized",
    "setup_login_manager",
    # Filter functions
    "truncate_text",
    "has_events",
    "has_resolutions",
    "has_meetings",
    "has_financial_reports",
    "has_papers",
    "has_documentations",
    "register_filters",
    # Error handlers
    "handle_cloudinary_error",
    "register_error_handlers",
]
