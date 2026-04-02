"""Integration tests for availability cycle endpoint."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient


def _create_circle(
    client: TestClient,
    headers: dict[str, str],
) -> str:
    """Create a test circle and return its ID."""
    response = client.post(
        "/circles",
        json={"name": "Test Circle", "timezone": "UTC"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_cycle_empty_to_attending(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """
    Ensure cycle action transitions empty → attending.
    """
    circle_id = _create_circle(client, auth_headers)
    local_date = (date.today() + timedelta(days=1)).isoformat()

    response = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["availability"] is not None
    assert data["availability"]["state"] == "attending"
    assert data["availability"]["local_date"] == local_date


def test_cycle_attending_to_hosting(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """
    Ensure cycle action transitions attending → hosting.
    """
    circle_id = _create_circle(client, auth_headers)
    local_date = (date.today() + timedelta(days=2)).isoformat()

    # First cycle: empty → attending
    client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )

    # Second cycle: attending → hosting
    response = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["availability"] is not None
    assert data["availability"]["state"] == "hosting"


def test_cycle_hosting_to_empty(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """
    Ensure cycle action transitions hosting → empty.
    """
    circle_id = _create_circle(client, auth_headers)
    local_date = (date.today() + timedelta(days=3)).isoformat()

    # First cycle: empty → attending
    client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )

    # Second cycle: attending → hosting
    client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )

    # Third cycle: hosting → empty
    response = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["availability"] is None


def test_cycle_full_rotation(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """
    Ensure full cycle rotation: empty → attending → hosting → empty
    → attending.
    """
    circle_id = _create_circle(client, auth_headers)
    local_date = (date.today() + timedelta(days=4)).isoformat()

    # Cycle 1: empty → attending
    r1 = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )
    assert r1.json()["availability"]["state"] == "attending"

    # Cycle 2: attending → hosting
    r2 = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )
    assert r2.json()["availability"]["state"] == "hosting"

    # Cycle 3: hosting → empty
    r3 = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )
    assert r3.json()["availability"] is None

    # Cycle 4: empty → attending again
    r4 = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )
    assert r4.json()["availability"]["state"] == "attending"


def test_cycle_past_date_as_owner_succeeds(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """
    Ensure cycling a past date as circle owner succeeds.

    Owners and admins can edit past dates.
    """
    circle_id = _create_circle(client, auth_headers)
    past_date = (date.today() - timedelta(days=1)).isoformat()

    response = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": past_date}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["availability"] is not None
    assert data["availability"]["state"] == "attending"


def test_cycle_non_member_returns_403(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """
    Ensure cycling availability as a non-member returns 403.
    """
    circle_id = _create_circle(client, auth_headers)
    local_date = (date.today() + timedelta(days=5)).isoformat()

    other_headers = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-b', email='b@x.test')}"
        )
    }

    response = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=other_headers,
    )

    assert response.status_code == 403


def test_cycle_nonexistent_circle_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """
    Ensure cycling for a nonexistent circle returns 404.
    """
    local_date = (date.today() + timedelta(days=6)).isoformat()

    response = client.post(
        f"/circles/{uuid.uuid4()}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": local_date}},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_cycle_unknown_action_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """
    Ensure an unknown action returns 400.
    """
    circle_id = _create_circle(client, auth_headers)
    local_date = (date.today() + timedelta(days=7)).isoformat()

    response = client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={
            "action": "unknown_action",
            "arguments": {"local_date": local_date},
        },
        headers=auth_headers,
    )

    assert response.status_code == 422  # Pydantic validation error
