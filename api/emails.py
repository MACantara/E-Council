"""Email helpers for the FastAPI API that reuse the abstracted email service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from api.settings import API_BASE_URL, FRONTEND_URL, SECRET_KEY
from models import EmailVerification, PasswordReset
from services.email import EmailBackend

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_serializer() -> URLSafeTimedSerializer:
    """Return a URLSafeTimedSerializer for email tokens."""
    return URLSafeTimedSerializer(SECRET_KEY)


def _now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.utcnow()


def send_verification_email(
    db: Session,
    backend: EmailBackend,
    user,
) -> None:
    """Send an email verification link to a new user."""
    s = get_serializer()
    token = s.dumps(user.users_email, salt="email-confirm")
    link = f"{FRONTEND_URL}/verify-email?token={token}"
    subject = "New Account Email Verification"
    recipients = [user.users_email]
    html = (
        f"<html><body><p>Please verify your email by clicking "
        f"<a href='{link}'>this link</a>.</p></body></html>"
    )
    body = f"Please verify your email by visiting: {link}"

    backend.send(recipients, subject, html=html, body=body)

    email_verification = EmailVerification(
        email_verification_users_id=user.users_id,
        email_verification_token=token,
        email_verification_new_email=user.users_email,
    )
    db.add(email_verification)
    db.commit()


def verify_email_token(db: Session, token: str) -> None:
    """Verify an email token and activate the user's account."""
    s = get_serializer()
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)
    except SignatureExpired as exc:
        raise ValueError("The email confirmation link has expired.") from exc
    except BadSignature as exc:
        raise ValueError("The email confirmation link is invalid.") from exc

    target = db.query(EmailVerification).filter_by(email_verification_token=token).first()
    if target is None or target.user.users_email != email:
        raise ValueError("The email confirmation link is invalid.")

    target.user.users_email_verified = 1
    db.delete(target)
    db.commit()


def send_password_reset_email(
    db: Session,
    backend: EmailBackend,
    user,
) -> tuple[str, str]:
    """Send a password reset email and return the selector and token."""
    import os

    selector = os.urandom(16).hex()
    token = os.urandom(32).hex()
    expires = _now() + timedelta(hours=1)

    link = f"{FRONTEND_URL}/reset-password?selector={selector}&token={token}"
    subject = "Password Reset Request"
    recipients = [user.users_email]
    html = (
        f"<html><body><p>You requested a password reset. Click "
        f"<a href='{link}'>this link</a> to reset your password.</p></body></html>"
    )
    body = f"Reset your password by visiting: {link}"

    backend.send(recipients, subject, html=html, body=body)

    password_reset = PasswordReset(
        password_reset_users_id=user.users_id,
        password_reset_selector=selector,
        password_reset_token=token,
        password_reset_expires=expires,
    )
    db.add(password_reset)
    db.commit()

    return selector, token


def reset_password(db: Session, selector: str, token: str, new_password: str) -> None:
    """Reset a password using a selector and token."""
    password_reset = db.query(PasswordReset).filter_by(password_reset_selector=selector).first()
    if password_reset is None:
        raise ValueError("The password reset link is invalid or has expired.")

    if password_reset.password_reset_token != token or password_reset.password_reset_expires < _now():
        raise ValueError("The password reset link is invalid or has expired.")

    user = password_reset.user
    user.set_password(new_password)
    db.delete(password_reset)
    db.commit()


def send_new_email_verification(
    db: Session,
    backend: EmailBackend,
    user,
    new_email: str,
) -> str:
    """Send a verification email for a new email address and return the token."""
    s = get_serializer()
    token = s.dumps(new_email, salt="email-change")
    link = f"{API_BASE_URL}/api/v1/account/confirm-new-email/{token}"
    subject = "Email Change Verification"
    recipients = [new_email]
    html = (
        f"<html><body><p>Confirm your new email by clicking "
        f"<a href='{link}'>this link</a>.</p></body></html>"
    )
    body = f"Confirm your new email by visiting: {link}"

    backend.send(recipients, subject, html=html, body=body)

    email_verification = EmailVerification(
        email_verification_users_id=user.users_id,
        email_verification_token=token,
        email_verification_new_email=new_email,
    )
    db.add(email_verification)
    db.commit()

    return token


def confirm_new_email(db: Session, token: str) -> str:
    """Confirm a new email and return the new email address."""
    s = get_serializer()
    try:
        new_email = s.loads(token, salt="email-change", max_age=3600)
    except SignatureExpired as exc:
        raise ValueError("The email confirmation link has expired.") from exc
    except BadSignature as exc:
        raise ValueError("The email confirmation link is invalid.") from exc

    email_verification = db.query(EmailVerification).filter_by(email_verification_token=token).first()
    if email_verification is None or email_verification.email_verification_new_email != new_email:
        raise ValueError("The email confirmation link is invalid.")

    user = email_verification.user
    old_email = user.users_email
    user.users_email = new_email
    db.delete(email_verification)
    db.commit()
    return old_email


def send_password_change_notification(backend: EmailBackend, users_email: str) -> None:
    """Send a notification when the user's password is changed."""
    subject = "Password Change Notification"
    html = "<html><body><p>Your password has been changed.</p></body></html>"
    body = "Your password has been changed."
    backend.send([users_email], subject, html=html, body=body)


def send_email_change_notification(
    backend: EmailBackend,
    users_old_email: str,
    users_new_email: str,
) -> None:
    """Send a notification to the old email address when the email is changed."""
    subject = "Email Change Notification"
    html = (
        f"<html><body><p>Your email has been changed from {users_old_email} "
        f"to {users_new_email}.</p></body></html>"
    )
    body = f"Your email has been changed from {users_old_email} to {users_new_email}."
    backend.send([users_old_email], subject, html=html, body=body)


def send_email_change_confirmation(
    backend: EmailBackend,
    users_new_email: str,
) -> None:
    """Send a confirmation to the new email address."""
    subject = "Email Change Confirmation"
    html = "<html><body><p>Your email has been updated successfully.</p></body></html>"
    body = "Your email has been updated successfully."
    backend.send([users_new_email], subject, html=html, body=body)


def send_account_deletion_notification(backend: EmailBackend, users_email: str) -> None:
    """Send a notification when the user's account is deleted."""
    subject = "Account Deletion Notification"
    html = "<html><body><p>Your account has been deleted.</p></body></html>"
    body = "Your account has been deleted."
    backend.send([users_email], subject, html=html, body=body)
