"""Per-user onboarding-state router.

All endpoints are scoped to the authenticated user; a user can only
read and modify their own onboarding progress.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingStateOut,
    TipsSeenIn,
    WelcomeSeenIn,
)
from app.services.onboarding import (
    get_or_create_state,
    mark_tips_seen,
    mark_welcome_seen,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("", response_model=OnboardingStateOut)
def read_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OnboardingStateOut:
    """
    Return the caller's onboarding state.

    Defaults (welcome unseen, no tips) are created on first access.

    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The caller's onboarding state.
    """
    state = get_or_create_state(db, current_user.id)
    return OnboardingStateOut.model_validate(state)


@router.put("/welcome", response_model=OnboardingStateOut)
def put_welcome(
    payload: WelcomeSeenIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OnboardingStateOut:
    """
    Mark the welcome intro as seen.

    Idempotent: repeating the call has no further effect.

    :param payload: Whether the welcome intro has been seen.
    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated onboarding state.
    """
    state = get_or_create_state(db, current_user.id)
    if payload.welcome_seen:
        state = mark_welcome_seen(db, state)
    return OnboardingStateOut.model_validate(state)


@router.post("/tips", response_model=OnboardingStateOut)
def post_tips(
    payload: TipsSeenIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OnboardingStateOut:
    """
    Union newly-shown tip keys into the caller's seen set.

    Idempotent: re-sending keys already seen has no further effect.

    :param payload: Tip keys the user has now been shown.
    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated onboarding state.
    """
    state = get_or_create_state(db, current_user.id)
    state = mark_tips_seen(db, state, payload.tip_keys)
    return OnboardingStateOut.model_validate(state)
