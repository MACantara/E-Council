"""Email backend protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EmailBackend(ABC):
    """Abstract protocol for email backends."""

    @abstractmethod
    def send(
        self,
        recipients: list[str],
        subject: str,
        *,
        html: str | None = None,
        body: str | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Send a plain email message.

        Args:
            recipients: List of recipient email addresses.
            subject: Email subject.
            html: Optional HTML body.
            body: Optional plain text body.
            sender: Optional sender address.

        Returns:
            A result dict with backend-specific details.
        """
        raise NotImplementedError

    def send_template(
        self,
        recipients: list[str],
        subject: str,
        *,
        html_template: str | None = None,
        text_template: str | None = None,
        context: dict[str, Any] | None = None,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Render templates and send the resulting email.

        Args:
            recipients: List of recipient email addresses.
            subject: Email subject.
            html_template: Optional HTML template path.
            text_template: Optional plain text template path.
            context: Variables to render in the templates.
            sender: Optional sender address.

        Returns:
            A result dict with backend-specific details.
        """
        from flask import render_template

        context = context or {}
        html = render_template(html_template, **context) if html_template else None
        body = render_template(text_template, **context) if text_template else None
        return self.send(recipients, subject, html=html, body=body, sender=sender)

    def send_batch(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Send a batch of messages.

        Args:
            messages: List of message dicts accepted by send.

        Returns:
            A list of result dicts.
        """
        results = []
        for message in messages:
            results.append(
                self.send(
                    message["recipients"],
                    message["subject"],
                    html=message.get("html"),
                    body=message.get("body"),
                    sender=message.get("sender"),
                )
            )
        return results
