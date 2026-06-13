"""Unit tests for the Web Push notification channel."""

from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_settings import (
    UserNotificationSettings,
    WebPushSubscription,
)
from app.models.user import User
from app.services.notifications.channels import webpush as wp_mod
from app.services.notifications.channels.base import (
    ChannelTarget,
    Recipient,
)
from app.services.notifications.channels.webpush import WebPushChannel
from app.services.notifications.context import EventContext


def _ctx() -> EventContext:
    """Return a minimal event context."""
    return EventContext(
        event_id=uuid.uuid4(),
        circle_id=uuid.uuid4(),
        circle_name="C",
        local_date=date(2026, 6, 20),
        event_type="viable",
        title="T",
        body="B",
        url="http://x/day",
    )


def _vapid_settings() -> SimpleNamespace:
    """Return settings with VAPID keys configured."""
    return SimpleNamespace(
        VAPID_PUBLIC_KEY="pub",
        VAPID_PRIVATE_KEY="priv",
        VAPID_SUBJECT="mailto:ops@x",
    )


def test_collect_targets_loads_subscriptions(
    db_session: Session, monkeypatch
) -> None:
    """Ensure one target per subscription of an enabled recipient."""
    monkeypatch.setattr(wp_mod, "get_settings", _vapid_settings)
    user = User(email="u@x.test")
    db_session.add(user)
    db_session.flush()
    db_session.add_all(
        [
            WebPushSubscription(
                user_id=user.id,
                endpoint="https://push/1",
                p256dh="k1",
                auth="a1",
            ),
            WebPushSubscription(
                user_id=user.id,
                endpoint="https://push/2",
                p256dh="k2",
                auth="a2",
            ),
        ]
    )
    db_session.flush()

    settings = UserNotificationSettings(user_id=user.id, webpush_enabled=True)
    recipient = Recipient(
        user_id=user.id,
        delivery_id=uuid.uuid4(),
        email="u@x.test",
        settings=settings,
    )
    channel = WebPushChannel()
    targets = channel.collect_targets(_ctx(), [recipient], db_session)
    assert sorted(t.address for t in targets) == [
        "https://push/1",
        "https://push/2",
    ]


def test_collect_targets_empty_when_disabled(
    db_session: Session, monkeypatch
) -> None:
    """Ensure a recipient with web push disabled yields no targets."""
    monkeypatch.setattr(wp_mod, "get_settings", _vapid_settings)
    settings = UserNotificationSettings(
        user_id=uuid.uuid4(), webpush_enabled=False
    )
    recipient = Recipient(
        user_id=settings.user_id,
        delivery_id=uuid.uuid4(),
        email="u@x.test",
        settings=settings,
    )
    channel = WebPushChannel()
    assert channel.collect_targets(_ctx(), [recipient], db_session) == []


def test_send_prunes_gone_subscription(
    db_session: Session, monkeypatch
) -> None:
    """Ensure an HTTP 410 from the push service prunes the sub."""
    monkeypatch.setattr(wp_mod, "get_settings", _vapid_settings)
    user = User(email="u@x.test")
    db_session.add(user)
    db_session.flush()
    sub = WebPushSubscription(
        user_id=user.id,
        endpoint="https://push/gone",
        p256dh="k",
        auth="a",
    )
    db_session.add(sub)
    db_session.flush()

    gone = wp_mod.WebPushException("gone")
    gone.response = SimpleNamespace(status_code=410)
    monkeypatch.setattr(wp_mod, "webpush", MagicMock(side_effect=gone))

    channel = WebPushChannel()
    target = ChannelTarget(
        address=sub.endpoint,
        user_id=user.id,
        extra={"p256dh": "k", "auth": "a", "subscription_id": sub.id},
    )
    with pytest.raises(wp_mod.WebPushException):
        channel.send(target, _ctx(), db_session)

    remaining = db_session.execute(
        select(WebPushSubscription).where(WebPushSubscription.id == sub.id)
    ).scalar_one_or_none()
    assert remaining is None
