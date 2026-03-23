"""FastAPI dependencies for authentication and database access."""
from __future__ import annotations

import logging
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
from app.models.user import User

bearer = HTTPBearer()
LOG = logging.getLogger(__name__)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the OIDC bearer token and return the local User.

    Decodes the access token using the Keycloak JWKS endpoint,
    then finds or creates the corresponding User and AuthIdentity
    rows.  The first successful call for a new identity provisions
    the local user account.

    :param credentials: Authorization header bearer token.
    :param settings: Application configuration.
    :param db: Database session.
    :returns: Local User record for the authenticated identity.
    :raises HTTPException: 401 when the token is missing, expired,
        has the wrong audience/issuer, or has a tampered signature.
    """
    token = credentials.credentials
    jwks_client = get_jwks_client(settings.OIDC_AUTHORITY)
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload: dict = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.OIDC_AUDIENCE,
            issuer=settings.OIDC_ISSUER,
        )
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


# Alias for existing routers. The previous is_active check is no
# longer needed because the users table has no is_active column;
# OIDC-authenticated users are always considered active.
get_current_active_user = get_current_user

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "bearer",
]
