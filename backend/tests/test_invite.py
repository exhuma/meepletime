"""Tests for invite PIN generation, normalization, and the join flow."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.circle import Circle
from app.services import invite


def test_generate_pin_shape() -> None:
    """A generated PIN is 6 chars, all from the unambiguous alphabet."""
    for _ in range(50):
        pin = invite.generate_pin()
        assert len(pin) == invite.INVITE_LENGTH
        assert all(ch in invite.INVITE_ALPHABET for ch in pin)
        # Confusable characters must never appear.
        assert not (set("0O1IL") & set(pin))


def test_normalize_pin_strips_and_uppercases() -> None:
    """normalize_pin removes separators and uppercases input."""
    assert invite.normalize_pin(" ab-23 4f ") == "AB234F"
    assert invite.normalize_pin("k7p2qf") == "K7P2QF"


def test_is_valid_pin() -> None:
    """is_valid_pin accepts in-alphabet 6-char codes only."""
    assert invite.is_valid_pin("K7P2QF")
    assert not invite.is_valid_pin("K7P2Q")  # too short
    assert not invite.is_valid_pin("K7P2QFA")  # too long
    assert not invite.is_valid_pin("K0P2QF")  # contains excluded 0


def test_generate_unique_pin_retries_past_collision(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """generate_unique_pin skips a PIN already taken by a circle."""
    taken_pin = "AAAAAA"
    free_pin = "BBBBBB"
    db_session.add(
        Circle(
            name="Existing",
            invite_token=taken_pin,
            created_by_user_id=uuid.uuid4(),
        )
    )
    db_session.flush()

    pins = iter([taken_pin, free_pin])
    monkeypatch.setattr(invite, "generate_pin", lambda: next(pins))

    assert invite.generate_unique_pin(db_session) == free_pin


def _create_circle(client: TestClient, headers: dict[str, str]) -> str:
    """Create a circle and return its invite PIN."""
    resp = client.post(
        "/circles",
        json={"name": "PIN Circle", "timezone": "UTC"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["invite_token"]


def test_created_circle_has_valid_pin(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """A newly created circle exposes a well-formed invite PIN."""
    pin = _create_circle(client, auth_headers)
    assert invite.is_valid_pin(pin)


def test_join_accepts_normalized_pin(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Joining works with a lowercase, space-padded PIN."""
    pin = _create_circle(client, auth_headers)
    other = {
        "Authorization": (
            f"Bearer {token_factory(sub='joiner', email='j@x.test')}"
        )
    }
    messy = f" {pin.lower()} "
    resp = client.post(
        "/circles/join",
        json={"invite_token": messy, "pseudonym": "Joiner"},
        headers=other,
    )
    assert resp.status_code == 201


def test_preview_accepts_lowercase_pin(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """The unauthenticated preview normalizes a lowercase PIN."""
    pin = _create_circle(client, auth_headers)
    resp = client.get(f"/circles/join/{pin.lower()}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "PIN Circle"


def test_join_wrong_length_pin_is_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """A PIN of the wrong length is rejected before lookup."""
    resp = client.post(
        "/circles/join",
        json={"invite_token": "ABC", "pseudonym": "X"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_join_unknown_pin_is_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """A valid-format but unknown PIN returns 404."""
    resp = client.post(
        "/circles/join",
        json={"invite_token": "ZZZZZZ", "pseudonym": "X"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
