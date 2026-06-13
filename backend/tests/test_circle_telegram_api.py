"""Integration tests for circle Telegram configuration endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.routers import circle_telegram


def _make_circle(client: TestClient, headers: dict[str, str]) -> str:
    """Create a circle and return its id (caller becomes owner)."""
    resp = client.post(
        "/circles",
        json={"name": "Bots", "timezone": "UTC"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_lists_and_masks_token(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure a created bot config never leaks the raw token."""
    circle_id = _make_circle(client, auth_headers)
    create = client.post(
        f"/circles/{circle_id}/telegram",
        json={"label": "Group", "bot_token": "secret-token-1234"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    body = create.json()
    assert "bot_token" not in body
    assert body["token_hint"] == "…1234"
    assert body["mode"] == "group"

    listing = client.get(f"/circles/{circle_id}/telegram", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()[0]["token_hint"] == "…1234"


def test_non_admin_cannot_list(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a non-member cannot read a circle's Telegram config."""
    circle_id = _make_circle(client, auth_headers)
    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-b', email='b@x.test')}"
        )
    }
    resp = client.get(f"/circles/{circle_id}/telegram", headers=other)
    assert resp.status_code == 403


def test_update_sets_group_chat_id(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure PUT can attach a detected group chat id."""
    circle_id = _make_circle(client, auth_headers)
    config_id = client.post(
        f"/circles/{circle_id}/telegram",
        json={"label": "Group", "bot_token": "secret-token-1234"},
        headers=auth_headers,
    ).json()["id"]

    resp = client.put(
        f"/circles/{circle_id}/telegram/{config_id}",
        json={"group_chat_id": "-1009"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["group_chat_id"] == "-1009"


def test_detect_chat_returns_options(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    """Ensure detect-chat surfaces chats the bot has seen."""
    circle_id = _make_circle(client, auth_headers)
    config_id = client.post(
        f"/circles/{circle_id}/telegram",
        json={"label": "Group", "bot_token": "secret-token-1234"},
        headers=auth_headers,
    ).json()["id"]

    monkeypatch.setattr(
        circle_telegram,
        "get_chat_options",
        lambda token: [
            {"chat_id": "-1009", "name": "Game Night", "type": "group"}
        ],
    )
    resp = client.post(
        f"/circles/{circle_id}/telegram/{config_id}/detect-chat",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    chats = resp.json()["chats"]
    assert chats == [
        {"chat_id": "-1009", "name": "Game Night", "type": "group"}
    ]


def test_delete_config(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure a bot config can be removed."""
    circle_id = _make_circle(client, auth_headers)
    config_id = client.post(
        f"/circles/{circle_id}/telegram",
        json={"label": "Group", "bot_token": "secret-token-1234"},
        headers=auth_headers,
    ).json()["id"]

    resp = client.delete(
        f"/circles/{circle_id}/telegram/{config_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 204
    listing = client.get(f"/circles/{circle_id}/telegram", headers=auth_headers)
    assert listing.json() == []
