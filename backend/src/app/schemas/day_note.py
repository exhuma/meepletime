"""Pydantic schemas for day notes."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel


class DayNoteCreate(BaseModel):
    content: str


class DayNoteOut(BaseModel):
    id: uuid.UUID
    circle_id: uuid.UUID
    user_id: uuid.UUID
    local_date: date
    content: str
    created_at: datetime
    pseudonym: str | None = None

    model_config = {"from_attributes": True}
