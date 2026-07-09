"""Email abstraction layer."""

from .backends import (
    ConsoleEmailBackend,
    InMemoryEmailBackend,
    MailgunEmailBackend,
    NullEmailBackend,
    SendgridEmailBackend,
    SmtpEmailBackend,
)
from .errors import EmailError
from .protocol import EmailBackend
from .service import get_email
from .tasks import send_email as send_email_task

__all__ = [
    "EmailBackend",
    "EmailError",
    "SmtpEmailBackend",
    "ConsoleEmailBackend",
    "InMemoryEmailBackend",
    "SendgridEmailBackend",
    "MailgunEmailBackend",
    "NullEmailBackend",
    "get_email",
    "send_email_task",
]
