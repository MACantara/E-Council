"""
Email utility functions for E-Council.
Handles all email sending functionality including verification, password reset, and notifications.
"""

import os
from datetime import datetime, timedelta

from flask import flash, render_template, url_for
from flask_login import current_user
from flask_mail import Message

from repositories import repo
from tasks import send_email as send_email_task

# Note: These imports will need to be adjusted based on final model structure
# For now, importing from app.py (will be refactored later)
# from models.user import Users, EmailVerification, PasswordReset
# from models.department import Departments
# from models.event import EventInvitations

# Temporary imports from app.py (will be refactored later)
# Using lazy imports to avoid circular dependency with app.py


def send_verification_email(users_email: str) -> None:
    """
    Send email verification link to a new user.

    Args:
        users_email: Email address of the user to verify
    """
    from extensions import get_serializer
    from models import EmailVerification, Users

    s = get_serializer()

    user = Users.query.filter_by(users_email=users_email).first_or_404()
    token = s.dumps(users_email, salt="email-confirm")
    link = url_for("auth.confirm_email", token=token, _external=True)
    msg = Message("New Account Email Verification", recipients=[users_email])
    msg.html = render_template("email/verification_email.html", link=link)
    msg.body = render_template("email/verification_email.txt", link=link)

    # Check for existing email verification records
    existing_verification = EmailVerification.query.filter_by(
        email_verification_users_id=user.users_id, email_verification_new_email=users_email
    ).first()

    if existing_verification:
        flash("A verification email has already been sent to this email address. Please check your email.", "error")
        return

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))

    # Track email verification in the database
    email_verification = EmailVerification(
        email_verification_users_id=user.users_id,
        email_verification_token=token,
        email_verification_new_email=users_email,
    )
    repo.add(email_verification)
    repo.commit()


def send_reset_password_email(users_email: str) -> None:
    """
    Send password reset link to a user.

    Args:
        users_email: Email address of the user requesting password reset
    """
    from models import PasswordReset, Users

    user = Users.query.filter_by(users_email=users_email).first_or_404()
    selector = os.urandom(16).hex()
    token = os.urandom(32).hex()
    expires = datetime.utcnow() + timedelta(hours=1)

    # Create the password reset link
    link = url_for("auth.reset_password", selector=selector, token=token, _external=True)
    msg = Message("Password Reset Request", recipients=[users_email])
    msg.html = render_template("email/reset_password_email.html", link=link)
    msg.body = render_template("email/reset_password_email.txt", link=link)

    # Check for existing password reset records
    existing_reset = PasswordReset.query.filter_by(password_reset_users_id=user.users_id).first()

    if existing_reset:
        flash("A password reset email has already been sent to this email address. Please check your email.", "error")
        return

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))

    # Track password reset in the database
    password_reset = PasswordReset(
        password_reset_users_id=user.users_id,
        password_reset_selector=selector,
        password_reset_token=token,
        password_reset_expires=expires,
    )
    repo.add(password_reset)
    repo.commit()


def send_password_change_notification_email(users_email: str) -> None:
    """
    Send notification when user password is changed.

    Args:
        users_email: Email address of the user
    """

    msg = Message("Password Change Notification", recipients=[users_email])
    msg.html = render_template("email/password_change_notification_email.html")
    msg.body = render_template("email/password_change_notification_email.txt")

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))


def send_email_change_notification(users_old_email: str, users_new_email: str) -> None:
    """
    Send notification when user email is changed.

    Args:
        users_old_email: Old email address of the user
        users_new_email: New email address of the user
    """

    msg = Message("Email Change Notification", recipients=[users_old_email])
    msg.html = render_template(
        "email/email_change_notification_email.html", old_email=users_old_email, new_email=users_new_email
    )
    msg.body = render_template(
        "email/email_change_notification_email.txt", old_email=users_old_email, new_email=users_new_email
    )

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))


def send_email_change_confirmation(users_old_email: str, users_new_email: str) -> None:
    """
    Send confirmation when user email is changed.

    Args:
        users_old_email: Old email address of the user
        users_new_email: New email address of the user
    """

    msg = Message("Email Change Confirmation", recipients=[users_new_email])
    msg.html = render_template(
        "email/email_change_confirmation_email.html", old_email=users_old_email, new_email=users_new_email
    )
    msg.body = render_template("email/email_change_confirmation_email.txt", new_email=users_new_email)

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))


def send_new_email_verification(users_new_email: str) -> None:
    """
    Send verification link for new email address.

    Args:
        users_new_email: New email address to verify
    """
    from extensions import get_serializer
    from models import EmailVerification

    s = get_serializer()

    user = current_user
    token = s.dumps(users_new_email, salt="email-change")
    link = url_for("account.confirm_new_email", token=token, _external=True)
    msg = Message("Email Change Verification", recipients=[users_new_email])
    msg.html = render_template("email/new_email_verification_email.html", link=link)
    msg.body = render_template("email/new_email_verification_email.txt", link=link)

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))

    # Track email verification in the database
    email_verification = EmailVerification(
        email_verification_users_id=user.users_id,
        email_verification_token=token,
        email_verification_new_email=users_new_email,
    )
    repo.add(email_verification)
    repo.commit()


def send_account_deletion_notification_email(users_email: str) -> None:
    """
    Send notification when user account is deleted.

    Args:
        users_email: Email address of the user
    """

    msg = Message("Account Deletion Notification", recipients=[users_email])
    msg.html = render_template("email/account_deletion_notification_email.html")
    msg.body = render_template("email/account_deletion_notification_email.txt")

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))


def send_invite_email(users_email: str, event_name: str, event_id: int) -> None:
    """
    Send invitation email to manage an event.

    Args:
        users_email: Email address of the invitee
        event_name: Name of the event
        event_id: ID of the event
    """
    from extensions import get_serializer
    from models import Departments, EventInvitations, Users

    s = get_serializer()

    # Get the current user's details
    inviter = Users.query.get(current_user.users_id)
    inviter_first_name = inviter.users_first_name
    inviter_last_name = inviter.users_last_name
    inviter_department = Departments.query.get(inviter.users_departments_id).departments_name

    token = s.dumps(users_email, salt="invite-user")
    accept_link = url_for("events.accept_invite", token=token, _external=True)
    reject_link = url_for("events.reject_invite", token=token, _external=True)
    msg = Message("Invitation to Manage Event", recipients=[users_email])
    msg.html = render_template(
        "email/invite_email.html",
        event_name=event_name,
        inviter_first_name=inviter_first_name,
        inviter_last_name=inviter_last_name,
        inviter_department=inviter_department,
        accept_link=accept_link,
        reject_link=reject_link,
    )
    msg.body = render_template(
        "email/invite_email.txt",
        event_name=event_name,
        inviter_first_name=inviter_first_name,
        inviter_last_name=inviter_last_name,
        inviter_department=inviter_department,
        accept_link=accept_link,
        reject_link=reject_link,
    )

    send_email_task.apply_async(args=(msg.recipients, msg.subject, msg.html, msg.body, msg.sender))

    # Store the invitation details in the event_invitations table
    event_invitation = EventInvitations(
        event_invitations_events_id=event_id, event_invitations_email=users_email, event_invitations_token=token
    )
    repo.add(event_invitation)
    repo.commit()
