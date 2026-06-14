"""Integration tests for the /circles API endpoints."""

from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient

# Minimal byte payload; content-type validation is by declared type,
# so the bytes themselves need not be a real image.
_PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-image-bytes"


def _create_circle(
    client: TestClient,
    auth_headers: dict[str, str],
    name: str = "Image Circle",
) -> dict:
    """Create a circle as the default identity and return its body."""
    resp = client.post(
        "/circles",
        json={"name": name, "timezone": "UTC"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


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


def test_list_circles_includes_next_viable_date(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure GET /circles annotates each circle's next viable date."""
    create = client.post(
        "/circles",
        json={"name": "Viable Soon", "timezone": "UTC"},
        headers=auth_headers,
    )
    circle_id = create.json()["id"]
    target = (date.today() + timedelta(days=5)).isoformat()
    # Mark the owner as attending an upcoming day -> that day is viable.
    client.post(
        f"/circles/{circle_id}/availability/jobs",
        json={"action": "cycle", "arguments": {"local_date": target}},
        headers=auth_headers,
    )

    response = client.get("/circles", headers=auth_headers)
    assert response.status_code == 200
    body = next(c for c in response.json() if c["id"] == circle_id)
    assert body["next_viable_date"] == target


def test_list_circles_next_viable_date_null_when_none(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Ensure next_viable_date is null when no upcoming day is viable."""
    client.post(
        "/circles",
        json={"name": "Quiet Circle", "timezone": "UTC"},
        headers=auth_headers,
    )
    response = client.get("/circles", headers=auth_headers)
    assert response.status_code == 200
    assert all(c["next_viable_date"] is None for c in response.json())


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


def test_invalid_token_emits_backend_warning(
    client: TestClient,
    caplog,
) -> None:
    """Ensure invalid bearer tokens produce a useful warning log."""
    caplog.set_level(logging.WARNING, logger="app.dependencies")

    response = client.get(
        "/circles",
        headers={"Authorization": "Bearer definitely-not-a-jwt"},
    )

    assert response.status_code == 401
    assert "Invalid token" in response.text
    assert any(
        "Token validation failed via unclassified" in record.getMessage()
        for record in caplog.records
    )


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


def test_upload_circle_image_sets_image_ref_and_serves_bytes(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Owner upload sets image_ref; public GET returns the bytes."""
    circle = _create_circle(client, auth_headers)
    cid = circle["id"]

    upload = client.post(
        f"/circles/{cid}/image",
        files={"file": ("hero.png", _PNG_BYTES, "image/png")},
        headers=auth_headers,
    )
    assert upload.status_code == 200
    assert upload.json()["image_ref"].startswith(f"/circles/{cid}/image?v=")

    # No auth headers: the image endpoint must be public.
    served = client.get(f"/circles/{cid}/image")
    assert served.status_code == 200
    assert served.content == _PNG_BYTES
    assert served.headers["content-type"] == "image/png"


def test_upload_circle_image_member_forbidden(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """A plain member cannot upload a circle image (403)."""
    circle = _create_circle(client, auth_headers)
    cid = circle["id"]

    member_headers = {
        "Authorization": (
            f"Bearer {token_factory(sub='member-1', email='m@x.test')}"
        )
    }
    join = client.post(
        "/circles/join",
        json={
            "invite_token": circle["invite_token"],
            "pseudonym": "member-one",
            "can_host_default": False,
        },
        headers=member_headers,
    )
    assert join.status_code == 201

    resp = client.post(
        f"/circles/{cid}/image",
        files={"file": ("hero.png", _PNG_BYTES, "image/png")},
        headers=member_headers,
    )
    assert resp.status_code == 403


def test_upload_circle_image_non_member_forbidden(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """A non-member cannot upload a circle image (403)."""
    circle = _create_circle(client, auth_headers)
    cid = circle["id"]

    other_headers = {
        "Authorization": (
            f"Bearer {token_factory(sub='nobody', email='n@x.test')}"
        )
    }
    resp = client.post(
        f"/circles/{cid}/image",
        files={"file": ("hero.png", _PNG_BYTES, "image/png")},
        headers=other_headers,
    )
    assert resp.status_code == 403


def test_upload_circle_image_rejects_bad_content_type(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """An unsupported content type is rejected with 400."""
    circle = _create_circle(client, auth_headers)
    cid = circle["id"]
    resp = client.post(
        f"/circles/{cid}/image",
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_upload_circle_image_rejects_oversized(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """A payload above the configured limit is rejected with 413."""
    circle = _create_circle(client, auth_headers)
    cid = circle["id"]
    oversized = b"x" * (5 * 1024 * 1024 + 1)
    resp = client.post(
        f"/circles/{cid}/image",
        files={"file": ("big.png", oversized, "image/png")},
        headers=auth_headers,
    )
    assert resp.status_code == 413


def test_get_circle_image_missing_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """A circle without an image returns 404 from the image GET."""
    circle = _create_circle(client, auth_headers)
    resp = client.get(f"/circles/{circle['id']}/image")
    assert resp.status_code == 404


def test_delete_circle_image_clears_ref(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting the image clears image_ref and 404s the GET."""
    circle = _create_circle(client, auth_headers)
    cid = circle["id"]
    client.post(
        f"/circles/{cid}/image",
        files={"file": ("hero.png", _PNG_BYTES, "image/png")},
        headers=auth_headers,
    )

    deleted = client.delete(f"/circles/{cid}/image", headers=auth_headers)
    assert deleted.status_code == 200
    assert deleted.json()["image_ref"] is None
    assert client.get(f"/circles/{cid}/image").status_code == 404


def test_deleting_circle_cascades_to_image(db_session) -> None:
    """Deleting a circle removes its stored image (no orphan row).

    Exercised at the ORM layer: the model's delete-orphan cascade
    (and the DB-level ``ON DELETE CASCADE`` in Postgres) ensures the
    blob row is removed with its circle.
    """
    from sqlalchemy import select

    from app.models.circle import Circle
    from app.models.circle_image import CircleImage
    from app.models.user import User

    owner = User(email="owner@x.test", display_name="Owner")
    db_session.add(owner)
    db_session.flush()

    circle = Circle(
        name="Cascade",
        timezone="UTC",
        invite_token="ABCDEF",
        created_by_user_id=owner.id,
    )
    circle.image = CircleImage(content_type="image/png", data=_PNG_BYTES)
    db_session.add(circle)
    db_session.flush()
    circle_id = circle.id

    db_session.delete(circle)
    db_session.flush()

    remaining = db_session.execute(
        select(CircleImage).where(CircleImage.circle_id == circle_id)
    ).scalar_one_or_none()
    assert remaining is None
