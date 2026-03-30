"""Tests for API-layer token and range validation dependencies."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

import jwt
import pytest
from fastapi import HTTPException

from app.config import Settings
from app.dependencies import (
    _decode_dev_token,
    _select_token_validation_mode,
    validate_date_range,
)


def _settings() -> Settings:
    """Return minimal settings needed by dependency helpers."""
    secret = "dev-secret-with-at-least-thirty-two-chars"
    return cast(
        Settings,
        SimpleNamespace(
            DEV_SHARED_SECRET=secret,
            OIDC_AUDIENCE="meepletime-backend",
            OIDC_ISSUER="https://keycloak.example/realms/meepletime",
        ),
    )


def _token_payload(**overrides: object) -> dict[str, object]:
    """Return a baseline JWT payload with optional field overrides."""
    now = datetime.now(tz=UTC)
    payload: dict[str, object] = {
        "sub": "user-123",
        "aud": "meepletime-backend",
        "iss": "https://keycloak.example/realms/meepletime",
        "exp": int((now + timedelta(minutes=10)).timestamp()),
    }
    payload.update(overrides)
    return payload


def _sign(
    payload: dict[str, object],
    secret: str = "dev-secret-with-at-least-thirty-two-chars",
) -> str:
    """Return an HS256 JWT for the provided payload."""
    return jwt.encode(payload, secret, algorithm="HS256")


def _unsigned_token(algorithm: str) -> str:
    """Return a JWT-shaped string with the requested alg header."""
    header = (
        base64.urlsafe_b64encode(
            json.dumps({"alg": algorithm, "typ": "JWT"}).encode()
        )
        .decode()
        .rstrip("=")
    )
    payload = base64.urlsafe_b64encode(b"{}")
    signature = base64.urlsafe_b64encode(b"sig").decode().rstrip("=")
    return f"{header}.{payload.decode().rstrip('=')}.{signature}"


def test_decode_dev_token_valid_token() -> None:
    """Ensure valid HS256 dev token decodes and returns claims."""
    token = _sign(_token_payload())

    payload = _decode_dev_token(token, _settings())

    assert payload["sub"] == "user-123"
    assert payload["aud"] == "meepletime-backend"


def test_decode_dev_token_expired_token() -> None:
    """Ensure expired HS256 dev token raises ExpiredSignatureError."""
    token = _sign(
        _token_payload(
            exp=int((datetime.now(tz=UTC) - timedelta(minutes=1)).timestamp())
        )
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        _decode_dev_token(token, _settings())


def test_decode_dev_token_wrong_audience() -> None:
    """Ensure wrong audience raises InvalidAudienceError."""
    token = _sign(_token_payload(aud="different-audience"))

    with pytest.raises(jwt.InvalidAudienceError):
        _decode_dev_token(token, _settings())


def test_decode_dev_token_wrong_issuer() -> None:
    """Ensure wrong issuer raises InvalidIssuerError."""
    token = _sign(_token_payload(iss="https://wrong-issuer.example"))

    with pytest.raises(jwt.InvalidIssuerError):
        _decode_dev_token(token, _settings())


def test_decode_dev_token_tampered_signature() -> None:
    """Ensure tampered signature raises InvalidSignatureError."""
    token = _sign(_token_payload())
    header, payload, signature = token.split(".")
    tampered_signature = ("a" if signature[0] != "a" else "b") + signature[1:]
    tampered = ".".join([header, payload, tampered_signature])

    with pytest.raises(jwt.InvalidSignatureError):
        _decode_dev_token(tampered, _settings())


def test_select_validation_mode_prefers_dev_for_hs256() -> None:
    """Ensure HS256 headers select the dev shared-secret path."""
    token = _sign(_token_payload())

    mode = _select_token_validation_mode(token, _settings())

    assert mode == "dev-shared-secret"


def test_select_validation_mode_prefers_oidc_for_rs256() -> None:
    """Ensure RS256 headers select the OIDC JWKS validation path."""
    token = _unsigned_token("RS256")

    mode = _select_token_validation_mode(token, _settings())

    assert mode == "oidc-jwks"


def test_select_validation_mode_rejects_hs256_without_secret() -> None:
    """Ensure HS256 tokens fail fast when dev-token support is off."""
    token = _sign(_token_payload())
    settings = cast(
        Settings,
        SimpleNamespace(
            DEV_SHARED_SECRET=None,
            OIDC_AUDIENCE="meepletime-backend",
            OIDC_ISSUER="https://keycloak.example/realms/meepletime",
        ),
    )

    with pytest.raises(jwt.InvalidTokenError):
        _select_token_validation_mode(token, settings)


def test_select_validation_mode_rejects_unknown_algorithm() -> None:
    """Ensure unsupported JWT algorithms are rejected clearly."""
    token = _unsigned_token("HS384")

    with pytest.raises(jwt.InvalidTokenError):
        _select_token_validation_mode(token, _settings())


def test_validate_date_range_rejects_inverted_range() -> None:
    """Ensure start_date after end_date is rejected with HTTP 400."""
    with pytest.raises(HTTPException) as exc:
        validate_date_range(
            start_date=datetime(2026, 3, 30, tzinfo=UTC).date(),
            end_date=datetime(2026, 3, 29, tzinfo=UTC).date(),
        )

    assert exc.value.status_code == 400


def test_validate_date_range_accepts_ordered_range() -> None:
    """Ensure ordered date range passes without raising."""
    validate_date_range(
        start_date=datetime(2026, 3, 29, tzinfo=UTC).date(),
        end_date=datetime(2026, 3, 30, tzinfo=UTC).date(),
    )
