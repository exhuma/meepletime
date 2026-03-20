import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CircleCreate(BaseModel):
    name: str
    description: str | None = None
    image_ref: str | None = None
    timezone: str = "UTC"
    host_needed: bool = False
    minimum_attendees: int | None = None
    soft_max_attendees: int | None = None
    hard_max_attendees: int | None = None
    external_links: list[Any] | None = None


class CircleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    image_ref: str | None = None
    timezone: str | None = None
    host_needed: bool | None = None
    minimum_attendees: int | None = None
    soft_max_attendees: int | None = None
    hard_max_attendees: int | None = None
    external_links: list[Any] | None = None


class CircleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    image_ref: str | None
    timezone: str
    invite_token: uuid.UUID
    host_needed: bool
    minimum_attendees: int | None
    soft_max_attendees: int | None
    hard_max_attendees: int | None
    external_links: list[Any] | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
