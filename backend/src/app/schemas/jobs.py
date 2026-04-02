"""Pydantic schemas for job-pattern operations."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.schemas.availability import AvailabilityOut


class AvailabilityCycleArguments(BaseModel):
    """
    Arguments for the availability cycle action.

    :param local_date: The date to cycle availability for.
    """

    local_date: date


class AvailabilityJobRequest(BaseModel):
    """
    Job request for availability operations.

    :param action: The action to perform. Currently only
                   "cycle" is supported.
    :param arguments: Action-specific arguments.
    """

    action: Literal["cycle"]
    arguments: AvailabilityCycleArguments


class AvailabilityJobResponse(BaseModel):
    """
    Response for an availability job operation.

    :param availability: The resulting availability record,
                         or None if the state cycled to empty.
    """

    availability: AvailabilityOut | None
