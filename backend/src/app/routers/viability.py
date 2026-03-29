"""Viability router: day viability computation endpoints."""

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import (
    get_circle_or_404,
    get_current_active_user,
    get_db,
    get_membership_or_403,
    validate_date_range,
)
from app.models.user import User
from app.schemas.viability import DayViability
from app.services.viability import compute_viability

router = APIRouter(tags=["viability"])


@router.get("/circles/{circle_id}/viability", response_model=list[DayViability])
def get_viability(
    circle_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[DayViability]:
    """
    Return computed viability for each day in [start_date, end_date]
    for *circle_id*.
    """
    circle = get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    validate_date_range(start_date, end_date)

    results = []
    current = start_date
    while current <= end_date:
        viability = compute_viability(circle, current, db)
        results.append(viability)
        current += timedelta(days=1)

    return results
