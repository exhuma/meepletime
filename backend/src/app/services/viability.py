"""Viability computation service."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.availability import AvailabilityState, DayAvailability
from app.models.circle import Circle
from app.models.host_day_constraint import HostDayConstraint
from app.schemas.availability import AvailabilityOut
from app.schemas.viability import DayViability


def _merge_min(a: int | None, b: int | None) -> int | None:
    """
    Most restrictive merge for minimum thresholds (take max).
    """
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def _merge_max(a: int | None, b: int | None) -> int | None:
    """
    Most restrictive merge for maximum thresholds (take min).
    """
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


def compute_viability(
    circle: Circle, local_date: date, db: Session
) -> DayViability:
    """
    Compute the derived viability for *local_date* in *circle*.

    Two evaluation paths:

    * **No hosting members** — circle defaults are applied directly.
      If ``host_needed`` is true the day is non-viable.
    * **Hosting members present** — each hosting member's effective
      constraints are evaluated (circle defaults merged with any
      personal ``HostDayConstraint``, taking the most restrictive
      value per field).  The day is viable when at least one hosting
      member's effective constraints are satisfied by the current
      attendee count (any-host logic).

    ``viable_host_count`` reports how many hosting members can
    accommodate the current attendance; ``has_multiple_viable_hosts``
    fires when this count exceeds one so the frontend can signal
    that members should agree out-of-band on who hosts.

    :param circle: The circle whose viability is being evaluated.
    :param local_date: The date to evaluate in the circle timezone.
    :param db: Database session.
    :returns: Computed ``DayViability`` for the given circle-day.
    """
    availabilities = list(
        db.execute(
            select(DayAvailability).where(
                DayAvailability.circle_id == circle.id,
                DayAvailability.local_date == local_date,
            )
        )
        .scalars()
        .all()
    )

    attendee_count = len(availabilities)
    hosting_avails = [
        a for a in availabilities if a.state == AvailabilityState.hosting
    ]
    hosting_count = len(hosting_avails)

    is_viable: bool
    viable_host_count: int
    is_soft_max_exceeded: bool

    if attendee_count == 0:
        is_viable = False
        viable_host_count = 0
        is_soft_max_exceeded = False

    elif not hosting_avails:
        # No hosts present — evaluate circle defaults directly.
        is_viable = not circle.host_needed
        if is_viable and circle.minimum_attendees is not None:
            is_viable = attendee_count >= circle.minimum_attendees
        if is_viable and circle.hard_max_attendees is not None:
            is_viable = attendee_count <= circle.hard_max_attendees
        viable_host_count = 0
        is_soft_max_exceeded = (
            circle.soft_max_attendees is not None
            and attendee_count > circle.soft_max_attendees
        )

    else:
        # Hosting members present — per-host any-viable evaluation.
        viable_host_count = 0
        is_soft_max_exceeded = False

        for avail in hosting_avails:
            constraint = db.execute(
                select(HostDayConstraint).where(
                    HostDayConstraint.circle_id == circle.id,
                    HostDayConstraint.user_id == avail.user_id,
                    HostDayConstraint.local_date == local_date,
                )
            ).scalar_one_or_none()
            eff_min = _merge_min(
                circle.minimum_attendees,
                constraint.override_minimum_attendees if constraint else None,
            )
            eff_hard_max = _merge_max(
                circle.hard_max_attendees,
                constraint.override_hard_max_attendees if constraint else None,
            )
            eff_soft_max = _merge_max(
                circle.soft_max_attendees,
                constraint.override_soft_max_attendees if constraint else None,
            )

            host_viable = True
            if eff_min is not None and attendee_count < eff_min:
                host_viable = False
            if eff_hard_max is not None and attendee_count > eff_hard_max:
                host_viable = False

            if host_viable:
                viable_host_count += 1
                if eff_soft_max is not None and attendee_count > eff_soft_max:
                    is_soft_max_exceeded = True

        is_viable = viable_host_count >= 1

    avail_out = [AvailabilityOut.model_validate(a) for a in availabilities]

    return DayViability(
        circle_id=circle.id,
        local_date=local_date,
        attendee_count=attendee_count,
        hosting_count=hosting_count,
        is_viable=is_viable,
        is_soft_max_exceeded=is_soft_max_exceeded,
        has_multiple_viable_hosts=viable_host_count > 1,
        viable_host_count=viable_host_count,
        availabilities=avail_out,
    )


def next_viable_date(
    circle: Circle,
    db: Session,
    *,
    today: date,
    horizon_days: int = 366,
) -> date | None:
    """
    Return the earliest viable date on or after *today* for *circle*.

    Only days with at least one availability record can ever be
    viable (an empty day is never a meetup candidate), so the search
    is limited to those candidate dates within
    ``[today, today + horizon_days]``, evaluated in ascending order
    with an early exit on the first viable one.

    :param circle: The circle whose schedule is searched.
    :param today: The current date in the circle's timezone.
    :param horizon_days: How far ahead to look (default ~1 year).
    :returns: The earliest upcoming viable date, or ``None``.
    """
    horizon = today + timedelta(days=horizon_days)
    candidate_dates = (
        db.execute(
            select(DayAvailability.local_date)
            .where(
                DayAvailability.circle_id == circle.id,
                DayAvailability.local_date >= today,
                DayAvailability.local_date <= horizon,
            )
            .distinct()
            .order_by(DayAvailability.local_date)
        )
        .scalars()
        .all()
    )
    for candidate in candidate_dates:
        if compute_viability(circle, candidate, db).is_viable:
            return candidate
    return None
