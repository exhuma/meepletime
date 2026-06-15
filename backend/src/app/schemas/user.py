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
    # Resolved avatar reference (uploaded image, IDP picture, or
    # gravatar URL). ``None`` means the client should render initials.
    avatar_ref: str | None = None

    model_config = {"from_attributes": True}
