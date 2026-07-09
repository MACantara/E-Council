"""Celery task for sending emails through the configured backend."""

from __future__ import annotations

from typing import Any

from tasks import celery_app

from .service import get_email


@celery_app.task(name="tasks.send_email")
def send_email(recipients: list[str], subject: str, html: str, body: str, sender: str | None = None) -> dict[str, Any]:
    """Send an email using the configured email backend.

    Args:
        recipients: List of recipient email addresses.
        subject: Email subject.
        html: HTML body.
        body: Plain text body.
        sender: Optional sender address.

    Returns:
        Backend result dict.
    """
    backend = get_email()
    return backend.send(recipients, subject, html=html, body=body, sender=sender)
