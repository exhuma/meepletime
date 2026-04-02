"""Host day constraints router.

Manages per-hosting-member per-day capacity constraints.  A
constraint row represents situational limits that differ from circle
defaults on a specific date (e.g. reduced capacity due to
renovations).

Routes
------
``/me/`` routes
    Available to any authenticated circle member managing their own
    constraints.

``/{user_id}/`` routes
    Restricted to circle owner or admin; allows managing any
    member's constraints (e.g. when a host is unavailable to update
    their own record).
"""

from __future__ import annotations

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
from app.models.host_day_constraint import HostDayConstraint
from app.models.membership import MemberRole
from app.models.user import User
from app.schemas.host_day_constraint import (
    HostDayConstraintOut,
    HostDayConstraintSet,
)

router = APIRouter(tags=["host_day_constraints"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_constraint(
    db: Session,
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    local_date: date,
) -> HostDayConstraint | None:
    return db.execute(
        select(HostDayConstraint).where(
            HostDayConstraint.circle_id == circle_id,
            HostDayConstraint.user_id == user_id,
            HostDayConstraint.local_date == local_date,
        )
    ).scalar_one_or_none()


def _upsert_constraint(
    db: Session,
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    local_date: date,
    data: HostDayConstraintSet,
) -> HostDayConstraint:
    existing = _get_constraint(db, circle_id, user_id, local_date)
    if existing:
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    constraint = HostDayConstraint(
        circle_id=circle_id,
        user_id=user_id,
        local_date=local_date,
        **data.model_dump(),
    )
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return constraint


def _delete_constraint(
    db: Session,
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    local_date: date,
) -> None:
    existing = _get_constraint(db, circle_id, user_id, local_date)
    if existing:
        db.delete(existing)
        db.commit()


# ---------------------------------------------------------------------------
# Own-constraint routes (any circle member)
# ---------------------------------------------------------------------------


@router.get(
    "/circles/{circle_id}/host-constraints/me/{local_date}",
    response_model=HostDayConstraintOut | None,
)
def get_own_constraint(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HostDayConstraint | None:
    """
    Return the calling member's host day constraint for *local_date*,
    or null if none has been set.

    :param circle_id: Target circle.
    :param local_date: The date to look up.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: Existing constraint row, or ``None``.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    return _get_constraint(db, circle_id, current_user.id, local_date)


@router.put(
    "/circles/{circle_id}/host-constraints/me/{local_date}",
    response_model=HostDayConstraintOut,
)
def set_own_constraint(
    circle_id: uuid.UUID,
    local_date: date,
    constraint_in: HostDayConstraintSet,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HostDayConstraint:
    """
    Create or replace the calling member's host day constraint for
    *local_date*.  Any circle member may manage their own constraints.

    :param circle_id: Target circle.
    :param local_date: The date to constrain.
    :param constraint_in: New constraint values.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: Saved constraint row.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    return _upsert_constraint(
        db, circle_id, current_user.id, local_date, constraint_in
    )


@router.delete(
    "/circles/{circle_id}/host-constraints/me/{local_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_own_constraint(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete the calling member's host day constraint for *local_date*.
    No-op if no constraint exists.

    :param circle_id: Target circle.
    :param local_date: The date whose constraint is removed.
    :param db: Database session.
    :param current_user: Authenticated user.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    _delete_constraint(db, circle_id, current_user.id, local_date)


# ---------------------------------------------------------------------------
# Admin routes (owner / admin only)
# ---------------------------------------------------------------------------


@router.get(
    "/circles/{circle_id}/host-constraints/{user_id}/{local_date}",
    response_model=HostDayConstraintOut | None,
)
def get_member_constraint(
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HostDayConstraint | None:
    """
    Return a specific member's host day constraint.  Requires owner
    or admin role.

    :param circle_id: Target circle.
    :param user_id: The member whose constraint is requested.
    :param local_date: The date to look up.
    :param db: Database session.
    :param current_user: Authenticated caller (must be owner/admin).
    :returns: Existing constraint row, or ``None``.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner required",
        )
    return _get_constraint(db, circle_id, user_id, local_date)


@router.put(
    "/circles/{circle_id}/host-constraints/{user_id}/{local_date}",
    response_model=HostDayConstraintOut,
)
def set_member_constraint(
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    local_date: date,
    constraint_in: HostDayConstraintSet,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HostDayConstraint:
    """
    Create or replace a specific member's host day constraint for
    *local_date*.  Requires owner or admin role.  Intended for cases
    where a host is unable to update their own record.

    :param circle_id: Target circle.
    :param user_id: The member whose constraint is set.
    :param local_date: The date to constrain.
    :param constraint_in: New constraint values.
    :param db: Database session.
    :param current_user: Authenticated caller (must be owner/admin).
    :returns: Saved constraint row.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner required",
        )
    return _upsert_constraint(db, circle_id, user_id, local_date, constraint_in)


@router.delete(
    "/circles/{circle_id}/host-constraints/{user_id}/{local_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_member_constraint(
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete a specific member's host day constraint.  Requires owner
    or admin role.  No-op if no constraint exists.

    :param circle_id: Target circle.
    :param user_id: The member whose constraint is removed.
    :param local_date: The date whose constraint is removed.
    :param db: Database session.
    :param current_user: Authenticated caller (must be owner/admin).
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner required",
        )
    _delete_constraint(db, circle_id, user_id, local_date)
