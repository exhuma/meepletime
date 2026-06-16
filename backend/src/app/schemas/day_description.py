"""Pydantic schemas for day descriptions."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.services.delta import DeltaDoc


class DayDescriptionUpsert(BaseModel):
    """Request body for setting a description (validated Delta)."""

    content_delta: DeltaDoc


class DayDescriptionOut(BaseModel):
    """A single description row, circle-wide or per-host."""

    id: uuid.UUID
    circle_id: uuid.UUID
    local_date: date
    host_user_id: uuid.UUID | None
    content_delta: dict[str, Any]
    updated_at: datetime
    host_pseudonym: str | None = None

    model_config = {"from_attributes": True}


class DayDescriptionBundle(BaseModel):
    """All descriptions for a circle-day.

    ``circle_wide`` is the single host-agnostic description (used by
    circles that do not require a host). ``per_host`` holds one entry
    per member currently hosting the day.
    """

    circle_wide: DayDescriptionOut | None = None
    per_host: list[DayDescriptionOut] = []
