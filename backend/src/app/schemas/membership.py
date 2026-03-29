"""Pydantic schemas for circle memberships."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.membership import MemberRole


class MembershipCreate(BaseModel):
    pseudonym: str = Field(min_length=1, max_length=64)
    can_host_default: bool = False


class MembershipOut(BaseModel):
    id: uuid.UUID
    circle_id: uuid.UUID
    user_id: uuid.UUID
    pseudonym: str
    role: MemberRole
    can_host_default: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class MembershipUpdate(BaseModel):
    pseudonym: str | None = Field(default=None, min_length=1, max_length=64)
    role: MemberRole | None = None
    can_host_default: bool | None = None


class InviteJoin(BaseModel):
    invite_token: uuid.UUID
    pseudonym: str = Field(min_length=1, max_length=64)
    can_host_default: bool = False
