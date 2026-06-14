"""Channel-agnostic dispatch for notification events.

``dispatch_event`` resolves the eligible recipients for an event and
fans the event out across every registered channel, recording one
:class:`NotificationChannelAttempt` per send and marking per-user
deliveries as delivered when at least one channel succeeds.

This runs inside the synchronous APScheduler worker thread, so every
channel ``send`` must use a hard network timeout and is wrapped here so
one failing target can never abort the others or the job.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import (
    NotificationChannelAttempt,
    NotificationDelivery,
    NotificationEvent,
)
from app.models.notification_settings import UserNotificationSettings
from app.models.user import User
from app.services.notifications.channels import (
    NotificationChannel,
    Recipient,
    iter_channels,
)
from app.services.notifications.context import (
    EventContext,
    build_event_context,
)

logger = logging.getLogger(__name__)


def _default_settings(user_id: uuid.UUID) -> UserNotificationSettings:
    """
    Return transient default settings for a user with no row yet.

    :param user_id: The user the defaults apply to.
    :returns: An unsaved settings object with channel defaults.
    """
    return UserNotificationSettings(
        user_id=user_id,
        email_enabled=True,
        webpush_enabled=False,
        telegram_dm_enabled=False,
    )


def _load_recipients(event: NotificationEvent, db: Session) -> list[Recipient]:
    """
    Load the event's delivery rows joined with user + settings.

    Muted members never receive a delivery row (filtered upstream in
    ``evaluate_and_notify``), so every row here is an eligible
    recipient.

    :param event: The event being dispatched.
    :param db: Active database session.
    :returns: Eligible recipients with resolved settings.
    """
    rows = db.execute(
        select(NotificationDelivery, User)
        .join(User, User.id == NotificationDelivery.user_id)
        .where(NotificationDelivery.notification_event_id == event.id)
    ).all()

    recipients: list[Recipient] = []
    for delivery, user in rows:
        settings = db.execute(
            select(UserNotificationSettings).where(
                UserNotificationSettings.user_id == user.id
            )
        ).scalar_one_or_none()
        if settings is None:
            settings = _default_settings(user.id)
        recipients.append(
            Recipient(
                user_id=user.id,
                delivery_id=delivery.id,
                email=settings.notification_email or user.email,
                settings=settings,
            )
        )
    return recipients


def dispatch_event(
    event: NotificationEvent,
    db: Session,
    channels: list[NotificationChannel] | None = None,
) -> None:
    """
    Deliver one event across all registered channels (best-effort).

    :param event: The persisted event to deliver.
    :param db: Active database session (committed here, not closed).
    :param channels: Explicit channel list (used by tests); defaults
        to the registered channels.
    """
    if channels is None:
        channels = iter_channels()
    if not channels:
        return

    ctx = build_event_context(event, db)
    recipients = _load_recipients(event, db)
    delivered: set[uuid.UUID] = set()

    for channel in channels:
        try:
            targets = channel.collect_targets(ctx, recipients, db)
        except Exception as exc:
            logger.warning(
                "collect_targets failed for channel %s: %s",
                channel.key,
                exc,
            )
            continue
        for target in targets:
            _send_one(channel, target, ctx, event, db, delivered)

    if delivered:
        _mark_delivered(delivered, db)

    db.commit()


def _send_one(
    channel: NotificationChannel,
    target,
    ctx: EventContext,
    event: NotificationEvent,
    db: Session,
    delivered: set[uuid.UUID],
) -> None:
    """
    Send one target and record the attempt outcome.

    :param channel: The channel performing the send.
    :param target: The target to deliver to.
    :param ctx: The event context.
    :param event: The originating event.
    :param db: Active database session.
    :param delivered: Set of delivery ids with a success so far.
    """
    status = "sent"
    error: str | None = None
    try:
        channel.send(target, ctx, db)
    except Exception as exc:
        status = "failed"
        error = str(exc)[:512]
        logger.warning("channel %s send failed: %s", channel.key, exc)

    db.add(
        NotificationChannelAttempt(
            notification_event_id=event.id,
            delivery_id=target.delivery_id,
            user_id=target.user_id,
            channel=channel.key,
            status=status,
            error=error,
        )
    )
    if status == "sent" and target.delivery_id is not None:
        delivered.add(target.delivery_id)


def _mark_delivered(delivery_ids: set[uuid.UUID], db: Session) -> None:
    """
    Stamp ``delivered_at`` on deliveries with a successful send.

    :param delivery_ids: Deliveries that had at least one success.
    :param db: Active database session.
    """
    now = datetime.now(UTC)
    deliveries = (
        db.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.id.in_(delivery_ids)
            )
        )
        .scalars()
        .all()
    )
    for delivery in deliveries:
        if delivery.delivered_at is None:
            delivery.delivered_at = now
