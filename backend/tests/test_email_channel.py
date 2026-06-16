"""Unit tests for the SMTP email notification channel."""

from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.notification_settings import UserNotificationSettings
from app.services import email as email_svc
from app.services.notifications.channels.base import (
    ChannelTarget,
    Recipient,
)
from app.services.notifications.channels.email import EmailChannel
from app.services.notifications.context import EventContext


def _ctx() -> EventContext:
    """Return a minimal event context for sending."""
    return EventContext(
        event_id=uuid.uuid4(),
        circle_id=uuid.uuid4(),
        circle_name="Test Circle",
        local_date=date(2026, 6, 20),
        event_type="viable",
        title="Test Circle: a day is now viable",
        body="2026-06-20 is now viable.",
        url="http://localhost:5173/circles/x/day/2026-06-20",
    )


def _recipient(email: str, enabled: bool) -> Recipient:
    """Return a recipient with the given email flag."""
    settings = UserNotificationSettings(
        user_id=uuid.uuid4(),
        email_enabled=enabled,
        webpush_enabled=False,
        telegram_dm_enabled=False,
    )
    return Recipient(
        user_id=settings.user_id,
        delivery_id=uuid.uuid4(),
        email=email,
        settings=settings,
    )


def _smtp_settings(**overrides: object) -> SimpleNamespace:
    """Return SMTP-configured settings for the email module."""
    base = dict(
        SMTP_HOST="smtp.test",
        SMTP_PORT=587,
        SMTP_FROM="noreply@test",
        SMTP_USE_TLS=True,
        SMTP_USERNAME="user",
        SMTP_PASSWORD="pass",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_collect_targets_skips_when_unconfigured(monkeypatch) -> None:
    """Ensure no targets are produced when SMTP is unconfigured."""
    monkeypatch.setattr(
        email_svc,
        "get_settings",
        lambda: SimpleNamespace(SMTP_HOST=None, SMTP_FROM=None),
    )
    channel = EmailChannel()
    targets = channel.collect_targets(
        _ctx(), [_recipient("a@x.test", True)], db=None
    )
    assert targets == []


def test_collect_targets_honors_enabled_flag(monkeypatch) -> None:
    """Ensure only recipients with email enabled get a target."""
    monkeypatch.setattr(email_svc, "get_settings", lambda: _smtp_settings())
    channel = EmailChannel()
    recipients = [
        _recipient("on@x.test", True),
        _recipient("off@x.test", False),
    ]
    targets = channel.collect_targets(_ctx(), recipients, db=None)
    assert [t.address for t in targets] == ["on@x.test"]


def _no_image_db() -> MagicMock:
    """Return a DB stub whose image lookup yields nothing."""
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    return db


def test_send_builds_multipart_html_with_text_fallback(monkeypatch) -> None:
    """Ensure send builds an HTML email with the plain-text fallback."""
    monkeypatch.setattr(email_svc, "get_settings", lambda: _smtp_settings())
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        email_svc, "_deliver", lambda message: captured.update(message=message)
    )

    ctx = _ctx()
    EmailChannel().send(
        ChannelTarget(address="to@x.test"), ctx, db=_no_image_db()
    )

    message = captured["message"]
    assert message.get_content_type() == "multipart/alternative"
    # The plain-text alternative is byte-for-byte the legacy body.
    plain = message.get_body(("plain",)).get_content()
    assert plain == f"{ctx.body}\n\n{ctx.url}\n"
    html = message.get_body(("html",)).get_content()
    assert ctx.title in html
    # No stored image -> gradient/initials hero, not a CID image.
    assert "cid:hero" not in html
    assert "linear-gradient" in html


def test_deliver_uses_ssl_login_and_send(monkeypatch) -> None:
    """Ensure delivery opens SMTP_SSL, logs in, and sends the message."""
    monkeypatch.setattr(email_svc, "get_settings", lambda: _smtp_settings())
    smtp = MagicMock()
    smtp_ctx = MagicMock()
    smtp_ctx.__enter__.return_value = smtp
    smtp_factory = MagicMock(return_value=smtp_ctx)
    monkeypatch.setattr(email_svc.smtplib, "SMTP_SSL", smtp_factory)

    EmailChannel().send(
        ChannelTarget(address="to@x.test"), _ctx(), db=_no_image_db()
    )

    args, kwargs = smtp_factory.call_args
    assert args[0] == "smtp.test"
    assert args[1] == 587
    assert kwargs["timeout"] == 5
    smtp.ehlo.assert_called_once()
    smtp.login.assert_called_once_with("user", "pass")
    smtp.send_message.assert_called_once()
