"""Low-level SMTP send helper shared by notification + confirmation mail.

Uses the standard-library synchronous SMTP client with a hard timeout
so it is safe to call from a request thread or the scheduler worker.
Delivery is inert (``is_smtp_configured`` is ``False``) when SMTP host
and from-address are not configured.
"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from app.config import get_settings

# Hard network timeout for SMTP operations, in seconds.
SMTP_TIMEOUT = 5


context = ssl.create_default_context()


def is_smtp_configured() -> bool:
    """
    Return whether SMTP delivery is configured.

    :returns: ``True`` when both host and from-address are set.
    """
    settings = get_settings()
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


# Fixed Content-ID for the inline hero image referenced as
# ``src="cid:hero"`` by the HTML templates.
HERO_CID = "hero"


def _deliver(message: EmailMessage) -> None:
    """
    Open an SMTP connection and send a prepared message.

    :param message: A fully populated :class:`EmailMessage`.
    :raises OSError: On connection or SMTP transport failure.
    """
    settings = get_settings()
    with smtplib.SMTP_SSL(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=SMTP_TIMEOUT,
        context=context,
    ) as smtp:
        smtp.ehlo()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def _new_message(to: str, subject: str) -> EmailMessage:
    """
    Build an :class:`EmailMessage` with the common headers set.

    :param to: Recipient address.
    :param subject: Message subject.
    :returns: A message with ``Subject``/``From``/``To`` populated.
    """
    settings = get_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    return message


def send_email(to: str, subject: str, body: str) -> None:
    """
    Send one plain-text email over SMTP.

    :param to: Recipient address.
    :param subject: Message subject.
    :param body: Plain-text message body.
    :raises OSError: On connection or SMTP transport failure.
    """
    message = _new_message(to, subject)
    message.set_content(body)
    _deliver(message)


def send_email_html(
    to: str,
    subject: str,
    text: str,
    html: str,
    inline_image: tuple[bytes, str] | None = None,
) -> None:
    """
    Send a multipart email with plain-text and HTML alternatives.

    The plain-text part is always set first so every client has a
    readable fallback. When ``inline_image`` is given, the hero image
    is embedded via ``Content-ID`` (the structure is promoted to
    ``multipart/related``) and referenced from the HTML as
    ``src="cid:hero"``.

    :param to: Recipient address.
    :param subject: Message subject.
    :param text: Plain-text alternative body.
    :param html: HTML alternative body.
    :param inline_image: Optional ``(data, content_type)`` hero image.
    :raises OSError: On connection or SMTP transport failure.
    """
    message = _new_message(to, subject)
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    if inline_image is not None:
        data, content_type = inline_image
        maintype, _, subtype = content_type.partition("/")
        message.get_payload()[1].add_related(
            data,
            maintype=maintype or "image",
            subtype=subtype or "octet-stream",
            cid=f"<{HERO_CID}>",
        )
    _deliver(message)
