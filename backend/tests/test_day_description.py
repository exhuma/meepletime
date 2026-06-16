"""Tests for the day-description feature.

Covers the HTTP API (circle-wide and per-host descriptions, their
permissions, and Delta validation) and the folding of descriptions
into viability emails.
"""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.availability import AvailabilityState, DayAvailability
from app.models.circle import Circle
from app.models.day_description import DayDescription
from app.models.membership import CircleMembership, MemberRole
from app.models.notification import NotificationEvent
from app.models.user import User
from app.services.notifications.context import build_event_context
from app.services.notifications.email_render import render_notification

_DAY = "2026-07-04"
_DELTA = {"ops": [{"insert": "Meet at the church car park\n"}]}


# --------------------------------------------------------------------- #
# HTTP helpers                                                          #
# --------------------------------------------------------------------- #


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_circle(
    client: TestClient,
    headers: dict[str, str],
    *,
    host_needed: bool = False,
) -> dict:
    """Create a circle (owner = caller); optionally host-required."""
    resp = client.post(
        "/circles",
        json={"name": "Hikers", "timezone": "UTC"},
        headers=headers,
    )
    assert resp.status_code == 201
    circle = resp.json()
    if host_needed:
        patched = client.patch(
            f"/circles/{circle['id']}",
            json={"host_needed": True},
            headers=headers,
        )
        assert patched.status_code == 200
        circle = patched.json()
    return circle


def _join(
    client: TestClient,
    token: str,
    invite_token: str,
    pseudonym: str,
) -> None:
    resp = client.post(
        "/circles/join",
        json={
            "invite_token": invite_token,
            "pseudonym": pseudonym,
            "can_host_default": True,
        },
        headers=_headers(token),
    )
    assert resp.status_code in (200, 201)


def _user_id(
    client: TestClient,
    headers: dict[str, str],
    circle_id: str,
    pseudonym: str,
) -> str:
    resp = client.get(f"/circles/{circle_id}/members", headers=headers)
    assert resp.status_code == 200
    for member in resp.json():
        if member["pseudonym"] == pseudonym:
            return member["user_id"]
    raise AssertionError(f"member {pseudonym} not found")


def _cycle(
    client: TestClient,
    token: str,
    circle_id: str,
    times: int,
) -> None:
    """Cycle the caller's availability (empty->attending->hosting->...)."""
    for _ in range(times):
        resp = client.post(
            f"/circles/{circle_id}/availability/jobs",
            json={"action": "cycle", "arguments": {"local_date": _DAY}},
            headers=_headers(token),
        )
        assert resp.status_code in (200, 201, 202)


# --------------------------------------------------------------------- #
# Circle-wide description (owner / admin)                               #
# --------------------------------------------------------------------- #


