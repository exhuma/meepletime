"""Viability router: day viability computation endpoints."""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_db
from app.models.circle import Circle
from app.models.membership import CircleMembership
from app.models.user import User
from app.schemas.viability import DayViability
from app.services.viability import compute_viability

router = APIRouter(tags=["viability"])


def _require_membership(db: Session, circle_id: uuid.UUID, user_id: uuid.UUID) -> CircleMembership:
    """Return the membership record or raise HTTP 403 if the user is not a circle member."""
    membership = (
        db.query(CircleMembership)
        .filter(CircleMembership.circle_id == circle_id, CircleMembership.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not a member of this circle")
    return membership


@router.get("/circles/{circle_id}/viability", response_model=list[DayViability])
def get_viability(
    circle_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return computed viability for each day in [start_date, end_date] for *circle_id*."""
    circle = db.query(Circle).filter(Circle.id == circle_id).first()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found")
    _require_membership(db, circle_id, current_user.id)

    results = []
    current = start_date
    while current <= end_date:
        viability = compute_viability(circle, current, db)
        results.append(viability)
        current += timedelta(days=1)

    return results
