"""Integration tests for the /circles API endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def test_list_circles_empty_for_new_user(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure GET /circles returns [] for a user with no circles."""
    response = client.get("/circles", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_circle_returns_201(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure POST /circles creates a circle and returns 201."""
    payload = {"name": "Boardgame Night", "timezone": "UTC"}
    response = client.post("/circles", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Boardgame Night"
    assert "id" in data
    assert "invite_token" in data


def test_created_circle_appears_in_list(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure a new circle appears in the creator's circle list."""
    client.post(
        "/circles",
        json={"name": "RPG Campaign", "timezone": "UTC"},
        headers=auth_headers,
    )
    response = client.get("/circles", headers=auth_headers)
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "RPG Campaign" in names


def test_get_circle_non_member_returns_403(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure GET /circles/{id} returns 403 for a non-member."""
    create_resp = client.post(
        "/circles",
        json={"name": "Private Circle", "timezone": "UTC"},
        headers=auth_headers,
    )
    circle_id = create_resp.json()["id"]

    other_headers = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-b', email='b@x.test')}"
        )
    }
    response = client.get(f"/circles/{circle_id}", headers=other_headers)
    assert response.status_code == 403


def test_get_nonexistent_circle_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure GET /circles/{id} returns 404 for unknown IDs."""
    response = client.get(f"/circles/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


def test_update_circle_name(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure PATCH /circles/{id} updates the circle name."""
    create_resp = client.post(
        "/circles",
        json={"name": "Old Name", "timezone": "UTC"},
        headers=auth_headers,
    )
    circle_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/circles/{circle_id}",
        json={"name": "New Name"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "New Name"


def test_unauthenticated_request_is_rejected(
    client: TestClient,
) -> None:
    """Ensure GET /circles requires a bearer token (401/403)."""
    response = client.get("/circles")
    assert response.status_code in (401, 403)


def test_regenerate_invite_is_rate_limited(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure invite regeneration returns 429 after configured limit."""
    create_resp = client.post(
        "/circles",
        json={"name": "Rate Limited", "timezone": "UTC"},
        headers=auth_headers,
    )
    circle_id = create_resp.json()["id"]

    for _ in range(3):
        ok_resp = client.post(
            f"/circles/{circle_id}/invite",
            headers=auth_headers,
        )
        assert ok_resp.status_code == 200

    limited_resp = client.post(
        f"/circles/{circle_id}/invite",
        headers=auth_headers,
    )
    assert limited_resp.status_code == 429
    assert limited_resp.headers["RateLimit-Limit"] == "3"
    assert limited_resp.headers["RateLimit-Remaining"] == "0"
    assert int(limited_resp.headers["RateLimit-Reset"]) >= 1
    assert int(limited_resp.headers["Retry-After"]) >= 1
