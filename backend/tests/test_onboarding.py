"""Integration tests for the /onboarding endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_state_returns_defaults(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure first GET creates defaults: welcome unseen, no tips."""
    response = client.get("/onboarding", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {
        "welcome_seen": False,
        "seen_tips": [],
    }


def test_put_welcome_marks_seen_idempotently(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure PUT /welcome sets the flag and repeats safely."""
    first = client.put(
        "/onboarding/welcome",
        json={"welcome_seen": True},
        headers=auth_headers,
    )
    assert first.status_code == 200
    assert first.json()["welcome_seen"] is True

    second = client.put(
        "/onboarding/welcome",
        json={"welcome_seen": True},
        headers=auth_headers,
    )
    assert second.status_code == 200
    assert second.json()["welcome_seen"] is True


def test_post_tips_unions_and_dedupes(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure POST /tips unions keys and removes duplicates."""
    client.post(
        "/onboarding/tips",
        json={"tip_keys": ["a", "b"]},
        headers=auth_headers,
    )
    response = client.post(
        "/onboarding/tips",
        json={"tip_keys": ["b", "c"]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["seen_tips"] == ["a", "b", "c"]


def test_state_is_per_user(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure one user's onboarding state does not affect another's."""
    client.put(
        "/onboarding/welcome",
        json={"welcome_seen": True},
        headers=auth_headers,
    )
    client.post(
        "/onboarding/tips",
        json={"tip_keys": ["a", "b"]},
        headers=auth_headers,
    )
    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='user-b', email='b@x.test')}"
        )
    }
    response = client.get("/onboarding", headers=other)
    assert response.status_code == 200
    assert response.json() == {
        "welcome_seen": False,
        "seen_tips": [],
    }
