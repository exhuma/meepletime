import uuid
from datetime import date, datetime
import enum

from pydantic import BaseModel


class AvailabilityState(str, enum.Enum):
    attending = "attending"
    hosting = "hosting"


class AvailabilitySet(BaseModel):
    state: AvailabilityState


class AvailabilityOut(BaseModel):
    id: uuid.UUID
    circle_id: uuid.UUID
    user_id: uuid.UUID
    local_date: date
    state: AvailabilityState
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
