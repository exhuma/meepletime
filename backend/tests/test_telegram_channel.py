"""Unit tests for the circle-scoped Telegram channel."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.circle import Circle
from app.models.notification_settings import (
    CircleTelegramConfig,
    TelegramMemberLink,
    UserNotificationSettings,
)
from app.models.user import User
from app.services.notifications.channels import telegram as tg_mod
from app.services.notifications.channels.base import ChannelTarget, Recipient
from app.services.notifications.channels.telegram import TelegramChannel
from app.services.notifications.context import EventContext


def _ctx(circle_id: uuid.UUID) -> EventContext:
    """Return a minimal event context for a circle."""
    return EventContext(
        event_id=uuid.uuid4(),
        circle_id=circle_id,
        circle_name="C",
        local_date=date(2026, 6, 20),
        event_type="viable",
        title="T",
        body="B",
        url="http://x/day",
    )


def _circle(db: Session) -> Circle:
    """Create and return a persisted circle."""
    creator = User(email="c@x.test")
    db.add(creator)
    db.flush()
    circle = Circle(
        name="C",
        timezone="UTC",
        invite_token="AAAAAA",
        created_by_user_id=creator.id,
    )
    db.add(circle)
    db.flush()
    return circle


def test_collect_targets_group_mode(db_session: Session) -> None:
    """Ensure group-mode configs with a chat id yield one target each."""
    circle = _circle(db_session)
    db_session.add_all(
        [
            CircleTelegramConfig(
                circle_id=circle.id,
                label="Group A",
                bot_token="tokenA",
                mode="group",
                group_chat_id="-1001",
            ),
            # group mode but no chat id yet -> not deliverable
            CircleTelegramConfig(
                circle_id=circle.id,
                label="Unconfigured",
                bot_token="tokenB",
                mode="group",
                group_chat_id=None,
            ),
        ]
    )
    db_session.flush()

    channel = TelegramChannel()
    targets = channel.collect_targets(_ctx(circle.id), [], db_session)
    assert len(targets) == 1
    assert targets[0].address == "-1001"
    assert targets[0].extra["bot_token"] == "tokenA"
    assert targets[0].user_id is None


def _dm_recipient(user_id, enabled: bool) -> Recipient:
    """Return a recipient with the given Telegram-DM opt-in."""
    settings = UserNotificationSettings(
        user_id=user_id, telegram_dm_enabled=enabled
    )
    return Recipient(
        user_id=user_id,
        delivery_id=uuid.uuid4(),
        email="x@x.test",
        settings=settings,
    )


def test_dm_targets_require_link_and_optin(db_session: Session) -> None:
    """Ensure DM targets need both a link and a global opt-in."""
    circle = _circle(db_session)
    linked = User(email="l@x.test")
    unlinked = User(email="u@x.test")
    opted_out = User(email="o@x.test")
    db_session.add_all([linked, unlinked, opted_out])
    db_session.flush()

    config = CircleTelegramConfig(
        circle_id=circle.id,
        label="DM bot",
        bot_token="tokD",
        mode="dm",
        group_chat_id=None,
    )
    db_session.add(config)
    db_session.flush()
    # Both linked + opted_out have a chat link; only opt-in matters next.
    db_session.add_all(
        [
            TelegramMemberLink(
                circle_telegram_config_id=config.id,
                user_id=linked.id,
                chat_id="555",
            ),
            TelegramMemberLink(
                circle_telegram_config_id=config.id,
                user_id=opted_out.id,
                chat_id="666",
            ),
        ]
    )
    db_session.flush()

    recipients = [
        _dm_recipient(linked.id, enabled=True),
        _dm_recipient(unlinked.id, enabled=True),  # opted in, no link
        _dm_recipient(opted_out.id, enabled=False),  # linked, opted out
    ]
    channel = TelegramChannel()
    targets = channel.collect_targets(_ctx(circle.id), recipients, db_session)
    assert len(targets) == 1
    assert targets[0].address == "555"
    assert targets[0].user_id == linked.id
    assert targets[0].extra["bot_token"] == "tokD"


def test_send_calls_telegram_api(monkeypatch) -> None:
    """Ensure send forwards chat id, token, and text to the API."""
    sent = MagicMock()
    monkeypatch.setattr(tg_mod, "send_message", sent)
    channel = TelegramChannel()
    target = ChannelTarget(address="-1001", extra={"bot_token": "tokenA"})
    channel.send(target, _ctx(uuid.uuid4()), db=None)
    sent.assert_called_once()
    args = sent.call_args.args
    assert args[0] == "tokenA"
    assert args[1] == "-1001"
    assert "T" in args[2]
