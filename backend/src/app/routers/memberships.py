"""Memberships router: circle membership management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import (
    get_current_active_user,
    get_db,
    get_membership_or_403,
)
from app.models.membership import CircleMembership, MemberRole
from app.models.user import User
from app.schemas.membership import MembershipOut, MembershipUpdate
from app.utils import apply_partial_update

router = APIRouter(tags=["memberships"])


@router.get("/circles/{circle_id}/members", response_model=list[MembershipOut])
def list_members(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CircleMembership]:
    """Return all members of *circle_id*. The caller must be a member."""
    get_membership_or_403(db, circle_id, current_user.id)
    return list(
        db.execute(
            select(CircleMembership).where(
                CircleMembership.circle_id == circle_id
            )
        )
        .scalars()
        .all()
    )


@router.patch(
    "/circles/{circle_id}/members/{user_id}", response_model=MembershipOut
)
def update_membership(
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    update_in: MembershipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CircleMembership:
    """
    Update a membership's pseudonym, role, or host default.
    Owner/admin may update any member; a member may update their
    own record.
    """
    requester = get_membership_or_403(db, circle_id, current_user.id)
    target = db.execute(
        select(CircleMembership).where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    is_self = current_user.id == user_id
    is_admin = requester.role in (MemberRole.owner, MemberRole.admin)

    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    # Only owner/admin may change roles
    if update_in.role is not None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner/admin can change roles",
        )

    update_data = update_in.model_dump(exclude_unset=True)

    if "pseudonym" in update_data:
        pseudonym_taken = db.execute(
            select(CircleMembership).where(
                CircleMembership.circle_id == circle_id,
                CircleMembership.pseudonym == update_data["pseudonym"],
                CircleMembership.id != target.id,
            )
        ).scalar_one_or_none()
        if pseudonym_taken:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pseudonym already taken",
            )

    apply_partial_update(target, update_data)

    db.commit()
    db.refresh(target)
    return target


@router.delete(
    "/circles/{circle_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Remove a member from a circle. A member may leave themselves;
    owner/admin may remove others.
    """
    requester = get_membership_or_403(db, circle_id, current_user.id)
    target = db.execute(
        select(CircleMembership).where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    is_self = current_user.id == user_id
    is_admin = requester.role in (MemberRole.owner, MemberRole.admin)

    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    # Prevent removing the sole owner
    if target.role == MemberRole.owner:
        owner_count = db.execute(
            select(func.count())
            .select_from(CircleMembership)
            .where(
                CircleMembership.circle_id == circle_id,
                CircleMembership.role == MemberRole.owner,
            )
        ).scalar()
        if (owner_count or 0) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the only owner",
            )

    db.delete(target)
    db.commit()
