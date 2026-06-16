"""Day description router: static session detail for a circle-day.

A *description* is distinct from the threaded :class:`DayNote`. It has
two shapes, keyed by ``host_user_id``:

``circle-wide`` (``host_user_id IS NULL``)
    A single host-agnostic description, used by circles that do not
    require a host. Owned by circle owner/admin.

``per-host`` (``host_user_id`` set)
    One description per member hosting the day, owned by that host
    (``/hosts/me``) with an owner/admin override (``/hosts/{user_id}``).
    Used by host-required circles so members can compare host offers.

The stored payload is a validated Quill Delta document; no HTML is
accepted or trusted on ingress.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import (
    get_circle_or_404,
    get_current_active_user,
    get_db,
    get_membership_or_403,
    require_admin_or_owner,
)
from app.models.availability import AvailabilityState, DayAvailability
from app.models.day_description import DayDescription
from app.models.membership import CircleMembership
from app.models.user import User
from app.schemas.day_description import (
    DayDescriptionBundle,
    DayDescriptionOut,
    DayDescriptionUpsert,
)

router = APIRouter(tags=["day_descriptions"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _enrich(desc: DayDescription, db: Session) -> DayDescriptionOut:
    """Attach the host's circle pseudonym to a per-host row."""
    out = DayDescriptionOut.model_validate(desc)
    if desc.host_user_id is not None:
        membership = db.execute(
            select(CircleMembership).where(
                CircleMembership.circle_id == desc.circle_id,
                CircleMembership.user_id == desc.host_user_id,
            )
        ).scalar_one_or_none()
        out.host_pseudonym = membership.pseudonym if membership else None
    return out


def _get_description(
    db: Session,
    circle_id: uuid.UUID,
    local_date: date,
    host_user_id: uuid.UUID | None,
) -> DayDescription | None:
    host_clause = (
        DayDescription.host_user_id.is_(None)
        if host_user_id is None
        else DayDescription.host_user_id == host_user_id
    )
    return db.execute(
        select(DayDescription).where(
            DayDescription.circle_id == circle_id,
            DayDescription.local_date == local_date,
            host_clause,
        )
    ).scalar_one_or_none()


def _upsert_description(
    db: Session,
    circle_id: uuid.UUID,
    local_date: date,
    host_user_id: uuid.UUID | None,
    data: DayDescriptionUpsert,
    editor_id: uuid.UUID,
) -> DayDescription:
    """Create or replace a description row (application-level upsert)."""
    # exclude_none keeps the stored Delta in Quill's native shape (ops
    # without formatting omit the ``attributes`` key entirely).
    delta = data.content_delta.model_dump(exclude_none=True)
    existing = _get_description(db, circle_id, local_date, host_user_id)
    if existing:
        existing.content_delta = delta
        existing.updated_by_user_id = editor_id
        existing.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(existing)
        return existing

    desc = DayDescription(
        circle_id=circle_id,
        local_date=local_date,
        host_user_id=host_user_id,
        content_delta=delta,
        updated_by_user_id=editor_id,
    )
    db.add(desc)
    db.commit()
    db.refresh(desc)
    return desc


def _delete_description(
    db: Session,
    circle_id: uuid.UUID,
    local_date: date,
    host_user_id: uuid.UUID | None,
) -> None:
    existing = _get_description(db, circle_id, local_date, host_user_id)
    if existing:
        db.delete(existing)
        db.commit()


def _hosting_user_ids(
    db: Session, circle_id: uuid.UUID, local_date: date
) -> set[uuid.UUID]:
    """Return the user ids hosting *local_date* in *circle_id*."""
    rows = db.execute(
        select(DayAvailability.user_id).where(
            DayAvailability.circle_id == circle_id,
            DayAvailability.local_date == local_date,
            DayAvailability.state == AvailabilityState.hosting,
        )
    ).scalars()
    return set(rows)


def _require_hosting(
    db: Session,
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    local_date: date,
) -> None:
    """Reject with 403 if *user_id* is not hosting *local_date*."""
    if user_id not in _hosting_user_ids(db, circle_id, local_date):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hosts may set a host description",
        )


