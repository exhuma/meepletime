"""Channel-agnostic dispatch for notification events.

``dispatch_batch`` resolves the eligible recipients for a batch of
events (all for one circle) and fans a single aggregated message out
across every registered channel, recording one
:class:`NotificationChannelAttempt` per delivery and marking per-user
deliveries as delivered when at least one channel succeeds.
``dispatch_event`` is a thin batch-of-one wrapper.

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
    build_batch_context,
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


def _resolve_settings(
    user_id: uuid.UUID, db: Session
) -> UserNotificationSettings:
    """
    Return a user's notification settings or transient defaults.

    :param user_id: The user whose settings to resolve.
    :param db: Active database session.
    :returns: The persisted settings, or defaults when absent.
    """
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user_id
        )
    ).scalar_one_or_none()
    return settings if settings is not None else _default_settings(user_id)


def _load_recipients(event: NotificationEvent, db: Session) -> list[Recipient]:
    """
    Load the event's delivery rows joined with user + settings.

    Muted members never receive a delivery row (filtered upstream in
    the evaluation step), so every row here is an eligible recipient.

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
        settings = _resolve_settings(user.id, db)
        recipients.append(
            Recipient(
                user_id=user.id,
                delivery_id=delivery.id,
                email=settings.notification_email or user.email,
                settings=settings,
            )
        )
    return recipients


def _load_batch_recipients(
    event_ids: list[uuid.UUID], db: Session
) -> tuple[list[Recipient], dict[uuid.UUID, list[NotificationDelivery]]]:
    """
    Load distinct recipients and their deliveries across a batch.

    Every non-muted member has one delivery row per event in the batch.
    A recipient is built once per distinct user; the returned map lets
    the dispatcher mark all of a user's deliveries delivered from a
    single aggregated send.

    :param event_ids: Ids of the events in the batch.
    :param db: Active database session.
    :returns: A ``(recipients, deliveries_by_user)`` pair.
    """
    rows = db.execute(
        select(NotificationDelivery, User)
        .join(User, User.id == NotificationDelivery.user_id)
        .where(NotificationDelivery.notification_event_id.in_(event_ids))
    ).all()

    deliveries_by_user: dict[uuid.UUID, list[NotificationDelivery]] = {}
    users: dict[uuid.UUID, User] = {}
    for delivery, user in rows:
        deliveries_by_user.setdefault(user.id, []).append(delivery)
        users[user.id] = user

    recipients: list[Recipient] = []
    for user_id, deliveries in deliveries_by_user.items():
        settings = _resolve_settings(user_id, db)
        recipients.append(
            Recipient(
                user_id=user_id,
                delivery_id=deliveries[0].id,
                email=settings.notification_email or users[user_id].email,
                settings=settings,
            )
        )
    return recipients, deliveries_by_user


def dispatch_event(
    event: NotificationEvent,
    db: Session,
    channels: list[NotificationChannel] | None = None,
) -> None:
    """
    Deliver a single event (batch of one).

    :param event: The persisted event to deliver.
    :param db: Active database session (committed here, not closed).
    :param channels: Explicit channel list (used by tests); defaults
        to the registered channels.
    """
    dispatch_batch([event], db, channels)


def dispatch_batch(
    events: list[NotificationEvent],
    db: Session,
    channels: list[NotificationChannel] | None = None,
) -> None:
    """
    Deliver a batch of events as one aggregated message (best-effort).

    All events must belong to the same circle. A single message is
    built for the whole batch and sent once per target on each channel;
    every per-user delivery in the batch is audited and marked.

    :param events: The persisted events to deliver (same circle).
    :param db: Active database session (committed here, not closed).
    :param channels: Explicit channel list (used by tests); defaults
        to the registered channels.
    """
    if not events:
        return
    if channels is None:
        channels = iter_channels()
    if not channels:
        return

    ctx = build_batch_context(events, db)
    event_ids = [event.id for event in events]
    primary_event_id = ctx.event_id
    recipients, deliveries_by_user = _load_batch_recipients(event_ids, db)
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
            _deliver_target(
                channel,
                target,
                ctx,
                primary_event_id,
                deliveries_by_user,
                db,
                delivered,
            )

    if delivered:
        _mark_delivered(delivered, db)

    db.commit()


def _deliver_target(
    channel: NotificationChannel,
    target,
    ctx: EventContext,
    primary_event_id: uuid.UUID,
    deliveries_by_user: dict[uuid.UUID, list[NotificationDelivery]],
    db: Session,
    delivered: set[uuid.UUID],
) -> None:
    """
    Send one target and record the attempt against its deliveries.

    For a per-user target the single physical send is audited against
    each of that user's deliveries in the batch (preserving the
    one-attempt-per-delivery invariant). Broadcast targets (no user)
    record a single attempt against the primary event.

    :param channel: The channel performing the send.
    :param target: The target to deliver to.
    :param ctx: The aggregated event context.
    :param primary_event_id: Event id used for broadcast attempts.
    :param deliveries_by_user: Batch deliveries grouped by user id.
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

    user_deliveries = (
        deliveries_by_user.get(target.user_id, [])
        if target.user_id is not None
        else []
    )
    if user_deliveries:
        for delivery in user_deliveries:
            db.add(
                NotificationChannelAttempt(
                    notification_event_id=delivery.notification_event_id,
                    delivery_id=delivery.id,
                    user_id=target.user_id,
                    channel=channel.key,
                    status=status,
                    error=error,
                )
            )
            if status == "sent":
                delivered.add(delivery.id)
    else:
        db.add(
            NotificationChannelAttempt(
                notification_event_id=primary_event_id,
                delivery_id=None,
                user_id=target.user_id,
                channel=channel.key,
                status=status,
                error=error,
            )
        )


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
