"""Tests for batched, aggregated notification evaluation and dispatch."""

from __future__ import annotations

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.availability import AvailabilityState, DayAvailability
from app.models.circle import Circle
from app.models.membership import CircleMembership, MemberRole
from app.models.notification import (
    NotificationChannelAttempt,
    NotificationDelivery,
    NotificationEvent,
)
from app.models.user import User
from app.services.notifications import dispatch as dispatch_mod
from app.services.notifications.channels.base import ChannelTarget
from app.services.notifications.context import (
    build_batch_context,
    build_event_context,
)
from app.services.notifications.dispatch import dispatch_batch
from app.services.notifications.evaluation import evaluate_and_notify_batch

_D1 = date(2026, 6, 20)
_D2 = date(2026, 6, 21)
_D3 = date(2026, 6, 22)


class _FakeChannel:
    """A per-user channel that fails for one sentinel address."""

    key = "fake"

    def __init__(self) -> None:
        """Record every successful send for assertions."""
        self.sent: list[str] = []

    def collect_targets(self, ctx, recipients, db):
        """Return one target per recipient, addressed by email."""
        return [
            ChannelTarget(
                address=r.email,
                user_id=r.user_id,
                delivery_id=r.delivery_id,
            )
            for r in recipients
        ]

    def send(self, target, ctx, db) -> None:
        """Fail for the sentinel address, otherwise record success."""
        if target.address.startswith("fail"):
            raise RuntimeError("boom")
        self.sent.append(target.address)


def _user(db: Session, email: str) -> User:
    """Persist and return a user."""
    user = User(email=email, display_name=email.split("@")[0])
    db.add(user)
    db.flush()
    return user


def _circle(db: Session, owner: User, **kwargs: object) -> Circle:
    """Persist and return a circle owned by *owner*."""
    circle = Circle(
        name="Test Circle",
        timezone="UTC",
        invite_token=kwargs.pop("invite_token", "ABCDEF"),
        created_by_user_id=owner.id,
        **kwargs,
    )
    db.add(circle)
    db.flush()
    return circle


def _member(db: Session, circle: Circle, user: User) -> None:
    """Add *user* as a member of *circle*."""
    db.add(
        CircleMembership(
            circle_id=circle.id,
            user_id=user.id,
            pseudonym=user.email.split("@")[0],
            role=MemberRole.member,
        )
    )
    db.flush()


def _mark(
    db: Session,
    circle: Circle,
    user: User,
    day: date,
    state: AvailabilityState,
) -> None:
    """Record an availability for *user* in *circle* on *day*."""
    db.add(
        DayAvailability(
            circle_id=circle.id,
            user_id=user.id,
            local_date=day,
            state=state,
        )
    )
    db.flush()


def _event(
    db: Session, circle: Circle, day: date, kind: str
) -> NotificationEvent:
    """Persist and return a notification event."""
    event = NotificationEvent(
        circle_id=circle.id, local_date=day, event_type=kind
    )
    db.add(event)
    db.flush()
    return event


def _delivery(db: Session, event: NotificationEvent, user: User) -> None:
    """Persist a delivery row linking *event* to *user*."""
    db.add(
        NotificationDelivery(notification_event_id=event.id, user_id=user.id)
    )
    db.flush()


def test_single_event_context_matches_single_day(
    db_session: Session,
) -> None:
    """Ensure a batch of one reproduces the single-day wording."""
    owner = _user(db_session, "a@x.test")
    circle = _circle(db_session, owner)
    event = _event(db_session, circle, _D1, "viable")

    batch = build_batch_context([event], db_session)
    single = build_event_context(event, db_session)

    assert batch.title == single.title
    assert batch.body == single.body
    assert batch.url == single.url
    assert batch.event_type == single.event_type


def test_batch_context_summarizes_multiple_days(
    db_session: Session,
) -> None:
    """Ensure a multi-day batch links to the calendar and lists days."""
    owner = _user(db_session, "a@x.test")
    circle = _circle(db_session, owner)
    viable = _event(db_session, circle, _D1, "viable")
    forming = _event(db_session, circle, _D2, "non_viable_candidate")

    # Pass unsorted to confirm the builder orders by date.
    ctx = build_batch_context([forming, viable], db_session)

    assert ctx.url.endswith(f"/circles/{circle.id}")
    assert "/day/" not in ctx.url
    assert "viable" in ctx.title and "forming" in ctx.title
    assert f"- {_D1}: now viable" in ctx.body
    assert f"- {_D2}: candidate forming" in ctx.body
    # D1 (viable) is earliest, so it appears before D2 in the body.
    assert ctx.body.index(str(_D1)) < ctx.body.index(str(_D2))


