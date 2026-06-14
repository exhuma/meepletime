"""Low-level SMTP send helper shared by notification + confirmation mail.

Uses the standard-library synchronous SMTP client with a hard timeout
so it is safe to call from a request thread or the scheduler worker.
Delivery is inert (``is_smtp_configured`` is ``False``) when SMTP host
and from-address are not configured.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import get_settings

# Hard network timeout for SMTP operations, in seconds.
SMTP_TIMEOUT = 5


def is_smtp_configured() -> bool:
    """
    Return whether SMTP delivery is configured.

    :returns: ``True`` when both host and from-address are set.
    """
    settings = get_settings()
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_email(to: str, subject: str, body: str) -> None:
    """
    Send one plain-text email over SMTP.

    :param to: Recipient address.
    :param subject: Message subject.
    :param body: Plain-text message body.
    :raises OSError: On connection or SMTP transport failure.
    """
    settings = get_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message.set_content(body)

    with smtplib.SMTP(
        settings.SMTP_HOST, settings.SMTP_PORT, timeout=SMTP_TIMEOUT
    ) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
