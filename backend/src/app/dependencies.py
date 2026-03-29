"""FastAPI dependencies for authentication and database access."""

from __future__ import annotations

import logging
import uuid
from datetime import date

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.jwks import get_jwks_client
from app.config import Settings, get_settings
from app.database import get_db  # noqa: F401 — re-exported for routers
from app.models.auth_identity import AuthIdentity
from app.models.circle import Circle
from app.models.membership import CircleMembership, MemberRole
from app.models.user import User

bearer = HTTPBearer()
LOG = logging.getLogger(__name__)


def _decode_dev_token(
    token: str,
    settings: Settings,
) -> dict:
    """
    Decode a self-minted HS256 dev token.

    Used only when ``DEV_SHARED_SECRET`` is configured.
    Production deployments must never set that variable.

    :param token: Raw bearer token string.
    :param settings: Application settings.
    :returns: Decoded JWT payload.
    :raises jwt.InvalidTokenError: When the token is invalid.
    """
    return jwt.decode(
        token,
        settings.DEV_SHARED_SECRET,  # type: ignore[arg-type]
        algorithms=["HS256"],
        audience=settings.OIDC_AUDIENCE,
        issuer=settings.OIDC_ISSUER,
    )


def _decode_oidc_token(
    token: str,
    settings: Settings,
) -> dict:
    """
    Decode a Keycloak-issued RS256 token via JWKS.

    :param token: Raw bearer token string.
    :param settings: Application settings.
    :returns: Decoded JWT payload.
    :raises jwt.InvalidTokenError: When the token is invalid.
    """
    jwks_client = get_jwks_client(settings.OIDC_AUTHORITY)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.OIDC_AUDIENCE,
        issuer=settings.OIDC_ISSUER,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the bearer token and return the local User.

    When ``DEV_SHARED_SECRET`` is set the token is validated as a
    self-minted HS256 JWT (no Keycloak required).  Otherwise the
    token is validated against the Keycloak JWKS endpoint.

    :param credentials: Authorization header bearer token.
    :param settings: Application configuration.
    :param db: Database session.
    :returns: Local User record for the authenticated identity.
    :raises HTTPException: 401 when the token is missing, expired,
        has the wrong audience/issuer, or has a tampered signature.
    """
    token = credentials.credentials
    try:
        if settings.DEV_SHARED_SECRET is not None:
            payload: dict = _decode_dev_token(token, settings)
        else:
            payload = _decode_oidc_token(token, settings)
    except jwt.ExpiredSignatureError:
        LOG.debug("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        LOG.debug("Invalid token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    subject: str = payload["sub"]
    provider: str = settings.OIDC_ISSUER
    email: str = payload.get("email", "")
    display_name: str | None = payload.get("name")

    identity = db.execute(
        select(AuthIdentity).where(
            AuthIdentity.provider == provider,
            AuthIdentity.subject == subject,
        )
    ).scalar_one_or_none()

    if identity is not None:
        return identity.user

    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    if user is None:
        user = User(email=email, display_name=display_name)
        db.add(user)
        db.flush()

    identity = AuthIdentity(
        user_id=user.id,
        provider=provider,
        subject=subject,
    )
    db.add(identity)
    db.commit()
    db.refresh(user)
    return user


def get_circle_or_404(
    db: Session,
    circle_id: uuid.UUID,
) -> Circle:
    """
    Return the circle, or raise HTTP 404 when it does not exist.

    :param db: Database session.
    :param circle_id: Circle identifier.
    :returns: Existing Circle model.
    :raises HTTPException: 404 when circle is not found.
    """
    circle = db.execute(
        select(Circle).where(Circle.id == circle_id)
    ).scalar_one_or_none()
    if circle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found",
        )
    return circle


def get_membership_or_403(
    db: Session,
    circle_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CircleMembership:
    """
    Return membership for a user in a circle, or raise HTTP 403.

    :param db: Database session.
    :param circle_id: Circle identifier.
    :param user_id: User identifier.
    :returns: Existing CircleMembership model.
    :raises HTTPException: 403 when user is not a circle member.
    """
    membership = db.execute(
        select(CircleMembership).where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this circle",
        )
    return membership


def require_admin_or_owner(
    membership: CircleMembership,
) -> CircleMembership:
    """
    Ensure membership has admin/owner role, else raise HTTP 403.

    :param membership: Membership to check.
    :returns: The same membership when authorized.
    :raises HTTPException: 403 when role is insufficient.
    """
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required",
        )
    return membership


def require_owner(
    membership: CircleMembership,
) -> CircleMembership:
    """
    Ensure membership has owner role, else raise HTTP 403.

    :param membership: Membership to check.
    :returns: The same membership when authorized.
    :raises HTTPException: 403 when role is not owner.
    """
    if membership.role != MemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner role required",
        )
    return membership


def validate_date_range(start_date: date, end_date: date) -> None:
    """
    Validate that an API date range is ordered.

    :param start_date: Inclusive range start.
    :param end_date: Inclusive range end.
    :raises HTTPException: 400 when start_date is after end_date.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be less than or equal to end_date",
        )


# Alias for existing routers. The previous is_active check is no
# longer needed because the users table has no is_active column;
# OIDC-authenticated users are always considered active.
get_current_active_user = get_current_user

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_circle_or_404",
    "get_membership_or_403",
    "require_admin_or_owner",
    "require_owner",
    "validate_date_range",
    "bearer",
]