def test_dispatch_batch_sends_once_per_recipient(
    db_session: Session,
) -> None:
    """Ensure one aggregated send covers all of a recipient's days."""
    owner = _user(db_session, "a@x.test")
    ok_user = _user(db_session, "ok@x.test")
    circle = _circle(db_session, owner)
    e1 = _event(db_session, circle, _D1, "viable")
    e2 = _event(db_session, circle, _D2, "non_viable_candidate")
    for event in (e1, e2):
        _delivery(db_session, event, ok_user)

    fake = _FakeChannel()
    dispatch_batch([e1, e2], db_session, channels=[fake])

    # One physical send for the recipient, not one per day.
    assert fake.sent == ["ok@x.test"]
    # Every delivery across both days is stamped delivered.
    deliveries = list(
        db_session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.user_id == ok_user.id
            )
        ).scalars()
    )
    assert len(deliveries) == 2
    assert all(d.delivered_at is not None for d in deliveries)
    # One attempt is audited per delivery (per day).
    attempts = list(
        db_session.execute(select(NotificationChannelAttempt)).scalars()
    )
    assert len(attempts) == 2
    assert {a.notification_event_id for a in attempts} == {e1.id, e2.id}


def test_dispatch_batch_records_failure_without_delivery(
    db_session: Session,
) -> None:
    """Ensure a failed send is audited but not marked delivered."""
    owner = _user(db_session, "a@x.test")
    fail_user = _user(db_session, "fail@x.test")
    circle = _circle(db_session, owner)
    e1 = _event(db_session, circle, _D1, "viable")
    e2 = _event(db_session, circle, _D2, "viable")
    for event in (e1, e2):
        _delivery(db_session, event, fail_user)

    fake = _FakeChannel()
    dispatch_batch([e1, e2], db_session, channels=[fake])

    assert fake.sent == []
    attempts = list(
        db_session.execute(select(NotificationChannelAttempt)).scalars()
    )
    assert len(attempts) == 2
    assert all(a.status == "failed" for a in attempts)
    deliveries = list(
        db_session.execute(select(NotificationDelivery)).scalars()
    )
    assert all(d.delivered_at is None for d in deliveries)


def test_evaluate_batch_creates_event_per_day(
    db_session: Session,
    monkeypatch,
) -> None:
    """Ensure each qualifying day yields one event and one summary."""
    fake = _FakeChannel()
    monkeypatch.setattr(dispatch_mod, "iter_channels", lambda: [fake])

    owner = _user(db_session, "owner@x.test")
    attendee = _user(db_session, "att@x.test")
    circle = _circle(db_session, owner, host_needed=True)
    _member(db_session, circle, owner)
    _member(db_session, circle, attendee)

    _mark(db_session, circle, owner, _D1, AvailabilityState.hosting)
    _mark(db_session, circle, attendee, _D2, AvailabilityState.attending)
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1, _D2, _D3], db_session)

    events = list(db_session.execute(select(NotificationEvent)).scalars())
    by_date = {e.local_date: e.event_type for e in events}
    # D1 hosting -> viable; D2 attending only (host needed) -> candidate;
    # D3 has no availability -> no event.
    assert by_date == {
        _D1: "viable",
        _D2: "non_viable_candidate",
    }
    # A single aggregated send per recipient (two members).
    assert sorted(fake.sent) == ["att@x.test", "owner@x.test"]


def test_evaluate_batch_anti_storm_suppresses_repeat(
    db_session: Session,
    monkeypatch,
) -> None:
    """Ensure a repeated in-window day produces no new event or send."""
    fake = _FakeChannel()
    monkeypatch.setattr(dispatch_mod, "iter_channels", lambda: [fake])

    owner = _user(db_session, "owner@x.test")
    circle = _circle(db_session, owner)
    _member(db_session, circle, owner)
    _mark(db_session, circle, owner, _D1, AvailabilityState.attending)
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1], db_session)
    assert fake.sent == ["owner@x.test"]

    fake.sent.clear()
    evaluate_and_notify_batch(circle.id, [_D1], db_session)

    events = list(
        db_session.execute(
            select(NotificationEvent).where(NotificationEvent.local_date == _D1)
        ).scalars()
    )
    assert len(events) == 1  # second evaluation suppressed
    assert fake.sent == []  # no event -> no send


def _latest_event(db: Session, day: date) -> NotificationEvent:
    """Return the most recently created event for *day*."""
    return (
        db.execute(
            select(NotificationEvent)
            .where(NotificationEvent.local_date == day)
            .order_by(NotificationEvent.created_at.desc())
            .limit(1)
        )
        .scalars()
        .one()
    )


