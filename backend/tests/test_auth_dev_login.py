"""Tests for the development-only in-app login endpoint.

These exercise the ``/auth/dev/login`` route that is mounted only when
``DEV_AUTH_ENABLED`` is true. The minted tokens must pass through the
*real* token validator, so the round-trip via ``GET /auth/me`` is the
key assertion (proving this is not a parallel bypass). The endpoint
takes the identity directly and knows nothing about named presets.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth.dev_token import mint_dev_token
from app.config import Settings, get_settings
from app.database import get_db
from app.main import create_app


def test_dev_login_default_identity(client: TestClient) -> None:
    """A bare request mints a token for the default dev identity."""
    resp = client.post("/auth/dev/login", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "dev-agent@meepletime.local"


def test_dev_login_custom_identity(client: TestClient) -> None:
    """The supplied identity flows through to the provisioned user."""
    identity = {
        "sub": "dev-owner",
        "email": "dev-owner@meepletime.local",
        "name": "Dev Owner",
    }
    resp = client.post("/auth/dev/login", json=identity)
    assert resp.status_code == 200

    token = resp.json()["access_token"]
    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    profile = me.json()
    assert profile["email"] == "dev-owner@meepletime.local"
    assert profile["display_name"] == "Dev Owner"


def test_dev_login_disabled_returns_404(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The router is absent when DEV_AUTH_ENABLED is false.

    The mount decision is taken inside ``create_app()`` from the
    cached ``get_settings()``, so the flag must be cleared in the
    environment (not via ``dependency_overrides``) before building
    the app.
    """
    monkeypatch.setenv("MEEPLETIME_DEV_AUTH_ENABLED", "false")
    get_settings.cache_clear()
    try:
        app = create_app()

        def _override_get_db() -> Generator[Session, None, None]:
            yield db_session

        app.dependency_overrides[get_db] = _override_get_db
        with TestClient(app) as test_client:
            resp = test_client.post("/auth/dev/login", json={})
            assert resp.status_code == 404
    finally:
        # Restore the cache so later tests see the enabled flag.
        get_settings.cache_clear()


def test_config_rejects_dev_auth_without_secret() -> None:
    """Enabling dev auth without a signing secret fails fast."""
    with pytest.raises(ValidationError):
        Settings(DEV_AUTH_ENABLED=True, DEV_SHARED_SECRET=None)


def test_mint_dev_token_claims() -> None:
    """The shared mint helper sets the expected claims."""
    import jwt

    token = mint_dev_token(
        sub="dev-owner",
        email="dev-owner@meepletime.local",
        name="Dev Owner",
        secret="a-secret-with-at-least-thirty-two-chars!",
        issuer="https://keycloak.test/realms/meepletime",
        audience="meepletime-backend",
        ttl_seconds=60,
    )
    payload = jwt.decode(
        token,
        "a-secret-with-at-least-thirty-two-chars!",
        algorithms=["HS256"],
        audience="meepletime-backend",
        issuer="https://keycloak.test/realms/meepletime",
    )
    assert payload["sub"] == "dev-owner"
    assert payload["email"] == "dev-owner@meepletime.local"
    assert payload["name"] == "Dev Owner"
    assert payload["exp"] > payload["iat"]
