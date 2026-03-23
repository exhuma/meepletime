"""Authentication router: user profile endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """
    Return the authenticated user's profile.

    The OIDC bearer token is validated on each call;
    the local user account is provisioned on first access.

    :param current_user: Resolved local user from OIDC token.
    :returns: UserOut schema for the authenticated user.
    """
    return current_user
