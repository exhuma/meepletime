"""Integration tests for member Telegram DM linking endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _make_circle(client: TestClient, headers: dict[str, str]) -> str:
    """Create a circle and return its id (caller becomes owner)."""
    resp = client.post(
        "/circles",
        json={"name": "DM", "timezone": "UTC"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _make_dm_bot(
    client: TestClient, circle_id: str, headers: dict[str, str]
) -> str:
    """Create a DM-mode bot config and return its id."""
    resp = client.post(
        f"/circles/{circle_id}/telegram",
        json={
            "label": "DM bot",
            "bot_token": "secret-token-9999",
            "mode": "dm",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_dm_link_roundtrip(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure a member can link then unlink a DM chat for a bot."""
    circle_id = _make_circle(client, auth_headers)
    config_id = _make_dm_bot(client, circle_id, auth_headers)

    bots = client.get(
        f"/circles/{circle_id}/telegram/dm-bots", headers=auth_headers
    )
    assert bots.status_code == 200
    assert bots.json() == [
        {"id": config_id, "label": "DM bot", "linked": False}
    ]

    link = client.put(
        f"/circles/{circle_id}/telegram/{config_id}/link",
        json={"chat_id": "424242"},
        headers=auth_headers,
    )
    assert link.status_code == 204

    bots = client.get(
        f"/circles/{circle_id}/telegram/dm-bots", headers=auth_headers
    )
    assert bots.json()[0]["linked"] is True

    unlink = client.delete(
        f"/circles/{circle_id}/telegram/{config_id}/link",
        headers=auth_headers,
    )
    assert unlink.status_code == 204
    bots = client.get(
        f"/circles/{circle_id}/telegram/dm-bots", headers=auth_headers
    )
    assert bots.json()[0]["linked"] is False


def test_dm_bots_excludes_group_mode(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure group-mode bots never appear in the DM bot list."""
    circle_id = _make_circle(client, auth_headers)
    client.post(
        f"/circles/{circle_id}/telegram",
        json={"label": "Group", "bot_token": "secret-token-1111"},
        headers=auth_headers,
    )
    bots = client.get(
        f"/circles/{circle_id}/telegram/dm-bots", headers=auth_headers
    )
    assert bots.status_code == 200
    assert bots.json() == []


def test_link_non_member_forbidden(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a non-member cannot list or link DM bots."""
    circle_id = _make_circle(client, auth_headers)
    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-z', email='z@x.test')}"
        )
    }
    resp = client.get(f"/circles/{circle_id}/telegram/dm-bots", headers=other)
    assert resp.status_code == 403
