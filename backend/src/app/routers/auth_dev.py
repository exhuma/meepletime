"""Development-only in-app login endpoint.

Mounted by :func:`app.main.create_app` **only when**
``DEV_AUTH_ENABLED`` is true, letting the SPA authenticate without a
running Keycloak. It mints a real HS256 dev token — the HTTP
equivalent of ``scripts/dev_token.py`` — for whatever identity the
caller supplies, after which the standard token-validation and
user-provisioning path takes over. This is not an auth bypass.

**Development and headless-agent use only. Never enable in
production.**

The endpoint takes the identity (``sub``/``email``/``name``)
directly; it deliberately knows nothing about named "preset" dev
users. Presets are a developer convenience documented in
``docs/developer/auth.md`` and offered by the dev-only frontend
picker — never enumerated or hardcoded on the API, so they cannot
leak from a deployed instance.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dev_token import DEFAULT_TTL_SECONDS, mint_dev_token
from app.config import Settings, get_settings

router = APIRouter(prefix="/auth/dev", tags=["auth-dev"])


class DevLoginRequest(BaseModel):
    """Identity claims to mint a dev token for.

    All fields default to a generic dev identity so a bare request
    behaves like ``task dev:token`` with no arguments.
    """

    sub: str = "dev-agent"
    email: str = "dev-agent@meepletime.local"
    name: str = "Dev Agent"


class DevLoginResponse(BaseModel):
    """Minted dev token returned to the caller."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=DevLoginResponse)
def dev_login(
    body: DevLoginRequest,
    settings: Settings = Depends(get_settings),
) -> DevLoginResponse:
    """
    Mint an HS256 dev token for the supplied identity.

    The token's ``iss``/``aud`` come from settings, so it is
    accepted by the standard dev-token validator without any
    special-casing.

    :param body: Identity claims to embed in the token.
    :param settings: Application settings (provides the signing
        secret, issuer, and audience).
    :returns: The minted access token and its lifetime.
    """
    token = mint_dev_token(
        sub=body.sub,
        email=body.email,
        name=body.name,
        secret=settings.DEV_SHARED_SECRET,  # type: ignore[arg-type]
        issuer=settings.OIDC_ISSUER,  # type: ignore[arg-type]
        audience=settings.OIDC_AUDIENCE,
        ttl_seconds=DEFAULT_TTL_SECONDS,
    )
    return DevLoginResponse(
        access_token=token,
        expires_in=DEFAULT_TTL_SECONDS,
    )
