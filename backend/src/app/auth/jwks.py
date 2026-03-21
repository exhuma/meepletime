"""JWKS client factory for OIDC token validation."""
from __future__ import annotations

from functools import lru_cache

import httpx
import jwt


@lru_cache(maxsize=8)
def get_jwks_client(authority: str) -> jwt.PyJWKClient:
    """
    Return a cached JWKS client for the given OIDC authority.

    Resolves the JWKS URI from the OIDC discovery document
    so that hard-coded URIs are never needed.

    :param authority: OIDC issuer base URL.
    :returns: Configured PyJWKClient with automatic key refresh.
    """
    discovery_url = (
        f"{authority.rstrip('/')}"
        "/.well-known/openid-configuration"
    )
    with httpx.Client() as client:
        doc = (
            client.get(discovery_url)
            .raise_for_status()
            .json()
        )
    return jwt.PyJWKClient(doc["jwks_uri"])