# ---------------------------------------------------------------------------
# Read (any member)
# ---------------------------------------------------------------------------


@router.get(
    "/circles/{circle_id}/day-description/{local_date}",
    response_model=DayDescriptionBundle,
)
def get_day_descriptions(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DayDescriptionBundle:
    """
    Return the circle-wide description and the per-host descriptions of
    members currently hosting *local_date*. Any circle member may read.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)

    circle_wide = _get_description(db, circle_id, local_date, None)

    hosting_ids = _hosting_user_ids(db, circle_id, local_date)
    per_host_rows = (
        db.execute(
            select(DayDescription).where(
                DayDescription.circle_id == circle_id,
                DayDescription.local_date == local_date,
                DayDescription.host_user_id.is_not(None),
            )
        )
        .scalars()
        .all()
    )
    per_host = [
        _enrich(d, db) for d in per_host_rows if d.host_user_id in hosting_ids
    ]
    return DayDescriptionBundle(
        circle_wide=_enrich(circle_wide, db) if circle_wide else None,
        per_host=per_host,
    )


# ---------------------------------------------------------------------------
# Circle-wide description (owner / admin)
# ---------------------------------------------------------------------------


@router.put(
    "/circles/{circle_id}/day-description/{local_date}",
    response_model=DayDescriptionOut,
)
def set_circle_description(
    circle_id: uuid.UUID,
    local_date: date,
    body: DayDescriptionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DayDescriptionOut:
    """
    Create or replace the circle-wide description for *local_date*.
    Requires owner or admin role.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)
    desc = _upsert_description(
        db, circle_id, local_date, None, body, current_user.id
    )
    return _enrich(desc, db)


@router.delete(
    "/circles/{circle_id}/day-description/{local_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_circle_description(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete the circle-wide description for *local_date*. Requires owner
    or admin role. No-op if none exists.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)
    _delete_description(db, circle_id, local_date, None)


# ---------------------------------------------------------------------------
# Per-host description — own (the hosting member)
# ---------------------------------------------------------------------------


@router.put(
    "/circles/{circle_id}/day-description/{local_date}/hosts/me",
    response_model=DayDescriptionOut,
)
def set_own_host_description(
    circle_id: uuid.UUID,
    local_date: date,
    body: DayDescriptionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DayDescriptionOut:
    """
    Create or replace the calling member's own host description for
    *local_date*. The caller must be hosting that day.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    _require_hosting(db, circle_id, current_user.id, local_date)
    desc = _upsert_description(
        db, circle_id, local_date, current_user.id, body, current_user.id
    )
    return _enrich(desc, db)


@router.delete(
    "/circles/{circle_id}/day-description/{local_date}/hosts/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_own_host_description(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete the calling member's own host description for *local_date*.
    No-op if none exists.
    """
    get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    _delete_description(db, circle_id, local_date, current_user.id)


# ---------------------------------------------------------------------------
# Per-host description — override (owner / admin)
# ---------------------------------------------------------------------------


@router.put(
    "/circles/{circle_id}/day-description/{local_date}/hosts/{user_id}",
    response_model=DayDescriptionOut,
)
def set_member_host_description(
    circle_id: uuid.UUID,
    local_date: date,
    user_id: uuid.UUID,
    body: DayDescriptionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DayDescriptionOut:
    """
    Create or replace a specific host's description for *local_date*.
    Requires owner or admin role; the target must be hosting that day.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)
    _require_hosting(db, circle_id, user_id, local_date)
    desc = _upsert_description(
        db, circle_id, local_date, user_id, body, current_user.id
    )
    return _enrich(desc, db)


@router.delete(
    "/circles/{circle_id}/day-description/{local_date}/hosts/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_member_host_description(
    circle_id: uuid.UUID,
    local_date: date,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete a specific host's description for *local_date*. Requires
    owner or admin role. No-op if none exists.
    """
    get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)
    _delete_description(db, circle_id, local_date, user_id)
