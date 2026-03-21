"""Day overrides router: per-day circle setting overrides."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_db
from app.models.circle import Circle
from app.models.day_override import DayOverride
from app.models.membership import CircleMembership, MemberRole
from app.models.user import User
from app.schemas.day_override import DayOverrideCreate, DayOverrideOut

router = APIRouter(tags=["day_overrides"])


def _get_circle_or_404(db: Session, circle_id: uuid.UUID) -> Circle:
    """Return the circle or raise HTTP 404 if it does not exist."""
    circle = db.query(Circle).filter(Circle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found")
    return circle


def _require_membership(db: Session, circle_id: uuid.UUID, user_id: uuid.UUID) -> CircleMembership:
    """Return the membership or raise HTTP 403 if the user is not a member."""
    m = (
        db.query(CircleMembership)
        .filter(CircleMembership.circle_id == circle_id, CircleMembership.user_id == user_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this circle")
    return m


@router.get("/circles/{circle_id}/overrides/{local_date}", response_model=DayOverrideOut | None)
def get_override(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the day override for *local_date* in *circle_id*, or null if none exists."""
    _get_circle_or_404(db, circle_id)
    _require_membership(db, circle_id, current_user.id)
    return (
        db.query(DayOverride)
        .filter(DayOverride.circle_id == circle_id, DayOverride.local_date == local_date)
        .first()
    )


@router.put("/circles/{circle_id}/overrides/{local_date}", response_model=DayOverrideOut)
def upsert_override(
    circle_id: uuid.UUID,
    local_date: date,
    override_in: DayOverrideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or replace the day override for *local_date*. Requires owner or admin role."""
    _get_circle_or_404(db, circle_id)
    membership = _require_membership(db, circle_id, current_user.id)
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or owner required")

    existing = (
        db.query(DayOverride)
        .filter(DayOverride.circle_id == circle_id, DayOverride.local_date == local_date)
        .first()
    )
    if existing:
        for field, value in override_in.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    override = DayOverride(circle_id=circle_id, local_date=local_date, **override_in.model_dump())
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


@router.delete("/circles/{circle_id}/overrides/{local_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_override(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete the day override for *local_date* in *circle_id*. Requires owner or admin role."""
    _get_circle_or_404(db, circle_id)
    membership = _require_membership(db, circle_id, current_user.id)
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or owner required")

    existing = (
        db.query(DayOverride)
        .filter(DayOverride.circle_id == circle_id, DayOverride.local_date == local_date)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
