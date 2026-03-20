from datetime import date

from sqlalchemy.orm import Session

from app.models.circle import Circle
from app.models.availability import DayAvailability, AvailabilityState
from app.models.day_override import DayOverride
from app.schemas.viability import DayViability
from app.schemas.availability import AvailabilityOut


def compute_viability(circle: Circle, local_date: date, db: Session) -> DayViability:
    availabilities = (
        db.query(DayAvailability)
        .filter(
            DayAvailability.circle_id == circle.id,
            DayAvailability.local_date == local_date,
        )
        .all()
    )

    override = (
        db.query(DayOverride)
        .filter(
            DayOverride.circle_id == circle.id,
            DayOverride.local_date == local_date,
        )
        .first()
    )

    # Resolve effective settings: override wins when not None
    host_required = circle.host_needed
    min_attendees = circle.minimum_attendees
    soft_max = circle.soft_max_attendees
    hard_max = circle.hard_max_attendees

    if override is not None:
        if override.override_host_needed is not None:
            host_required = override.override_host_needed
        if override.override_minimum_attendees is not None:
            min_attendees = override.override_minimum_attendees
        if override.override_soft_max_attendees is not None:
            soft_max = override.override_soft_max_attendees
        if override.override_hard_max_attendees is not None:
            hard_max = override.override_hard_max_attendees

    attendee_count = len(availabilities)
    hosting_count = sum(1 for a in availabilities if a.state == AvailabilityState.hosting)

    # Viability rules
    is_viable = attendee_count > 0
    if is_viable and min_attendees is not None:
        is_viable = attendee_count >= min_attendees
    if is_viable and host_required:
        is_viable = hosting_count >= 1
    if is_viable and hard_max is not None:
        is_viable = attendee_count <= hard_max

    is_soft_max_exceeded = soft_max is not None and attendee_count > soft_max
    has_multiple_hosts_warning = hosting_count > 1

    avail_out = [AvailabilityOut.model_validate(a) for a in availabilities]

    return DayViability(
        circle_id=circle.id,
        local_date=local_date,
        attendee_count=attendee_count,
        hosting_count=hosting_count,
        is_viable=is_viable,
        is_soft_max_exceeded=is_soft_max_exceeded,
        has_multiple_hosts_warning=has_multiple_hosts_warning,
        availabilities=avail_out,
    )
