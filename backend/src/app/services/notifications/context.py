"""Event context shared by all notification channels.

The :class:`EventContext` carries the human-facing title/body and a
deep link for one notification event, so channels do not each
re-derive presentation from the raw ORM event.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.circle import Circle
from app.models.notification import NotificationEvent


@dataclass
class EventContext:
    """
    Presentation data for a single notification event.

    :param event_id: The originating event id.
    :param circle_id: Circle the event belongs to.
    :param circle_name: Display name of the circle.
    :param local_date: The day the event concerns (circle-local).
    :param event_type: Derived event type string.
    :param title: Short notification title.
    :param body: Notification body text.
    :param url: Deep link into the frontend day view.
    """

    event_id: uuid.UUID
    circle_id: uuid.UUID
    circle_name: str
    local_date: date
    event_type: str
    title: str
    body: str
    url: str


def build_event_context(event: NotificationEvent, db: Session) -> EventContext:
    """
    Build an :class:`EventContext` from a persisted event.

    :param event: The notification event to render.
    :param db: Active database session.
    :returns: A populated :class:`EventContext`.
    """
    circle = db.get(Circle, event.circle_id)
    name = circle.name if circle else "your circle"
    base = get_settings().APP_BASE_URL.rstrip("/")
    url = f"{base}/circles/{event.circle_id}/day/{event.local_date}"

    if event.event_type == "viable":
        title = f"{name}: a day is now viable"
        body = f"{event.local_date} is now a viable meetup day for {name}."
    else:
        title = f"{name}: meetup candidate"
        body = f"{event.local_date} has a meetup candidate forming for {name}."

    return EventContext(
        event_id=event.id,
        circle_id=event.circle_id,
        circle_name=name,
        local_date=event.local_date,
        event_type=event.event_type,
        title=title,
        body=body,
        url=url,
    )
