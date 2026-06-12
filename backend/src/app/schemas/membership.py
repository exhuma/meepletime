"""Pydantic schemas for circle memberships."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.membership import MemberRole
from app.services.invite import INVITE_LENGTH, is_valid_pin, normalize_pin


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
    invite_token: str = Field(
        min_length=INVITE_LENGTH, max_length=INVITE_LENGTH
    )
    pseudonym: str = Field(min_length=1, max_length=64)
    can_host_default: bool = False

    @field_validator("invite_token", mode="before")
    @classmethod
    def _normalize_token(cls, value: object) -> object:
        """Normalize and validate the PIN before length checks run."""
        if not isinstance(value, str):
            return value
        normalized = normalize_pin(value)
        if not is_valid_pin(normalized):
            raise ValueError("Invalid invite PIN")
        return normalized
