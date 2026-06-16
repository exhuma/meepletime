"""Event context shared by all notification channels.

The :class:`EventContext` carries the human-facing title/body and a
deep link for one notification event, so channels do not each
re-derive presentation from the raw ORM event.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.availability import AvailabilityState, DayAvailability
from app.models.circle import Circle
from app.models.day_description import DayDescription
from app.models.membership import CircleMembership
from app.models.notification import NotificationEvent
from app.services.delta import delta_to_text


@dataclass
class DescBlock:
    """One day-description block folded into a notification.

    :param label: Host pseudonym for a per-host description, or
        ``None`` for the circle-wide description.
    :param text: Plain-text rendering of the Quill description.
    """

    label: str | None
    text: str


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
    day_descriptions: dict[date, list[DescBlock]] = field(default_factory=dict)


def _description_blocks(
    circle: Circle, local_date: date, db: Session
) -> list[DescBlock]:
    """
    Collect the day's description(s) for folding into a notification.

    Host-required circles contribute one block per member currently
    hosting the day (labelled with their pseudonym); other circles
    contribute the single circle-wide description. Empty descriptions
    are skipped.

    :param circle: The circle the day belongs to.
    :param local_date: The day to describe.
    :param db: Active database session.
    :returns: Description blocks, possibly empty.
    """
    if circle.host_needed:
        hosting_ids = set(
            db.execute(
                select(DayAvailability.user_id).where(
                    DayAvailability.circle_id == circle.id,
                    DayAvailability.local_date == local_date,
                    DayAvailability.state == AvailabilityState.hosting,
                )
            ).scalars()
        )
        if not hosting_ids:
            return []
        rows = (
            db.execute(
                select(DayDescription).where(
                    DayDescription.circle_id == circle.id,
                    DayDescription.local_date == local_date,
                    DayDescription.host_user_id.is_not(None),
                )
            )
            .scalars()
            .all()
        )
        blocks: list[DescBlock] = []
        for row in rows:
            if row.host_user_id not in hosting_ids:
                continue
            text = delta_to_text(row.content_delta)
            if not text:
                continue
            membership = db.execute(
                select(CircleMembership).where(
                    CircleMembership.circle_id == circle.id,
                    CircleMembership.user_id == row.host_user_id,
                )
            ).scalar_one_or_none()
            label = membership.pseudonym if membership else None
            blocks.append(DescBlock(label=label, text=text))
        blocks.sort(key=lambda b: (b.label or ""))
        return blocks

    row = db.execute(
        select(DayDescription).where(
            DayDescription.circle_id == circle.id,
            DayDescription.local_date == local_date,
            DayDescription.host_user_id.is_(None),
        )
    ).scalar_one_or_none()
    if row is None:
        return []
    text = delta_to_text(row.content_delta)
    return [DescBlock(label=None, text=text)] if text else []


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
    elif event.event_type == "no_longer_viable":
        title = f"{name}: a day is no longer viable"
        body = (
            f"{event.local_date} is no longer a viable meetup day for {name}."
        )
    else:
        title = f"{name}: meetup candidate"
        body = f"{event.local_date} has a meetup candidate forming for {name}."

    day_descriptions: dict[date, list[DescBlock]] = {}
    if event.event_type == "viable" and circle is not None:
        blocks = _description_blocks(circle, event.local_date, db)
        if blocks:
            day_descriptions[event.local_date] = blocks

    return EventContext(
        event_id=event.id,
        circle_id=event.circle_id,
        circle_name=name,
        local_date=event.local_date,
        event_type=event.event_type,
        title=title,
        body=body,
        url=url,
        day_descriptions=day_descriptions,
    )


def _summary_title(name: str, viable: int, lost: int, forming: int) -> str:
    """
    Build the title for an aggregated, multi-day summary.

    :param name: Display name of the circle.
    :param viable: Number of days that became viable.
    :param lost: Number of days that are no longer viable.
    :param forming: Number of days with a forming candidate.
    :returns: A short summary title.
    """
    present = [
        (viable, "viable"),
        (lost, "no longer viable"),
        (forming, "forming"),
    ]
    buckets = [(count, label) for count, label in present if count]

    # Preserve the friendlier single-bucket phrasing.
    if len(buckets) == 1:
        count, label = buckets[0]
        if label == "viable":
            return f"{name}: {count} days now viable"
        if label == "forming":
            return f"{name}: {count} meetup candidates forming"
        return f"{name}: {count} days no longer viable"

    parts = ", ".join(f"{count} {label}" for count, label in buckets)
    return f"{name}: {parts}"


def build_batch_context(
    events: list[NotificationEvent], db: Session
) -> EventContext:
    """
    Build a single context covering one or more events for a circle.

    A batch of one delegates to :func:`build_event_context`, preserving
    the exact single-day wording. For multiple days the title and body
    summarise every day's derived transition and the link points at the
    circle calendar rather than a single day.

    :param events: The events to render (all for the same circle).
    :param db: Active database session.
    :returns: A populated :class:`EventContext`.
    """
    if len(events) == 1:
        return build_event_context(events[0], db)

    ordered = sorted(events, key=lambda e: e.local_date)
    primary = ordered[0]
    circle = db.get(Circle, primary.circle_id)
    name = circle.name if circle else "your circle"
    base = get_settings().APP_BASE_URL.rstrip("/")
    url = f"{base}/circles/{primary.circle_id}"

    viable = sum(1 for e in ordered if e.event_type == "viable")
    lost = sum(1 for e in ordered if e.event_type == "no_longer_viable")
    forming = len(ordered) - viable - lost
    title = _summary_title(name, viable, lost, forming)

    lines = [f"Updated meetup days for {name}:"]
    for event in ordered:
        if event.event_type == "viable":
            lines.append(f"- {event.local_date}: now viable")
        elif event.event_type == "no_longer_viable":
            lines.append(f"- {event.local_date}: no longer viable")
        else:
            lines.append(f"- {event.local_date}: candidate forming")
    body = "\n".join(lines)

    day_descriptions: dict[date, list[DescBlock]] = {}
    if circle is not None:
        for event in ordered:
            if event.event_type != "viable":
                continue
            blocks = _description_blocks(circle, event.local_date, db)
            if blocks:
                day_descriptions[event.local_date] = blocks

    return EventContext(
        event_id=primary.id,
        circle_id=primary.circle_id,
        circle_name=name,
        local_date=primary.local_date,
        event_type="batch",
        title=title,
        body=body,
        url=url,
        day_descriptions=day_descriptions,
    )
