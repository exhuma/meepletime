"""Tests for per-user Telegram DM opt-in (aggregate + detect)."""

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


def _make_dm_bot(
    client: TestClient, headers: dict[str, str], circle_id: str
) -> str:
    """Create a DM-mode bot on the circle and return its id."""
    resp = client.post(
        f"/circles/{circle_id}/telegram",
        json={
            "label": "DM Bot",
            "bot_token": "secret-token-9999",
            "mode": "dm",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["mode"] == "dm"
    return resp.json()["id"]


def test_aggregate_lists_member_dm_bots(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure the profile aggregate lists DM bots of joined circles."""
    circle_id = _make_circle(client, auth_headers)
    config_id = _make_dm_bot(client, auth_headers, circle_id)

    resp = client.get("/users/me/telegram/dm-bots", headers=auth_headers)
    assert resp.status_code == 200
    bots = resp.json()
    assert len(bots) == 1
    assert bots[0]["config_id"] == config_id
    assert bots[0]["circle_id"] == circle_id
    assert bots[0]["linked"] is False


def test_aggregate_excludes_non_member_circles(
    client: TestClient, auth_headers: dict[str, str], token_factory
) -> None:
    """Ensure a user never sees DM bots of circles they are not in."""
    circle_id = _make_circle(client, auth_headers)
    _make_dm_bot(client, auth_headers, circle_id)

    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-b', email='b@x.test')}"
        )
    }
    resp = client.get("/users/me/telegram/dm-bots", headers=other)
    assert resp.status_code == 200
    assert resp.json() == []


def test_link_reflects_in_aggregate(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure linking a chat flips the aggregate link state."""
    circle_id = _make_circle(client, auth_headers)
    config_id = _make_dm_bot(client, auth_headers, circle_id)

    link = client.put(
        f"/circles/{circle_id}/telegram/{config_id}/link",
        json={"chat_id": "12345"},
        headers=auth_headers,
    )
    assert link.status_code == 204

    bots = client.get("/users/me/telegram/dm-bots", headers=auth_headers).json()
    assert bots[0]["linked"] is True


def test_detect_dm_returns_only_private_chats(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    """Ensure detect-dm filters out non-private chats."""
    circle_id = _make_circle(client, auth_headers)
    config_id = _make_dm_bot(client, auth_headers, circle_id)

    monkeypatch.setattr(
        circle_telegram,
        "get_chat_options",
        lambda token: [
            {"chat_id": "-100", "name": "Group", "type": "group"},
            {"chat_id": "42", "name": "Alice", "type": "private"},
        ],
    )
    resp = client.post(
        f"/circles/{circle_id}/telegram/{config_id}/detect-dm",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    chats = resp.json()["chats"]
    assert chats == [{"chat_id": "42", "name": "Alice", "type": "private"}]


def test_detect_dm_rejects_non_member(
    client: TestClient, auth_headers: dict[str, str], token_factory
) -> None:
    """Ensure a non-member cannot detect a bot's private chats."""
    circle_id = _make_circle(client, auth_headers)
    config_id = _make_dm_bot(client, auth_headers, circle_id)

    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-c', email='c@x.test')}"
        )
    }
    resp = client.post(
        f"/circles/{circle_id}/telegram/{config_id}/detect-dm",
        headers=other,
    )
    assert resp.status_code == 403


def test_detect_dm_rejects_group_bot(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure detect-dm 404s for a group-mode bot."""
    circle_id = _make_circle(client, auth_headers)
    group_id = client.post(
        f"/circles/{circle_id}/telegram",
        json={"label": "Group", "bot_token": "secret-token-1234"},
        headers=auth_headers,
    ).json()["id"]

    resp = client.post(
        f"/circles/{circle_id}/telegram/{group_id}/detect-dm",
        headers=auth_headers,
    )
    assert resp.status_code == 404