def test_dropping_below_minimum_notifies_no_longer_viable(
    db_session: Session,
    monkeypatch,
) -> None:
    """A viable day losing a participant emits a lost-viability event."""
    fake = _FakeChannel()
    monkeypatch.setattr(dispatch_mod, "iter_channels", lambda: [fake])

    owner = _user(db_session, "owner@x.test")
    other = _user(db_session, "other@x.test")
    circle = _circle(db_session, owner, minimum_attendees=2)
    _member(db_session, circle, owner)
    _member(db_session, circle, other)
    _mark(db_session, circle, owner, _D1, AvailabilityState.attending)
    _mark(db_session, circle, other, _D1, AvailabilityState.attending)
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1], db_session)
    assert _latest_event(db_session, _D1).event_type == "viable"

    # One participant leaves -> count drops below the minimum.
    db_session.execute(
        delete(DayAvailability).where(
            DayAvailability.user_id == other.id,
            DayAvailability.local_date == _D1,
        )
    )
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1], db_session)

    lost = _latest_event(db_session, _D1)
    assert lost.event_type == "no_longer_viable"
    ctx = build_event_context(lost, db_session)
    assert "no longer" in ctx.title.lower()
    assert "no longer" in ctx.body.lower()
    assert "forming" not in ctx.body.lower()


def test_emptied_viable_day_notifies_no_longer_viable(
    db_session: Session,
    monkeypatch,
) -> None:
    """A viable day losing *all* attendees still notifies, not silence."""
    fake = _FakeChannel()
    monkeypatch.setattr(dispatch_mod, "iter_channels", lambda: [fake])

    owner = _user(db_session, "owner@x.test")
    circle = _circle(db_session, owner)
    _member(db_session, circle, owner)
    _mark(db_session, circle, owner, _D1, AvailabilityState.attending)
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1], db_session)
    assert _latest_event(db_session, _D1).event_type == "viable"

    db_session.execute(
        delete(DayAvailability).where(DayAvailability.local_date == _D1)
    )
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1], db_session)
    assert _latest_event(db_session, _D1).event_type == "no_longer_viable"


def test_emptied_forming_day_stays_silent(
    db_session: Session,
    monkeypatch,
) -> None:
    """A never-viable candidate emptying to zero is not 'no longer viable'."""
    fake = _FakeChannel()
    monkeypatch.setattr(dispatch_mod, "iter_channels", lambda: [fake])

    owner = _user(db_session, "owner@x.test")
    attendee = _user(db_session, "att@x.test")
    circle = _circle(db_session, owner, host_needed=True)
    _member(db_session, circle, owner)
    _member(db_session, circle, attendee)
    # Attending only with host required -> candidate forming, never viable.
    _mark(db_session, circle, attendee, _D1, AvailabilityState.attending)
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1], db_session)
    assert _latest_event(db_session, _D1).event_type == "non_viable_candidate"

    db_session.execute(
        delete(DayAvailability).where(DayAvailability.local_date == _D1)
    )
    db_session.commit()

    evaluate_and_notify_batch(circle.id, [_D1], db_session)

    events = list(
        db_session.execute(
            select(NotificationEvent).where(NotificationEvent.local_date == _D1)
        ).scalars()
    )
    # No new event, and nothing mislabeled as a lost-viability transition.
    assert len(events) == 1
    assert all(e.event_type != "no_longer_viable" for e in events)


def test_single_no_longer_viable_event_context(
    db_session: Session,
) -> None:
    """The single-day wording for a lost-viability event is explicit."""
    owner = _user(db_session, "a@x.test")
    circle = _circle(db_session, owner)
    event = _event(db_session, circle, _D1, "no_longer_viable")

    ctx = build_event_context(event, db_session)

    assert "no longer" in ctx.title.lower()
    assert "no longer" in ctx.body.lower()
    assert "forming" not in ctx.body.lower()


def test_batch_context_distinguishes_lost_viability(
    db_session: Session,
) -> None:
    """A mixed batch lists and counts all three transition types."""
    owner = _user(db_session, "a@x.test")
    circle = _circle(db_session, owner)
    viable = _event(db_session, circle, _D1, "viable")
    lost = _event(db_session, circle, _D2, "no_longer_viable")
    forming = _event(db_session, circle, _D3, "non_viable_candidate")

    ctx = build_batch_context([forming, lost, viable], db_session)

    assert f"- {_D1}: now viable" in ctx.body
    assert f"- {_D2}: no longer viable" in ctx.body
    assert f"- {_D3}: candidate forming" in ctx.body
    assert "1 viable" in ctx.title
    assert "1 no longer viable" in ctx.title
    assert "1 forming" in ctx.title
