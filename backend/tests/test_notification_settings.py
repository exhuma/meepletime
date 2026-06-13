"""Integration tests for the /notifications/settings endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_settings_returns_defaults(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure first GET creates defaults: email on, others off."""
    response = client.get("/notifications/settings", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "email_enabled": True,
        "webpush_enabled": False,
        "telegram_dm_enabled": False,
    }


def test_put_settings_updates_only_given_fields(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure PUT changes only the provided flags."""
    client.get("/notifications/settings", headers=auth_headers)
    response = client.put(
        "/notifications/settings",
        json={"email_enabled": False, "webpush_enabled": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email_enabled"] is False
    assert body["webpush_enabled"] is True
    assert body["telegram_dm_enabled"] is False


def test_settings_are_per_user(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure one user's settings do not affect another's."""
    client.put(
        "/notifications/settings",
        json={"email_enabled": False},
        headers=auth_headers,
    )
    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-b', email='b@x.test')}"
        )
    }
    response = client.get("/notifications/settings", headers=other)
    assert response.status_code == 200
    assert response.json()["email_enabled"] is True
