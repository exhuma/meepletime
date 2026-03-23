"""Pydantic schemas for day overrides."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class DayOverrideCreate(BaseModel):
    override_host_needed: bool | None = None
    override_minimum_attendees: int | None = None
    override_soft_max_attendees: int | None = None
    override_hard_max_attendees: int | None = None


class DayOverrideOut(BaseModel):
    id: uuid.UUID
    circle_id: uuid.UUID
    local_date: date
    override_host_needed: bool | None
    override_minimum_attendees: int | None
    override_soft_max_attendees: int | None
    override_hard_max_attendees: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
