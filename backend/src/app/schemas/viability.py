"""Pydantic schemas for viability responses."""
import uuid
from datetime import date

from pydantic import BaseModel

from app.schemas.availability import AvailabilityOut


class DayViability(BaseModel):
    circle_id: uuid.UUID
    local_date: date
    attendee_count: int
    hosting_count: int
    is_viable: bool
    is_soft_max_exceeded: bool
    has_multiple_hosts_warning: bool
    availabilities: list[AvailabilityOut]


class CalendarDay(BaseModel):
    local_date: date
    viability: DayViability | None
