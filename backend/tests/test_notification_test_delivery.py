"""Unit tests for the test-notification delivery helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.circle import Circle
from app.models.notification_settings import (
    CircleTelegramConfig,
    TelegramMemberLink,
)
from app.models.user import User
from app.services import email as email_svc
from app.services.notifications import test_delivery as td


def _user(db: Session, email: str = "u@x.test") -> User:
    """Create and return a persisted user."""
    user = User(email=email)
    db.add(user)
    db.flush()
    return user


def test_email_test_ok_when_configured(
    db_session: Session, monkeypatch
) -> None:
    """Ensure a configured email channel reports a successful test."""
    user = _user(db_session)
    monkeypatch.setattr(
        email_svc,
        "get_settings",
        lambda: SimpleNamespace(
            SMTP_HOST="smtp.test",
            SMTP_PORT=587,
            SMTP_FROM="from@test",
            SMTP_USE_TLS=True,
            SMTP_USERNAME=None,
            SMTP_PASSWORD=None,
        ),
    )
    smtp = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = smtp
    monkeypatch.setattr(
        email_svc.smtplib, "SMTP_SSL", MagicMock(return_value=ctx)
    )

    ok, message = td.send_user_test(db_session, user, "email")
    assert ok is True
    assert "test" in message.lower()
    smtp.send_message.assert_called_once()


def test_email_test_reports_unconfigured(
    db_session: Session,
) -> None:
    """Ensure an unconfigured email channel reports a clear failure."""
    user = _user(db_session)
    ok, message = td.send_user_test(db_session, user, "email")
    assert ok is False
    assert "configured" in message.lower()


def test_webpush_test_reports_unconfigured(
    db_session: Session,
) -> None:
    """Ensure web push with no VAPID config reports a clear failure."""
    user = _user(db_session)
    ok, message = td.send_user_test(db_session, user, "webpush")
    assert ok is False
    assert "configured" in message.lower()


def test_telegram_dm_test_requires_link(
    db_session: Session,
) -> None:
    """Ensure a user with no DM links gets a clear message."""
    user = _user(db_session)
    ok, message = td.send_user_test(db_session, user, "telegram")
    assert ok is False
    assert "link" in message.lower()


def test_telegram_dm_test_sends_to_links(
    db_session: Session, monkeypatch
) -> None:
    """Ensure the DM test sends to each linked chat across circles."""
    user = _user(db_session)
    circle = Circle(
        name="C",
        timezone="UTC",
        invite_token="AAAAAA",
        created_by_user_id=user.id,
    )
    db_session.add(circle)
    db_session.flush()
    config = CircleTelegramConfig(
        circle_id=circle.id,
        label="DM",
        bot_token="tokD",
        mode="dm",
        group_chat_id=None,
    )
    db_session.add(config)
    db_session.flush()
    db_session.add(
        TelegramMemberLink(
            circle_telegram_config_id=config.id,
            user_id=user.id,
            chat_id="999",
        )
    )
    db_session.flush()

    sent = MagicMock()
    monkeypatch.setattr(td, "send_message", sent)
    ok, message = td.send_user_test(db_session, user, "telegram")
    assert ok is True
    sent.assert_called_once_with("tokD", "999", sent.call_args.args[2])


def test_circle_group_test_requires_chat(
    db_session: Session,
) -> None:
    """Ensure a group bot with no chat id reports a clear failure."""
    user = _user(db_session)
    circle = Circle(
        name="C",
        timezone="UTC",
        invite_token="BBBBBB",
        created_by_user_id=user.id,
    )
    db_session.add(circle)
    db_session.flush()
    config = CircleTelegramConfig(
        circle_id=circle.id,
        label="G",
        bot_token="tokG",
        mode="group",
        group_chat_id=None,
    )
    db_session.add(config)
    db_session.flush()

    ok, message = td.send_circle_telegram_test(db_session, config, user)
    assert ok is False
    assert "chat" in message.lower()


def test_circle_group_test_sends(db_session: Session, monkeypatch) -> None:
    """Ensure a configured group bot posts a test to the group chat."""
    user = _user(db_session)
    circle = Circle(
        name="C",
        timezone="UTC",
        invite_token="CCCCCC",
        created_by_user_id=user.id,
    )
    db_session.add(circle)
    db_session.flush()
    config = CircleTelegramConfig(
        circle_id=circle.id,
        label="G",
        bot_token="tokG",
        mode="group",
        group_chat_id="-100",
    )
    db_session.add(config)
    db_session.flush()

    sent = MagicMock()
    monkeypatch.setattr(td, "send_message", sent)
    ok, message = td.send_circle_telegram_test(db_session, config, user)
    assert ok is True
    assert sent.call_args.args[0] == "tokG"
    assert sent.call_args.args[1] == "-100"
