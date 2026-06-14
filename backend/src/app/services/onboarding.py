"""Service layer for per-user onboarding state."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.onboarding import UserOnboardingState


def get_or_create_state(db: Session, user_id: uuid.UUID) -> UserOnboardingState:
    """
    Return the user's onboarding row, creating defaults on first use.

    :param db: Active database session.
    :param user_id: The user whose state to load.
    :returns: The persisted onboarding state row.
    """
    state = db.execute(
        select(UserOnboardingState).where(
            UserOnboardingState.user_id == user_id
        )
    ).scalar_one_or_none()
    if state is None:
        state = UserOnboardingState(user_id=user_id, seen_tips=[])
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def mark_welcome_seen(
    db: Session, state: UserOnboardingState
) -> UserOnboardingState:
    """
    Flag the welcome intro as seen (idempotent).

    :param db: Active database session.
    :param state: The onboarding row to mutate.
    :returns: The refreshed onboarding state row.
    """
    if not state.welcome_seen:
        state.welcome_seen = True
        db.commit()
        db.refresh(state)
    return state


def mark_tips_seen(
    db: Session,
    state: UserOnboardingState,
    tip_keys: list[str],
) -> UserOnboardingState:
    """
    Union the given tip keys into the seen set and persist.

    The attribute is *reassigned* (not mutated in place) so that
    SQLAlchemy detects the JSON change and flushes it.

    :param db: Active database session.
    :param state: The onboarding row to mutate.
    :param tip_keys: Tip keys the user has now been shown.
    :returns: The refreshed onboarding state row.
    """
    current = set(state.seen_tips or [])
    merged = current | set(tip_keys)
    if merged != current:
        # Sorted for stable storage and deterministic round-trips.
        state.seen_tips = sorted(merged)
        db.commit()
        db.refresh(state)
    return state
