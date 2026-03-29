"""Circles router: circle creation and management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_db
from app.models.circle import Circle
from app.models.membership import CircleMembership, MemberRole
from app.models.user import User
from app.schemas.circle import CircleCreate, CircleOut, CircleUpdate
from app.schemas.membership import InviteJoin, MembershipOut

router = APIRouter(tags=["circles"])


def _get_membership(
    db: Session, circle_id: uuid.UUID, user_id: uuid.UUID
) -> CircleMembership | None:
    """Return the CircleMembership for *user_id* in *circle_id*, or None."""
    return db.execute(
        select(CircleMembership).where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == user_id,
        )
    ).scalar_one_or_none()


def _require_membership(
    db: Session, circle_id: uuid.UUID, user_id: uuid.UUID
) -> CircleMembership:
    """
    Return the membership or raise HTTP 403 if *user_id* is not a member of
    *circle_id*.
    """
    membership = _get_membership(db, circle_id, user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this circle",
        )
    return membership


def _require_admin(membership: CircleMembership) -> None:
    """Raise HTTP 403 if *membership* does not have owner or admin role."""
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required",
        )


def _require_owner(membership: CircleMembership) -> None:
    """Raise HTTP 403 if *membership* does not have owner role."""
    if membership.role != MemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required"
        )


@router.get("/circles", response_model=list[CircleOut])
def list_circles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Circle]:
    """Return all circles that the authenticated user belongs to."""
    memberships = db.execute(
        select(CircleMembership).where(
            CircleMembership.user_id == current_user.id
        )
    ).scalars().all()
    circle_ids = [m.circle_id for m in memberships]
    return list(
        db.execute(
            select(Circle).where(Circle.id.in_(circle_ids))
        ).scalars().all()
    )


@router.post(
    "/circles", response_model=CircleOut, status_code=status.HTTP_201_CREATED
)
def create_circle(
    circle_in: CircleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """Create a new circle and automatically join the creator as owner."""
    circle = Circle(
        **circle_in.model_dump(),
        created_by_user_id=current_user.id,
    )
    db.add(circle)
    db.flush()

    membership = CircleMembership(
        circle_id=circle.id,
        user_id=current_user.id,
        pseudonym=current_user.email.split("@")[0],
        role=MemberRole.owner,
    )
    db.add(membership)
    db.commit()
    db.refresh(circle)
    return circle


@router.get("/circles/{circle_id}", response_model=CircleOut)
def get_circle(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """Return a single circle by ID. The caller must be a member."""
    circle = db.execute(
        select(Circle).where(Circle.id == circle_id)
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found"
        )
    _require_membership(db, circle_id, current_user.id)
    return circle


@router.patch("/circles/{circle_id}", response_model=CircleOut)
def update_circle(
    circle_id: uuid.UUID,
    circle_in: CircleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """Update circle settings. Requires owner or admin role."""
    circle = db.execute(
        select(Circle).where(Circle.id == circle_id)
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found"
        )
    membership = _require_membership(db, circle_id, current_user.id)
    _require_admin(membership)

    update_data = circle_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(circle, field, value)

    db.commit()
    db.refresh(circle)
    return circle


@router.delete("/circles/{circle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_circle(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Permanently delete a circle. Requires owner role."""
    circle = db.execute(
        select(Circle).where(Circle.id == circle_id)
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found"
        )
    membership = _require_membership(db, circle_id, current_user.id)
    _require_owner(membership)
    db.delete(circle)
    db.commit()


@router.post("/circles/{circle_id}/invite", response_model=CircleOut)
def regenerate_invite(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """
    Generate a new invite token for *circle_id*, invalidating the
    previous one. Requires owner or admin role.
    """
    circle = db.execute(
        select(Circle).where(Circle.id == circle_id)
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found"
        )
    membership = _require_membership(db, circle_id, current_user.id)
    _require_admin(membership)
    circle.invite_token = uuid.uuid4()
    db.commit()
    db.refresh(circle)
    return circle


@router.get("/circles/join/{invite_token}", response_model=CircleOut)
def preview_circle_by_invite(
    invite_token: uuid.UUID,
    db: Session = Depends(get_db),
) -> Circle:
    """
    Return public circle details for a valid *invite_token* without
    requiring authentication.
    """
    circle = db.execute(
        select(Circle).where(Circle.invite_token == invite_token)
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token"
        )
    return circle


@router.post(
    "/circles/join",
    response_model=MembershipOut,
    status_code=status.HTTP_201_CREATED,
)
def join_circle(
    join_in: InviteJoin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CircleMembership:
    """Join a circle using an invite token and choose a per-circle pseudonym."""
    circle = db.execute(
        select(Circle).where(Circle.invite_token == join_in.invite_token)
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token"
        )

    existing = _get_membership(db, circle.id, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member"
        )

    # Check pseudonym uniqueness within the circle
    pseudonym_taken = db.execute(
        select(CircleMembership).where(
            CircleMembership.circle_id == circle.id,
            CircleMembership.pseudonym == join_in.pseudonym,
        )
    ).scalar_one_or_none()
    if pseudonym_taken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pseudonym already taken in this circle",
        )

    membership = CircleMembership(
        circle_id=circle.id,
        user_id=current_user.id,
        pseudonym=join_in.pseudonym,
        role=MemberRole.member,
        can_host_default=join_in.can_host_default,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
