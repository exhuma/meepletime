"""Helper for minting self-signed HS256 development JWTs.

Shared by the dev-login endpoints (:mod:`app.routers.auth_dev`) and
the ``dev_token`` CLI script so both produce an identical token
shape. **Development and headless-agent use only — never enabled in
production.**
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

DEFAULT_TTL_SECONDS = 365 * 24 * 3600


def mint_dev_token(
    *,
    sub: str,
    email: str,
    name: str,
    secret: str,
    issuer: str,
    audience: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> str:
    """
    Mint a self-signed HS256 JWT accepted by the dev-token path.

    The claim shape matches what ``_decode_dev_token`` validates in
    :mod:`app.dependencies` (``iss``/``aud``/``sub``/``email``/
    ``name``/``iat``/``exp``), so the minted token flows through the
    existing validator and user-provisioning logic unchanged.

    :param sub: Subject claim (stable per dev identity).
    :param email: Email claim.
    :param name: Display-name claim.
    :param secret: HS256 signing secret (``DEV_SHARED_SECRET``).
    :param issuer: ``iss`` claim (``OIDC_ISSUER``).
    :param audience: ``aud`` claim (``OIDC_AUDIENCE``).
    :param ttl_seconds: Token lifetime in seconds.
    :returns: Encoded HS256 JWT string.
    """
    now = datetime.now(tz=UTC)
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": sub,
        "email": email,
        "name": name,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(payload, secret, algorithm="HS256")
