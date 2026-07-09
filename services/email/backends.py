"""Email backend implementations."""

from __future__ import annotations

import json
import sys
from typing import Any, cast

from flask import current_app
from flask_mail import Message

from extensions import mail

from .errors import EmailError
from .protocol import EmailBackend


class SmtpEmailBackend(EmailBackend):
    """Email backend that sends messages via Flask-Mail/SMTP."""

    def send(
        self,
        recipients: list[str],
        subject: str,
        *,
        html: str | None = None,
        body: str | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Send a message using Flask-Mail."""
        recipients_typed = cast(list[str | tuple[str, str]], recipients)
        msg = Message(subject=subject, recipients=recipients_typed, html=html, body=body, sender=sender)
        mail.send(msg)
        return {"sent": True, "backend": "smtp", "recipients": recipients}


class ConsoleEmailBackend(EmailBackend):
    """Email backend that prints messages to stdout for development."""

    def send(
        self,
        recipients: list[str],
        subject: str,
        *,
        html: str | None = None,
        body: str | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Print the email to stdout instead of sending it."""
        default_sender = current_app.config.get("MAIL_DEFAULT_SENDER") if current_app else None
        sender = sender or default_sender or "e-council@example.com"
        print("--- Email ---", file=sys.stdout)
        print(f"From: {sender}", file=sys.stdout)
        print(f"To: {', '.join(recipients)}", file=sys.stdout)
        print(f"Subject: {subject}", file=sys.stdout)
        if body:
            print(f"\n{body}", file=sys.stdout)
        if html:
            print(f"\nHTML:\n{html}", file=sys.stdout)
        print("--- End email ---", file=sys.stdout)
        return {"sent": True, "backend": "console", "recipients": recipients}


class InMemoryEmailBackend(EmailBackend):
    """Email backend that stores messages in memory for testing."""

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def send(
        self,
        recipients: list[str],
        subject: str,
        *,
        html: str | None = None,
        body: str | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Store the message in memory."""
        default_sender = current_app.config.get("MAIL_DEFAULT_SENDER") if current_app else None
        message = {
            "recipients": recipients,
            "subject": subject,
            "html": html,
            "body": body,
            "sender": sender or default_sender,
        }
        self.messages.append(message)
        return {"sent": True, "backend": "memory", "recipients": recipients}

    def clear(self) -> None:
        """Clear all stored messages."""
        self.messages.clear()


class SendgridEmailBackend(EmailBackend):
    """Email backend that sends messages via the SendGrid API."""

    def __init__(self, api_key: str | None = None, from_email: str | None = None) -> None:
        self.api_key = api_key
        self.from_email = from_email

    def send(
        self,
        recipients: list[str],
        subject: str,
        *,
        html: str | None = None,
        body: str | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Send a message via the SendGrid API."""
        import requests

        api_key = self.api_key or (current_app.config.get("SENDGRID_API_KEY") if current_app else None)
        from_email = (
            sender or self.from_email or (current_app.config.get("SENDGRID_FROM_EMAIL") if current_app else None)
        )
        if not api_key:
            raise EmailError("SendGrid API key is not configured")
        if not from_email:
            raise EmailError("SendGrid from email is not configured")

        content = []
        if body:
            content.append({"type": "text/plain", "value": body})
        if html:
            content.append({"type": "text/html", "value": html})

        payload = {
            "personalizations": [{"to": [{"email": email} for email in recipients]}],
            "from": {"email": from_email},
            "subject": subject,
            "content": content,
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30,
        )
        if response.status_code >= 400:
            raise EmailError(f"SendGrid API error: {response.status_code} {response.text}")

        return {"sent": True, "backend": "sendgrid", "recipients": recipients}


class MailgunEmailBackend(EmailBackend):
    """Email backend that sends messages via the Mailgun API."""

    def __init__(
        self,
        api_key: str | None = None,
        domain: str | None = None,
        from_email: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.domain = domain
        self.from_email = from_email

    def send(
        self,
        recipients: list[str],
        subject: str,
        *,
        html: str | None = None,
        body: str | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Send a message via the Mailgun API."""
        import requests

        api_key = self.api_key or (current_app.config.get("MAILGUN_API_KEY") if current_app else None)
        domain = self.domain or (current_app.config.get("MAILGUN_DOMAIN") if current_app else None)
        from_email = (
            sender or self.from_email or (current_app.config.get("MAILGUN_FROM_EMAIL") if current_app else None)
        )
        if not api_key or not domain:
            raise EmailError("Mailgun API key and domain are not configured")
        if not from_email:
            raise EmailError("Mailgun from email is not configured")

        data = {"from": from_email, "to": recipients, "subject": subject}
        if body:
            data["text"] = body
        if html:
            data["html"] = html

        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data=data,
            timeout=30,
        )
        if response.status_code >= 400:
            raise EmailError(f"Mailgun API error: {response.status_code} {response.text}")

        return {"sent": True, "backend": "mailgun", "recipients": recipients}


class NullEmailBackend(EmailBackend):
    """No-op email backend that discards all messages."""

    def send(
        self,
        recipients: list[str],
        subject: str,
        *,
        html: str | None = None,
        body: str | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Discard the message."""
        return {"sent": False, "backend": "null", "recipients": recipients}
