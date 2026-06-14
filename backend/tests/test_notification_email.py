"""Integration tests for the notification-email confirmation flow."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

import app.routers.notifications as notif_router
import app.services.email_confirmation as confirm_svc


class _Mailbox:
    """Collects (to, subject, body) tuples in place of real SMTP."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def __call__(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


@pytest.fixture()
def mailbox(monkeypatch) -> _Mailbox:
    """Patch SMTP config + send so confirmation mail is captured."""
    box = _Mailbox()
    monkeypatch.setattr(notif_router, "is_smtp_configured", lambda: True)
    monkeypatch.setattr(confirm_svc, "send_email", box)
    return box


def _code_from(body: str) -> str:
    """Extract the ``code`` query param from a confirmation body."""
    match = re.search(r"[?&]code=([^\s&]+)", body)
    assert match, f"no code in body: {body!r}"
    return match.group(1)


def test_set_email_sends_link_and_marks_pending(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Setting an address sends a link and reports it as pending."""
    res = client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["pending_email"] == "notify@example.com"
    assert body["notification_email"] is None
    assert len(mailbox.sent) == 1
    assert mailbox.sent[0][0] == "notify@example.com"


def test_confirm_promotes_address_and_consumes_code(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Confirming sets notification_email and invalidates the code."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    code = _code_from(mailbox.sent[0][2])

    res = client.post("/notifications/email/confirm", json={"code": code})
    assert res.status_code == 200
    assert res.json() == {
        "status": "confirmed",
        "email": "notify@example.com",
    }

    settings = client.get(
        "/notifications/settings", headers=auth_headers
    ).json()
    assert settings["notification_email"] == "notify@example.com"
    assert settings["pending_email"] is None

    # Code is single-use now.
    again = client.post("/notifications/email/confirm", json={"code": code})
    assert again.json()["status"] == "invalid"


def test_confirm_endpoint_needs_no_auth(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """The confirm endpoint works without an Authorization header."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    code = _code_from(mailbox.sent[0][2])
    res = client.post("/notifications/email/confirm", json={"code": code})
    assert res.status_code == 200
    assert res.json()["status"] == "confirmed"


def test_confirm_unknown_code_is_invalid(client: TestClient) -> None:
    """An unknown code reports 'invalid' without leaking existence."""
    res = client.post("/notifications/email/confirm", json={"code": "nope"})
    assert res.status_code == 200
    assert res.json() == {"status": "invalid", "email": None}


def test_expired_code_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    mailbox: _Mailbox,
    monkeypatch,
) -> None:
    """A code past its deadline reports 'expired'."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    code = _code_from(mailbox.sent[0][2])

    # Force every pending row to be already expired.
    from datetime import timedelta

    real_now = confirm_svc._now

    def _past():
        return real_now() + timedelta(hours=48)

    monkeypatch.setattr(confirm_svc, "_now", _past)

    res = client.post("/notifications/email/confirm", json={"code": code})
    assert res.json()["status"] == "expired"


def test_retry_resends_same_token_with_new_deadline(
    client: TestClient,
    auth_headers: dict[str, str],
    mailbox: _Mailbox,
    monkeypatch,
) -> None:
    """Retry reuses the same token and refreshes the deadline."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    first_settings = client.get(
        "/notifications/settings", headers=auth_headers
    ).json()
    first_code = _code_from(mailbox.sent[0][2])

    # Skip past the resend cooldown.
    from datetime import timedelta

    real_now = confirm_svc._now

    def _later():
        return real_now() + timedelta(seconds=120)

    monkeypatch.setattr(confirm_svc, "_now", _later)

    res = client.post("/notifications/email/resend", headers=auth_headers)
    assert res.status_code == 200
    second_code = _code_from(mailbox.sent[1][2])
    assert second_code == first_code
    assert (
        res.json()["pending_expires_at"] > first_settings["pending_expires_at"]
    )


def test_resend_without_pending_is_400(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Resending with nothing pending returns 400."""
    res = client.post("/notifications/email/resend", headers=auth_headers)
    assert res.status_code == 400


def test_replacing_keeps_old_until_confirmed(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Setting a new address leaves the old confirmed one active."""
    # Confirm the first address.
    client.post(
        "/notifications/email",
        json={"email": "first@example.com"},
        headers=auth_headers,
    )
    client.post(
        "/notifications/email/confirm",
        json={"code": _code_from(mailbox.sent[0][2])},
    )
    # Start confirming a second address.
    res = client.post(
        "/notifications/email",
        json={"email": "second@example.com"},
        headers=auth_headers,
    ).json()
    assert res["notification_email"] == "first@example.com"
    assert res["pending_email"] == "second@example.com"


def test_clear_email_removes_confirmed_and_pending(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """DELETE clears both the confirmed address and any pending one."""
    client.post(
        "/notifications/email",
        json={"email": "first@example.com"},
        headers=auth_headers,
    )
    client.post(
        "/notifications/email/confirm",
        json={"code": _code_from(mailbox.sent[0][2])},
    )
    res = client.delete("/notifications/email", headers=auth_headers).json()
    assert res["notification_email"] is None
    assert res["pending_email"] is None
