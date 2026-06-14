"""Unit tests for the ``next_viable_date`` viability helper."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.availability import AvailabilityState, DayAvailability
from app.models.circle import Circle
from app.models.user import User
from app.services.viability import next_viable_date

_TODAY = date(2026, 6, 14)


def _make_user(db: Session, email: str) -> User:
    """Persist and return a user with the given email."""
    user = User(email=email, display_name=email.split("@")[0])
    db.add(user)
    db.flush()
    return user


def _make_circle(db: Session, owner: User, **kwargs: object) -> Circle:
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


def _mark(
    db: Session,
    circle: Circle,
    user: User,
    day: date,
    state: AvailabilityState = AvailabilityState.attending,
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


def test_returns_none_without_availabilities(db_session: Session) -> None:
    """Ensure a circle with no availabilities yields no viable date."""
    owner = _make_user(db_session, "a@x.test")
    circle = _make_circle(db_session, owner)
    assert next_viable_date(circle, db_session, today=_TODAY) is None


def test_returns_upcoming_viable_day(db_session: Session) -> None:
    """Ensure an upcoming attended day is reported as viable."""
    owner = _make_user(db_session, "a@x.test")
    circle = _make_circle(db_session, owner)
    target = _TODAY + timedelta(days=3)
    _mark(db_session, circle, owner, target)
    assert next_viable_date(circle, db_session, today=_TODAY) == target


def test_ignores_past_viable_day(db_session: Session) -> None:
    """Ensure a viable day before today is not returned."""
    owner = _make_user(db_session, "a@x.test")
    circle = _make_circle(db_session, owner)
    _mark(db_session, circle, owner, _TODAY - timedelta(days=2))
    assert next_viable_date(circle, db_session, today=_TODAY) is None


def test_returns_earliest_of_several(db_session: Session) -> None:
    """Ensure the earliest upcoming viable day wins."""
    owner = _make_user(db_session, "a@x.test")
    circle = _make_circle(db_session, owner)
    later = _TODAY + timedelta(days=10)
    earlier = _TODAY + timedelta(days=4)
    _mark(db_session, circle, owner, later)
    _mark(db_session, circle, owner, earlier)
    assert next_viable_date(circle, db_session, today=_TODAY) == earlier


def test_host_needed_without_host_is_not_viable(db_session: Session) -> None:
    """Ensure a host-required circle skips days with no host."""
    owner = _make_user(db_session, "a@x.test")
    circle = _make_circle(db_session, owner, host_needed=True)
    # Attendee present but nobody hosting -> not viable.
    _mark(db_session, circle, owner, _TODAY + timedelta(days=2))
    assert next_viable_date(circle, db_session, today=_TODAY) is None


def test_host_needed_with_host_is_viable(db_session: Session) -> None:
    """Ensure a host-required circle returns a day that has a host."""
    owner = _make_user(db_session, "a@x.test")
    circle = _make_circle(db_session, owner, host_needed=True)
    target = _TODAY + timedelta(days=2)
    _mark(db_session, circle, owner, target, AvailabilityState.hosting)
    assert next_viable_date(circle, db_session, today=_TODAY) == target
