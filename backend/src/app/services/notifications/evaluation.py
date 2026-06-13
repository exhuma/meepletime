"""Derived-state evaluation that emits notification events.

Computes viability for ``(circle_id, local_date)``, applies the
anti-storm suppression rules (§12.3), writes one event plus a delivery
row per non-muted member, then hands the event to the dispatcher for
actual transport.
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
from app.services.notifications.dispatch import dispatch_event
from app.services.viability import compute_viability

logger = logging.getLogger(__name__)


def evaluate_and_notify(
    circle_id: uuid.UUID, local_date: date, db: Session
) -> None:
    """
    Evaluate viability and emit a notification event if warranted.

    Anti-storm logic suppresses duplicate events that fall within
    twice the debounce window. After persistence, the event is
    dispatched across the configured channels (best-effort).

    :param circle_id: Circle to evaluate.
    :param local_date: Circle-local date to evaluate.
    :param db: Active database session.
    """
    circle = db.get(Circle, circle_id)
    if not circle:
        return

    viability = compute_viability(circle, local_date, db)

    if viability.attendee_count == 0:
        return  # No candidate – nothing to notify about

    event_type = "viable" if viability.is_viable else "non_viable_candidate"

    recent_cutoff = datetime.now(UTC) - timedelta(
        seconds=get_settings().NOTIFICATION_DEBOUNCE_SECONDS * 2
    )
    existing = db.execute(
        select(NotificationEvent).where(
            NotificationEvent.circle_id == circle_id,
            NotificationEvent.local_date == local_date,
            NotificationEvent.event_type == event_type,
            NotificationEvent.created_at >= recent_cutoff,
        )
    ).first()
    if existing:
        return

    event = NotificationEvent(
        circle_id=circle_id,
        local_date=local_date,
        event_type=event_type,
    )
    db.add(event)
    db.flush()

    members = (
        db.execute(
            select(CircleMembership).where(
                CircleMembership.circle_id == circle_id
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

    db.commit()
    logger.info(
        "Notification event %s created for circle %s on %s",
        event_type,
        circle_id,
        local_date,
    )

    dispatch_event(event, db)
