"""Integration tests for the test-notification endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.notifications import test_delivery as td


def test_user_test_email_unconfigured(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure the email test reports unconfigured without sending."""
    resp = client.post(
        "/notifications/test",
        json={"channel": "email"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "configured" in body["message"].lower()


def test_user_test_telegram_no_link(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure the Telegram DM test reports no linked chats."""
    resp = client.post(
        "/notifications/test",
        json={"channel": "telegram"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is False


def test_user_test_requires_auth(client: TestClient) -> None:
    """Ensure the test endpoint requires authentication."""
    resp = client.post("/notifications/test", json={"channel": "email"})
    assert resp.status_code in (401, 403)


def test_circle_group_test_sends(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    """Ensure an admin can test a configured group bot."""
    circle_id = client.post(
        "/circles",
        json={"name": "T", "timezone": "UTC"},
        headers=auth_headers,
    ).json()["id"]
    config_id = client.post(
        f"/circles/{circle_id}/telegram",
        json={
            "label": "G",
            "bot_token": "secret-token-1234",
            "group_chat_id": "-100",
        },
        headers=auth_headers,
    ).json()["id"]

    monkeypatch.setattr(td, "send_message", lambda *a, **k: None)
    resp = client.post(
        f"/circles/{circle_id}/telegram/{config_id}/test",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_circle_test_non_member_forbidden(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a non-member cannot test a circle's bot."""
    circle_id = client.post(
        "/circles",
        json={"name": "T", "timezone": "UTC"},
        headers=auth_headers,
    ).json()["id"]
    config_id = client.post(
        f"/circles/{circle_id}/telegram",
        json={"label": "G", "bot_token": "secret-token-1234"},
        headers=auth_headers,
    ).json()["id"]

    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-q', email='q@x.test')}"
        )
    }
    resp = client.post(
        f"/circles/{circle_id}/telegram/{config_id}/test",
        headers=other,
    )
    assert resp.status_code == 403
