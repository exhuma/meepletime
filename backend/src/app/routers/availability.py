"""Availability router: day-level availability management."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import (
    get_circle_or_404,
    get_current_active_user,
    get_db,
    get_membership_or_403,
    validate_date_range,
)
from app.models.availability import (
    AvailabilityState as DBAvailabilityState,
)
from app.models.availability import (
    DayAvailability,
)
from app.models.circle import Circle
from app.models.membership import CircleMembership, MemberRole
from app.models.user import User
from app.schemas.availability import (
    AvailabilityOut,
    AvailabilitySet,
)
from app.schemas.jobs import (
    AvailabilityJobRequest,
    AvailabilityJobResponse,
)
from app.services.notifications import trigger_notification_eval

logger = logging.getLogger(__name__)

router = APIRouter(tags=["availability"])


def _local_today(tz_name: str) -> date:
    """Return the current local date for *tz_name*."""
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).date()


def _validate_date(
    local_date: date,
    circle: Circle,
    membership: CircleMembership,
) -> None:
    """
    Raise HTTP 400/403 if *local_date* is invalid.

    Past dates are read-only for regular members.
    Dates beyond the 3-month horizon are rejected for all.
    """
    today = _local_today(circle.timezone)
    horizon = today + timedelta(days=90)

    if local_date > horizon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date is beyond the 3-month planning horizon",
        )
    if local_date < today and membership.role not in (
        MemberRole.owner,
        MemberRole.admin,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Past dates are read-only for regular members",
        )


@router.get(
    "/circles/{circle_id}/availability",
    response_model=list[AvailabilityOut],
)
def get_availability(
    circle_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[DayAvailability]:
    """
    Return all availability records in [start_date, end_date].

    :param circle_id: Target circle.
    :param start_date: Inclusive range start.
    :param end_date: Inclusive range end.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: List of DayAvailability records.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    validate_date_range(start_date, end_date)

    return list(
        db.execute(
            select(DayAvailability).where(
                DayAvailability.circle_id == circle_id,
                DayAvailability.local_date >= start_date,
                DayAvailability.local_date <= end_date,
            )
        )
        .scalars()
        .all()
    )


@router.put(
    "/circles/{circle_id}/availability/{local_date}",
    response_model=AvailabilityOut,
)
def set_availability(
    circle_id: uuid.UUID,
    local_date: date,
    avail_in: AvailabilitySet,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DayAvailability:
    """
    Create or update the current user's availability for *local_date*.

    Write is idempotent for the same state.

    :param circle_id: Target circle.
    :param local_date: The date to set availability for.
    :param avail_in: Desired availability state.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: Saved DayAvailability record.
    """
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    _validate_date(local_date, circle, membership)

    existing = db.execute(
        select(DayAvailability).where(
            DayAvailability.circle_id == circle_id,
            DayAvailability.user_id == current_user.id,
            DayAvailability.local_date == local_date,
        )
    ).scalar_one_or_none()

    if existing:
        existing.state = DBAvailabilityState(avail_in.state.value)
        db.commit()
        db.refresh(existing)
        record = existing
    else:
        record = DayAvailability(
            circle_id=circle_id,
            user_id=current_user.id,
            local_date=local_date,
            state=DBAvailabilityState(avail_in.state.value),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    try:
        trigger_notification_eval(circle_id, local_date, SessionLocal)
    except Exception:
        logger.warning(
            "Notification eval failed for circle=%s date=%s",
            circle_id,
            local_date,
            exc_info=True,
        )

    return record


@router.delete(
    "/circles/{circle_id}/availability/{local_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_availability(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete the current user's availability for *local_date*.

    Equivalent to setting state to empty. No-op if no record exists.

    :param circle_id: Target circle.
    :param local_date: The date to clear availability for.
    :param db: Database session.
    :param current_user: Authenticated user.
    """
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    _validate_date(local_date, circle, membership)

    existing = db.execute(
        select(DayAvailability).where(
            DayAvailability.circle_id == circle_id,
            DayAvailability.user_id == current_user.id,
            DayAvailability.local_date == local_date,
        )
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()

    try:
        trigger_notification_eval(circle_id, local_date, SessionLocal)
    except Exception:
        logger.warning(
            "Notification eval failed for circle=%s date=%s",
            circle_id,
            local_date,
            exc_info=True,
        )


@router.post(
    "/circles/{circle_id}/availability/jobs",
    response_model=AvailabilityJobResponse,
)
def cycle_availability(
    circle_id: uuid.UUID,
    job: AvailabilityJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AvailabilityJobResponse:
    """
    Cycle the current user's availability state for a date.

    Implements the state cycle: empty -> attending -> hosting ->
    empty.  The "empty" state is represented by the absence of a
    database record.

    :param circle_id: Target circle.
    :param job: Job request containing action and arguments.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: Job response with the new availability record or
              None if cycled to empty.
    :raises HTTPException: 400 if action is not "cycle" or if
                           date is invalid.
    :raises HTTPException: 403 if user lacks permission.
    :raises HTTPException: 404 if circle not found.
    """
    if job.action != "cycle":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {job.action}",
        )

    local_date = job.arguments.local_date
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    _validate_date(local_date, circle, membership)

    existing = db.execute(
        select(DayAvailability).where(
            DayAvailability.circle_id == circle_id,
            DayAvailability.user_id == current_user.id,
            DayAvailability.local_date == local_date,
        )
    ).scalar_one_or_none()

    result: DayAvailability | None

    if existing is None:
        # empty -> attending
        record = DayAvailability(
            circle_id=circle_id,
            user_id=current_user.id,
            local_date=local_date,
            state=DBAvailabilityState.attending,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        result = record
    elif existing.state == DBAvailabilityState.attending:
        # attending -> hosting
        existing.state = DBAvailabilityState.hosting
        db.commit()
        db.refresh(existing)
        result = existing
    else:
        # hosting -> empty
        db.delete(existing)
        db.commit()
        result = None

    try:
        trigger_notification_eval(circle_id, local_date, SessionLocal)
    except Exception:
        logger.warning(
            "Notification eval failed for circle=%s date=%s",
            circle_id,
            local_date,
            exc_info=True,
        )

    availability_out = (
        AvailabilityOut.model_validate(result) if result else None
    )
    return AvailabilityJobResponse(availability=availability_out)
