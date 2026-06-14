"""Pydantic schemas for onboarding-state endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class OnboardingStateOut(BaseModel):
    """The caller's onboarding progress."""

    welcome_seen: bool
    seen_tips: list[str]

    model_config = {"from_attributes": True}


class WelcomeSeenIn(BaseModel):
    """Mark the welcome intro as seen."""

    welcome_seen: bool = True


class TipsSeenIn(BaseModel):
    """Append newly-shown tip keys to the seen set."""

    tip_keys: list[str]