def test_get_empty_returns_null_bundle(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure an unset day has a null circle-wide and empty per-host."""
    circle = _create_circle(client, auth_headers)
    resp = client.get(
        f"/circles/{circle['id']}/day-description/{_DAY}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["circle_wide"] is None
    assert body["per_host"] == []


def test_owner_sets_and_updates_circle_wide(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure owner can upsert the circle-wide description in place."""
    circle = _create_circle(client, auth_headers)
    url = f"/circles/{circle['id']}/day-description/{_DAY}"

    first = client.put(
        url, json={"content_delta": _DELTA}, headers=auth_headers
    )
    assert first.status_code == 200

    updated = {"ops": [{"insert": "New spot\n"}]}
    second = client.put(
        url, json={"content_delta": updated}, headers=auth_headers
    )
    assert second.status_code == 200

    got = client.get(url, headers=auth_headers).json()
    assert got["circle_wide"]["content_delta"] == updated
    assert got["per_host"] == []


def test_member_cannot_set_circle_wide(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a plain member is forbidden from the circle-wide PUT."""
    circle = _create_circle(client, auth_headers)
    member = token_factory(sub="member-1", email="m1@x.test")
    _join(client, member, circle["invite_token"], "Memberer")

    resp = client.put(
        f"/circles/{circle['id']}/day-description/{_DAY}",
        json={"content_delta": _DELTA},
        headers=_headers(member),
    )
    assert resp.status_code == 403


def test_admin_can_set_circle_wide(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a promoted admin may set the circle-wide description."""
    circle = _create_circle(client, auth_headers)
    admin = token_factory(sub="admin-1", email="a1@x.test")
    _join(client, admin, circle["invite_token"], "Adminer")
    admin_uid = _user_id(client, auth_headers, circle["id"], "Adminer")
    promote = client.patch(
        f"/circles/{circle['id']}/members/{admin_uid}",
        json={"role": "admin"},
        headers=auth_headers,
    )
    assert promote.status_code == 200

    resp = client.put(
        f"/circles/{circle['id']}/day-description/{_DAY}",
        json={"content_delta": _DELTA},
        headers=_headers(admin),
    )
    assert resp.status_code == 200


def test_delete_circle_wide(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure owner can clear and a member cannot delete."""
    circle = _create_circle(client, auth_headers)
    url = f"/circles/{circle['id']}/day-description/{_DAY}"
    client.put(url, json={"content_delta": _DELTA}, headers=auth_headers)

    member = token_factory(sub="member-2", email="m2@x.test")
    _join(client, member, circle["invite_token"], "Mem2")
    assert client.delete(url, headers=_headers(member)).status_code == 403

    assert client.delete(url, headers=auth_headers).status_code == 204
    got = client.get(url, headers=auth_headers).json()
    assert got["circle_wide"] is None


# --------------------------------------------------------------------- #
# Delta validation                                                     #
# --------------------------------------------------------------------- #


def test_delta_validation_rejects_bad_payloads(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure malformed or unsafe Deltas are rejected with 422."""
    circle = _create_circle(client, auth_headers)
    url = f"/circles/{circle['id']}/day-description/{_DAY}"

    bad_payloads = [
        {"content_delta": {"nope": []}},  # missing ops
        {"content_delta": {"ops": [{"insert": {"image": "x"}}]}},  # embed
        {
            "content_delta": {
                "ops": [{"insert": "x", "attributes": {"script": True}}]
            }
        },  # disallowed attribute
        {
            "content_delta": {
                "ops": [
                    {
                        "insert": "x",
                        "attributes": {"link": "javascript:alert(1)"},
                    }
                ]
            }
        },  # unsafe link scheme
    ]
    for payload in bad_payloads:
        resp = client.put(url, json=payload, headers=auth_headers)
        assert resp.status_code == 422, payload


def test_delta_valid_roundtrips(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensure a valid formatted Delta is stored unchanged."""
    circle = _create_circle(client, auth_headers)
    url = f"/circles/{circle['id']}/day-description/{_DAY}"
    delta = {
        "ops": [
            {"insert": "Trail", "attributes": {"bold": True}},
            {"insert": "\n", "attributes": {"header": 3}},
            {"insert": "Mullerthal loop\n"},
        ]
    }
    resp = client.put(url, json={"content_delta": delta}, headers=auth_headers)
    assert resp.status_code == 200
    got = client.get(url, headers=auth_headers).json()
    assert got["circle_wide"]["content_delta"] == delta


# --------------------------------------------------------------------- #
# Per-host descriptions                                                #
# --------------------------------------------------------------------- #


def test_hosting_member_sets_own(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a hosting member may set their own host description."""
    circle = _create_circle(client, auth_headers, host_needed=True)
    host = token_factory(sub="host-1", email="h1@x.test")
    _join(client, host, circle["invite_token"], "Hoster")
    _cycle(client, host, circle["id"], 2)  # -> hosting

    resp = client.put(
        f"/circles/{circle['id']}/day-description/{_DAY}/hosts/me",
        json={"content_delta": _DELTA},
        headers=_headers(host),
    )
    assert resp.status_code == 200

    bundle = client.get(
        f"/circles/{circle['id']}/day-description/{_DAY}",
        headers=auth_headers,
    ).json()
    assert len(bundle["per_host"]) == 1
    assert bundle["per_host"][0]["host_pseudonym"] == "Hoster"


def test_non_hosting_member_cannot_set_own(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a non-hosting member cannot set a host description."""
    circle = _create_circle(client, auth_headers, host_needed=True)
    member = token_factory(sub="nh-1", email="nh1@x.test")
    _join(client, member, circle["invite_token"], "NotHost")
    _cycle(client, member, circle["id"], 1)  # -> attending only

    resp = client.put(
        f"/circles/{circle['id']}/day-description/{_DAY}/hosts/me",
        json={"content_delta": _DELTA},
        headers=_headers(member),
    )
    assert resp.status_code == 403


def test_owner_override_requires_admin(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure owner overrides a host's description; a member cannot."""
    circle = _create_circle(client, auth_headers, host_needed=True)
    host = token_factory(sub="host-2", email="h2@x.test")
    _join(client, host, circle["invite_token"], "Hoster2")
    _cycle(client, host, circle["id"], 2)  # -> hosting
    host_uid = _user_id(client, auth_headers, circle["id"], "Hoster2")

    other = token_factory(sub="other-1", email="o1@x.test")
    _join(client, other, circle["invite_token"], "Other")
    forbidden = client.put(
        f"/circles/{circle['id']}/day-description/{_DAY}/hosts/{host_uid}",
        json={"content_delta": _DELTA},
        headers=_headers(other),
    )
    assert forbidden.status_code == 403

    allowed = client.put(
        f"/circles/{circle['id']}/day-description/{_DAY}/hosts/{host_uid}",
        json={"content_delta": _DELTA},
        headers=auth_headers,
    )
    assert allowed.status_code == 200


def test_per_host_filtered_to_current_hosts(
    client: TestClient,
    auth_headers: dict[str, str],
    token_factory,
) -> None:
    """Ensure a host who stops hosting is dropped from the bundle."""
    circle = _create_circle(client, auth_headers, host_needed=True)
    host = token_factory(sub="host-3", email="h3@x.test")
    _join(client, host, circle["invite_token"], "Hoster3")
    _cycle(client, host, circle["id"], 2)  # -> hosting
    client.put(
        f"/circles/{circle['id']}/day-description/{_DAY}/hosts/me",
        json={"content_delta": _DELTA},
        headers=_headers(host),
    )
    _cycle(client, host, circle["id"], 1)  # hosting -> empty

    bundle = client.get(
        f"/circles/{circle['id']}/day-description/{_DAY}",
        headers=auth_headers,
    ).json()
    assert bundle["per_host"] == []


# --------------------------------------------------------------------- #
# Email folding (db-level unit tests)                                   #
# --------------------------------------------------------------------- #


def _user(db: Session, email: str) -> User:
    user = User(email=email, display_name=email.split("@")[0])
    db.add(user)
    db.flush()
    return user


def _membership(
    db: Session, circle: Circle, user: User, pseudonym: str
) -> None:
    db.add(
        CircleMembership(
            circle_id=circle.id,
            user_id=user.id,
            pseudonym=pseudonym,
            role=MemberRole.member,
        )
    )
    db.flush()


def _viable_event(db: Session, circle: Circle, day: date) -> NotificationEvent:
    event = NotificationEvent(
        circle_id=circle.id, local_date=day, event_type="viable"
    )
    db.add(event)
    db.flush()
    return event


def test_email_includes_circle_wide_description(
    db_session: Session,
) -> None:
    """Ensure a host-free viable day folds its description into email."""
    owner = _user(db_session, "o@x.test")
    circle = Circle(
        name="Hikers",
        timezone="UTC",
        invite_token="AAAAAA",
        created_by_user_id=owner.id,
        host_needed=False,
    )
    db_session.add(circle)
    db_session.flush()
    day = date(2026, 7, 4)
    db_session.add(
        DayDescription(
            circle_id=circle.id,
            local_date=day,
            host_user_id=None,
            content_delta={"ops": [{"insert": "Meet at the bridge\n"}]},
        )
    )
    db_session.flush()
    event = _viable_event(db_session, circle, day)

    ctx = build_event_context(event, db_session)
    rendered = render_notification(ctx, db_session)
    assert "Meet at the bridge" in rendered.text
    assert "Meet at the bridge" in rendered.html


def test_email_includes_per_host_descriptions(
    db_session: Session,
) -> None:
    """Ensure each host's description (labelled) appears in the email."""
    owner = _user(db_session, "o2@x.test")
    other = _user(db_session, "h@x.test")
    circle = Circle(
        name="Hikers",
        timezone="UTC",
        invite_token="BBBBBB",
        created_by_user_id=owner.id,
        host_needed=True,
    )
    db_session.add(circle)
    db_session.flush()
    _membership(db_session, circle, owner, "Alice")
    _membership(db_session, circle, other, "Bob")
    day = date(2026, 7, 4)
    for user, text in ((owner, "Easy loop"), (other, "Summit route")):
        db_session.add(
            DayAvailability(
                circle_id=circle.id,
                user_id=user.id,
                local_date=day,
                state=AvailabilityState.hosting,
            )
        )
        db_session.add(
            DayDescription(
                circle_id=circle.id,
                local_date=day,
                host_user_id=user.id,
                content_delta={"ops": [{"insert": f"{text}\n"}]},
            )
        )
    db_session.flush()
    event = _viable_event(db_session, circle, day)

    ctx = build_event_context(event, db_session)
    rendered = render_notification(ctx, db_session)
    assert "Easy loop" in rendered.html
    assert "Summit route" in rendered.html
    assert "Alice" in rendered.html and "Bob" in rendered.html
