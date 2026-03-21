"""Pydantic schemas for user responses."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    """Public representation of a user profile."""

    id: uuid.UUID
    email: str
    display_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
