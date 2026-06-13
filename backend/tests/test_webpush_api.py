"""Integration tests for the Web Push subscription endpoints."""

from __future__ import annotations

from urllib.parse import quote

from fastapi.testclient import TestClient


def _sub_payload(endpoint: str) -> dict:
    """Return a browser-style PushSubscription payload."""
    return {
        "endpoint": endpoint,
        "keys": {"p256dh": "key-data", "auth": "auth-data"},
    }


def test_webpush_key_null_when_unconfigured(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure the key endpoint returns null when VAPID is unset."""
    response = client.get("/notifications/webpush/key", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"vapid_public_key": None}


def test_subscribe_and_unsubscribe_roundtrip(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure a subscription can be registered then removed."""
    endpoint = "https://push.example/abc"
    create = client.post(
        "/notifications/webpush/subscriptions",
        json=_sub_payload(endpoint),
        headers=auth_headers,
    )
    assert create.status_code == 201

    # Re-registering the same endpoint is idempotent (no 500).
    again = client.post(
        "/notifications/webpush/subscriptions",
        json=_sub_payload(endpoint),
        headers=auth_headers,
    )
    assert again.status_code == 201

    remove = client.delete(
        f"/notifications/webpush/subscriptions?endpoint={quote(endpoint)}",
        headers=auth_headers,
    )
    assert remove.status_code == 204


def test_subscribe_requires_auth(client: TestClient) -> None:
    """Ensure registering a subscription requires authentication."""
    response = client.post(
        "/notifications/webpush/subscriptions",
        json=_sub_payload("https://push.example/x"),
    )
    assert response.status_code in (401, 403)
