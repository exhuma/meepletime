"""Tests for profile-picture upload and avatar resolution."""

from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from app.services.avatar import GravatarProvider, resolve_avatar_ref

_PNG = b"\x89PNG\r\n\x1a\nfake-bytes"


def _gravatar(email: str) -> str:
    """Return the expected gravatar URL for an email."""
    digest = hashlib.md5(email.strip().lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{digest}?d=404&s=256"


def test_me_falls_back_to_gravatar(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure /auth/me yields a gravatar ref with no image or claim."""
    res = client.get("/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["avatar_ref"] == _gravatar("test@example.com")


def test_me_uses_idp_picture_claim(client: TestClient, token_factory) -> None:
    """Ensure the IDP picture claim is used when no upload exists."""
    headers = {
        "Authorization": "Bearer "
        + token_factory(
            sub="pic-user",
            email="pic@example.com",
            picture="https://idp.example/p.png",
        )
    }
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["avatar_ref"] == "https://idp.example/p.png"


def test_upload_then_serve_and_precedence(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure an upload is served and outranks the gravatar fallback."""
    res = client.post(
        "/users/me/image",
        headers=auth_headers,
        files={"file": ("a.png", _PNG, "image/png")},
    )
    assert res.status_code == 200
    ref = res.json()["avatar_ref"]
    assert ref.startswith("/users/")
    assert "/image?v=" in ref

    # /auth/me now reports the uploaded image, not the gravatar.
    me = client.get("/auth/me", headers=auth_headers).json()
    assert me["avatar_ref"] == ref

    # The bytes are served publicly with the stored content type.
    served = client.get(ref)
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/png"
    assert served.content == _PNG


def test_upload_rejects_unsupported_type(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure a non-image upload is rejected with HTTP 400."""
    res = client.post(
        "/users/me/image",
        headers=auth_headers,
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400


def test_delete_falls_back_to_gravatar(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure deleting the upload restores the gravatar fallback."""
    client.post(
        "/users/me/image",
        headers=auth_headers,
        files={"file": ("a.png", _PNG, "image/png")},
    )
    res = client.delete("/users/me/image", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["avatar_ref"] == _gravatar("test@example.com")


def test_get_image_404_when_absent(client: TestClient) -> None:
    """Ensure serving a missing image returns HTTP 404."""
    res = client.get("/users/00000000-0000-0000-0000-000000000000/image")
    assert res.status_code == 404


def test_upload_requires_auth(client: TestClient) -> None:
    """Ensure uploading without a token is rejected."""
    res = client.post(
        "/users/me/image",
        files={"file": ("a.png", _PNG, "image/png")},
    )
    assert res.status_code in (401, 403)


def test_gravatar_provider_empty_email() -> None:
    """Ensure the gravatar provider returns None for an empty email."""
    assert GravatarProvider().url_for("  ") is None


def test_resolver_prefers_picture_over_gravatar() -> None:
    """Ensure picture_url outranks the gravatar fallback."""

    class _User:
        id = "x"
        email = "a@b.c"
        picture_url = "https://idp/p.png"

    assert resolve_avatar_ref(_User(), None) == "https://idp/p.png"
