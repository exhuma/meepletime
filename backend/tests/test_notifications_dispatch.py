"""Unit tests for the channel-agnostic notification dispatcher."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.circle import Circle
from app.models.notification import (
    NotificationChannelAttempt,
    NotificationDelivery,
    NotificationEvent,
)
from app.models.user import User
from app.services.notifications.channels.base import (
    ChannelTarget,
    Recipient,
)
from app.services.notifications.context import EventContext
from app.services.notifications.dispatch import dispatch_event


class _FakeChannel:
    """A per-user channel that fails for one sentinel address."""

    key = "fake"

    def __init__(self) -> None:
        """Record every successful send for assertions."""
        self.sent: list[str] = []

    def collect_targets(
        self,
        ctx: EventContext,
        recipients: list[Recipient],
        db: Session,
    ) -> list[ChannelTarget]:
        """Return one target per recipient, addressed by email."""
        return [
            ChannelTarget(
                address=r.email,
                user_id=r.user_id,
                delivery_id=r.delivery_id,
            )
            for r in recipients
        ]

    def send(
        self, target: ChannelTarget, ctx: EventContext, db: Session
    ) -> None:
        """Fail for the sentinel address, otherwise record success."""
        if target.address.startswith("fail"):
            raise RuntimeError("boom")
        self.sent.append(target.address)


def _seed_event(db: Session) -> tuple[NotificationEvent, dict[str, User]]:
    """Create a circle, two users, an event, and delivery rows."""
    creator = User(email="creator@x.test")
    ok_user = User(email="ok@x.test")
    fail_user = User(email="fail@x.test")
    db.add_all([creator, ok_user, fail_user])
    db.flush()

    circle = Circle(
        name="Test Circle",
        timezone="UTC",
        invite_token="ABCDEF",
        created_by_user_id=creator.id,
    )
    db.add(circle)
    db.flush()

    event = NotificationEvent(
        circle_id=circle.id,
        local_date=date(2026, 6, 20),
        event_type="viable",
    )
    db.add(event)
    db.flush()

    for user in (ok_user, fail_user):
        db.add(
            NotificationDelivery(
                notification_event_id=event.id,
                user_id=user.id,
            )
        )
    db.flush()
    return event, {"ok": ok_user, "fail": fail_user}


def _attempts(
    db: Session, event_id: uuid.UUID
) -> list[NotificationChannelAttempt]:
    """Return all channel attempts for an event."""
    return list(
        db.execute(
            select(NotificationChannelAttempt).where(
                NotificationChannelAttempt.notification_event_id == event_id
            )
        ).scalars()
    )


def test_dispatch_marks_delivered_on_success(
    db_session: Session,
) -> None:
    """Ensure a successful send stamps delivered_at and logs sent."""
    event, users = _seed_event(db_session)
    fake = _FakeChannel()

    dispatch_event(event, db_session, channels=[fake])

    assert fake.sent == ["ok@x.test"]
    deliveries = list(
        db_session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.notification_event_id == event.id
            )
        ).scalars()
    )
    by_user = {d.user_id: d for d in deliveries}
    assert by_user[users["ok"].id].delivered_at is not None
    assert by_user[users["fail"].id].delivered_at is None


def test_dispatch_records_failure(db_session: Session) -> None:
    """Ensure a failed send is recorded without stamping delivered."""
    event, _ = _seed_event(db_session)
    fake = _FakeChannel()

    dispatch_event(event, db_session, channels=[fake])

    attempts = _attempts(db_session, event.id)
    statuses = sorted(a.status for a in attempts)
    assert statuses == ["failed", "sent"]
    failed = next(a for a in attempts if a.status == "failed")
    assert failed.error == "boom"
    assert failed.channel == "fake"


def test_dispatch_no_channels_is_noop(db_session: Session) -> None:
    """Ensure dispatch with no channels records no attempts."""
    event, _ = _seed_event(db_session)

    dispatch_event(event, db_session, channels=[])

    assert _attempts(db_session, event.id) == []


def test_load_recipients_prefers_notification_email(
    db_session: Session,
) -> None:
    """A confirmed notification_email overrides the profile email."""
    from app.models.notification_settings import (
        UserNotificationSettings,
    )
    from app.services.notifications.dispatch import _load_recipients

    event, users = _seed_event(db_session)
    db_session.add(
        UserNotificationSettings(
            user_id=users["ok"].id,
            email_enabled=True,
            notification_email="notify@x.test",
        )
    )
    db_session.flush()

    recipients = _load_recipients(event, db_session)
    by_user = {r.user_id: r for r in recipients}
    # ok_user has a confirmed notification address -> it wins.
    assert by_user[users["ok"].id].email == "notify@x.test"
    # fail_user has no settings row -> falls back to profile email.
    assert by_user[users["fail"].id].email == "fail@x.test"
