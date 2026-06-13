"""Tests for application settings loading and derivation."""

from __future__ import annotations

import pytest

from app.config import Settings

_AUTHORITY = "https://keycloak.example/realms/meepletime"
_PUBLIC_ISSUER = "https://public.example/realms/meepletime"


def _base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the minimum required MEEPLETIME_* env vars, clear issuer."""
    monkeypatch.setenv(
        "MEEPLETIME_DATABASE_URL",
        "postgresql://u:p@h:5432/d",
    )
    monkeypatch.setenv("MEEPLETIME_OIDC_AUTHORITY", _AUTHORITY)
    monkeypatch.setenv("MEEPLETIME_OIDC_AUDIENCE", "meepletime-backend")
    monkeypatch.delenv("MEEPLETIME_OIDC_ISSUER", raising=False)


def test_issuer_defaults_to_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OIDC_ISSUER falls back to OIDC_AUTHORITY when unset."""
    _base_env(monkeypatch)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.OIDC_ISSUER == _AUTHORITY


def test_issuer_override_is_respected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit OIDC_ISSUER overrides the authority fallback."""
    _base_env(monkeypatch)
    monkeypatch.setenv("MEEPLETIME_OIDC_ISSUER", _PUBLIC_ISSUER)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.OIDC_ISSUER == _PUBLIC_ISSUER
    assert settings.OIDC_AUTHORITY == _AUTHORITY
