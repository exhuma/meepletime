"""Day overrides router: per-day circle setting overrides."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import (
    get_circle_or_404,
    get_current_active_user,
    get_db,
    get_membership_or_403,
)
from app.models.day_override import DayOverride
from app.models.membership import MemberRole
from app.models.user import User
from app.schemas.day_override import DayOverrideCreate, DayOverrideOut

router = APIRouter(tags=["day_overrides"])


@router.get(
    "/circles/{circle_id}/overrides/{local_date}",
    response_model=DayOverrideOut | None,
)
def get_override(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DayOverride | None:
    """
    Return the day override for *local_date* in *circle_id*, or null
    if none exists.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    return db.execute(
        select(DayOverride).where(
            DayOverride.circle_id == circle_id,
            DayOverride.local_date == local_date,
        )
    ).scalar_one_or_none()


@router.put(
    "/circles/{circle_id}/overrides/{local_date}", response_model=DayOverrideOut
)
def upsert_override(
    circle_id: uuid.UUID,
    local_date: date,
    override_in: DayOverrideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DayOverride:
    """
    Create or replace the day override for *local_date*. Requires
    owner or admin role.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner required",
        )

    existing = db.execute(
        select(DayOverride).where(
            DayOverride.circle_id == circle_id,
            DayOverride.local_date == local_date,
        )
    ).scalar_one_or_none()
    if existing:
        for field, value in override_in.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    override = DayOverride(
        circle_id=circle_id, local_date=local_date, **override_in.model_dump()
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


@router.delete(
    "/circles/{circle_id}/overrides/{local_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_override(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete the day override for *local_date* in *circle_id*. Requires
    owner or admin role.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner required",
        )

    existing = db.execute(
        select(DayOverride).where(
            DayOverride.circle_id == circle_id,
            DayOverride.local_date == local_date,
        )
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()
