"""Derived-state evaluation that emits notification events.

Computes viability for each changed ``(circle_id, local_date)``, applies
the anti-storm suppression rules (§12.3), writes one event plus a
delivery row per non-muted member, then hands the whole batch to the
dispatcher so a single aggregated summary is delivered (§12.1).
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.circle import Circle
from app.models.membership import CircleMembership
from app.models.notification import (
    NotificationDelivery,
    NotificationEvent,
)
from app.services.notifications.dispatch import dispatch_batch
from app.services.viability import compute_viability

logger = logging.getLogger(__name__)


def _evaluate_one(
    circle: Circle,
    local_date: date,
    db: Session,
    anti_storm_window: int,
) -> NotificationEvent | None:
    """
    Evaluate one day and stage an event + deliveries if warranted.

    The event and its delivery rows are added to the session (and the
    event flushed for its id) but not committed — the caller commits
    the whole batch atomically.

    :param circle: The circle being evaluated.
    :param local_date: The circle-local date to evaluate.
    :param db: Active database session.
    :param anti_storm_window: Suppression window in seconds for
        duplicate events of the same type on the same day.
    :returns: The staged event, or ``None`` when nothing is
        notify-worthy (empty day or suppressed duplicate).
    """
    viability = compute_viability(circle, local_date, db)
    if viability.attendee_count == 0:
        return None  # No candidate – nothing to notify about

    event_type = "viable" if viability.is_viable else "non_viable_candidate"

    recent_cutoff = datetime.now(UTC) - timedelta(seconds=anti_storm_window)
    existing = db.execute(
        select(NotificationEvent).where(
            NotificationEvent.circle_id == circle.id,
            NotificationEvent.local_date == local_date,
            NotificationEvent.event_type == event_type,
            NotificationEvent.created_at >= recent_cutoff,
        )
    ).first()
    if existing:
        return None

    event = NotificationEvent(
        circle_id=circle.id,
        local_date=local_date,
        event_type=event_type,
    )
    db.add(event)
    db.flush()

    members = (
        db.execute(
            select(CircleMembership).where(
                CircleMembership.circle_id == circle.id
            )
        )
        .scalars()
        .all()
    )
    for member in members:
        prefs = member.notification_preferences or {}
        if prefs.get("disabled"):
            continue
        db.add(
            NotificationDelivery(
                notification_event_id=event.id,
                user_id=member.user_id,
            )
        )
    return event


def evaluate_and_notify_batch(
    circle_id: uuid.UUID, dates: list[date], db: Session
) -> None:
    """
    Evaluate a circle's changed days and emit one aggregated summary.

    Each qualifying day produces its own :class:`NotificationEvent`
    (the audit/dedupe record), but the batch is delivered as a single
    summary message per recipient. The anti-storm window scales with
    the aggregation window so duplicate suppression keeps pace with the
    broader debounce.

    :param circle_id: Circle to evaluate.
    :param dates: Circle-local dates that changed in this window.
    :param db: Active database session.
    """
    circle = db.get(Circle, circle_id)
    if not circle:
        return

    anti_storm_window = (
        get_settings().NOTIFICATION_AGGREGATION_WINDOW_SECONDS * 2
    )
    events: list[NotificationEvent] = []
    for local_date in sorted(dates):
        event = _evaluate_one(circle, local_date, db, anti_storm_window)
        if event is not None:
            events.append(event)

    if not events:
        return

    db.commit()
    logger.info(
        "Notification batch of %d event(s) created for circle %s",
        len(events),
        circle_id,
    )

    dispatch_batch(events, db)


def evaluate_and_notify(
    circle_id: uuid.UUID, local_date: date, db: Session
) -> None:
    """
    Evaluate a single day (batch of one).

    Thin wrapper preserved for direct callers and tests; delegates to
    :func:`evaluate_and_notify_batch`.

    :param circle_id: Circle to evaluate.
    :param local_date: Circle-local date to evaluate.
    :param db: Active database session.
    """
    evaluate_and_notify_batch(circle_id, [local_date], db)
