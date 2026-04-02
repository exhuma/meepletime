"""Pydantic schemas for host day constraints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class HostDayConstraintSet(BaseModel):
    """
    Input schema for creating or replacing a host day constraint.
    """

    override_minimum_attendees: int | None = None
    override_soft_max_attendees: int | None = None
    override_hard_max_attendees: int | None = None


class HostDayConstraintOut(BaseModel):
    """
    Output schema for a host day constraint record.
    """

    id: uuid.UUID
    circle_id: uuid.UUID
    user_id: uuid.UUID
    local_date: date
    override_minimum_attendees: int | None
    override_soft_max_attendees: int | None
    override_hard_max_attendees: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
