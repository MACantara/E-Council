"""Email service factory."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flask import current_app, has_app_context

from config import EmailConfig

from .backends import (
    ConsoleEmailBackend,
    InMemoryEmailBackend,
    MailgunEmailBackend,
    NullEmailBackend,
    SendgridEmailBackend,
    SmtpEmailBackend,
)
from .errors import EmailError

if TYPE_CHECKING:
    from flask import Flask

    from .protocol import EmailBackend


PROVIDER_MAP: dict[str, type[EmailBackend]] = {
    "smtp": SmtpEmailBackend,
    "console": ConsoleEmailBackend,
    "memory": InMemoryEmailBackend,
    "inmemory": InMemoryEmailBackend,
    "sendgrid": SendgridEmailBackend,
    "mailgun": MailgunEmailBackend,
    "null": NullEmailBackend,
}


def get_email(app: Flask | None = None) -> EmailBackend:
    """Return the configured email backend.

    Args:
        app: Optional Flask app. Defaults to current_app or the environment
            configuration when running outside a Flask app context.

    Returns:
        An EmailBackend instance.
    """
    if app is None:
        if has_app_context():
            app = current_app
        else:
            provider = os.environ.get("EMAIL_PROVIDER") or EmailConfig.EMAIL_PROVIDER
            backend_class = PROVIDER_MAP.get(provider)
            if backend_class is None:
                raise EmailError(f"Unknown email provider: {provider}")
            return backend_class()

    if "EMAIL_BACKEND" in app.config:
        return app.config["EMAIL_BACKEND"]

    provider = app.config.get("EMAIL_PROVIDER") or os.environ.get("EMAIL_PROVIDER") or EmailConfig.EMAIL_PROVIDER
    backend_class = PROVIDER_MAP.get(provider)
    if backend_class is None:
        raise EmailError(f"Unknown email provider: {provider}")

    return backend_class()
