"""Service layer for notification-email confirmation.

Drives the set / retry / confirm / clear lifecycle of a user's
notification email. A confirmed address lands on
``UserNotificationSettings.notification_email``; the transient pending
state lives in :class:`EmailConfirmation` (at most one row per user).
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.notification_settings import EmailConfirmation
from app.services.email import send_email
from app.services.notification_settings import get_or_create_settings

# Entropy for the opaque confirmation token, in bytes.
_TOKEN_BYTES = 32
# Minimum seconds between confirmation sends (retry throttle).
RESEND_COOLDOWN_SECONDS = 60


class ConfirmStatus(StrEnum):
    """Outcome of a confirmation-code submission."""

    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    INVALID = "invalid"


class NoPendingConfirmation(Exception):
    """Raised when a resend is requested but nothing is pending."""


class ResendTooSoon(Exception):
    """Raised when a resend is requested inside the cooldown window."""


def _now() -> datetime:
    """:returns: The current UTC time."""
    return datetime.now(UTC)


def _ttl() -> timedelta:
    """:returns: The configured confirmation validity window."""
    return timedelta(hours=get_settings().EMAIL_CONFIRMATION_TTL_HOURS)


def get_pending(db: Session, user_id: uuid.UUID) -> EmailConfirmation | None:
    """
    Return the user's pending confirmation row, if any.

    :param db: Active database session.
    :param user_id: The owning user.
    :returns: The pending row, or ``None``.
    """
    return db.execute(
        select(EmailConfirmation).where(EmailConfirmation.user_id == user_id)
    ).scalar_one_or_none()


def _confirmation_body(token: str) -> str:
    """
    Return the plain-text confirmation email body.

    :param token: The opaque confirmation token to embed.
    :returns: The message body including the confirmation link.
    """
    base = get_settings().APP_BASE_URL.rstrip("/")
    hours = get_settings().EMAIL_CONFIRMATION_TTL_HOURS
    link = f"{base}/confirm-email?code={token}"
    return (
        "Confirm this address to receive MeepleTime notifications "
        "here.\n\n"
        f"{link}\n\n"
        f"This link is valid for {hours} hours. If you did not request "
        "this, you can ignore this email.\n"
    )


def _send(row: EmailConfirmation) -> None:
    """
    Send the confirmation email for a pending row.

    :param row: The pending confirmation row.
    :raises OSError: On SMTP transport failure.
    """
    send_email(
        row.pending_email,
        "Confirm your MeepleTime notification email",
        _confirmation_body(row.token),
    )


def start_confirmation(
    db: Session, user_id: uuid.UUID, email: str
) -> EmailConfirmation:
    """
    Begin confirming a new notification address (new token, fresh TTL).

    Replaces any existing pending row for the user. Does **not** touch
    the currently confirmed address, which keeps receiving mail until
    the new one is confirmed.

    :param db: Active database session.
    :param user_id: The requesting user.
    :param email: The address to confirm.
    :returns: The persisted pending row.
    :raises OSError: On SMTP transport failure.
    """
    row = get_pending(db, user_id)
    if row is None:
        row = EmailConfirmation(user_id=user_id)
        db.add(row)
    row.pending_email = email
    row.token = secrets.token_urlsafe(_TOKEN_BYTES)
    row.expires_at = _now() + _ttl()
    row.created_at = _now()
    db.flush()
    _send(row)
    db.commit()
    db.refresh(row)
    return row


def resend_confirmation(db: Session, user_id: uuid.UUID) -> EmailConfirmation:
    """
    Resend the *same* pending link with a refreshed deadline.

    :param db: Active database session.
    :param user_id: The requesting user.
    :returns: The refreshed pending row.
    :raises NoPendingConfirmation: When nothing is pending.
    :raises ResendTooSoon: When inside the cooldown window.
    :raises OSError: On SMTP transport failure.
    """
    row = get_pending(db, user_id)
    if row is None:
        raise NoPendingConfirmation
    last_send = row.expires_at - _ttl()
    if (_now() - last_send).total_seconds() < RESEND_COOLDOWN_SECONDS:
        raise ResendTooSoon
    row.expires_at = _now() + _ttl()
    db.flush()
    _send(row)
    db.commit()
    db.refresh(row)
    return row


def confirm(db: Session, code: str) -> ConfirmStatus:
    """
    Confirm a code: promote the pending address and consume the row.

    :param db: Active database session.
    :param code: The token from the confirmation link.
    :returns: The confirmation outcome.
    """
    row = db.execute(
        select(EmailConfirmation).where(EmailConfirmation.token == code)
    ).scalar_one_or_none()
    if row is None:
        return ConfirmStatus.INVALID
    if row.expires_at <= _now():
        return ConfirmStatus.EXPIRED
    settings = get_or_create_settings(db, row.user_id)
    settings.notification_email = row.pending_email
    db.delete(row)
    db.commit()
    return ConfirmStatus.CONFIRMED


def clear_email(db: Session, user_id: uuid.UUID) -> None:
    """
    Clear the confirmed address and any pending confirmation.

    :param db: Active database session.
    :param user_id: The requesting user.
    """
    settings = get_or_create_settings(db, user_id)
    settings.notification_email = None
    row = get_pending(db, user_id)
    if row is not None:
        db.delete(row)
    db.commit()
