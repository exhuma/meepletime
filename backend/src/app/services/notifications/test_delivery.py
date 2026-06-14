"""Synchronous "send a real test notification" helpers.

Used by the test endpoints so a user (or admin) can verify a channel
end to end. Unlike the scheduler path these run in the request thread
(FastAPI threadpool), so they send synchronously and return a
``(ok, message)`` result instead of writing delivery/attempt rows.

A test bypasses the user's on/off preference for the channel — it
verifies the *mechanism*, not the toggle — by forcing the tested
channel enabled on a transient settings object.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.notification_settings import (
    CHANNEL_EMAIL,
    CHANNEL_TELEGRAM,
    CHANNEL_WEBPUSH,
    TELEGRAM_MODE_DM,
    CircleTelegramConfig,
    TelegramMemberLink,
    UserNotificationSettings,
)
from app.models.user import User
from app.services.notification_settings import get_or_create_settings
from app.services.notifications.channels import (
    get_channel,
    register_default_channels,
)
from app.services.notifications.channels.base import Recipient
from app.services.notifications.context import EventContext
from app.services.telegram_api import send_message

_TEST_TITLE = "MeepleTime test notification"
_TEST_BODY = "If you can read this, your notifications are working."


def _test_context() -> EventContext:
    """
    Return a synthetic context for a test notification.

    :returns: An :class:`EventContext` with test copy and the app URL.
    """
    return EventContext(
        event_id=uuid.uuid4(),
        circle_id=uuid.uuid4(),
        circle_name="MeepleTime",
        local_date=datetime.now(UTC).date(),
        event_type="test",
        title=_TEST_TITLE,
        body=_TEST_BODY,
        url=get_settings().APP_BASE_URL.rstrip("/"),
    )


def _forced_settings(
    user_id: uuid.UUID, channel_key: str
) -> UserNotificationSettings:
    """
    Return transient settings with only *channel_key* enabled.

    :param user_id: The user being tested.
    :param channel_key: The channel to force on.
    :returns: An unsaved settings object.
    """
    return UserNotificationSettings(
        user_id=user_id,
        email_enabled=channel_key == CHANNEL_EMAIL,
        webpush_enabled=channel_key == CHANNEL_WEBPUSH,
        telegram_dm_enabled=channel_key == CHANNEL_TELEGRAM,
    )


def _empty_target_message(channel_key: str) -> str:
    """
    Return a friendly message when a channel has no test target.

    :param channel_key: The channel that produced no targets.
    :returns: A human-readable explanation.
    """
    if channel_key == CHANNEL_EMAIL:
        return "Email delivery isn't configured on this server."
    settings = get_settings()
    configured = bool(
        settings.VAPID_PUBLIC_KEY
        and settings.VAPID_PRIVATE_KEY
        and settings.VAPID_SUBJECT
    )
    if not configured:
        return "Browser notifications aren't configured on this server."
    return (
        "No browser is subscribed yet — enable browser notifications "
        "on this device first."
    )


def _resolved_email(db: Session, user: User) -> str:
    """
    Return the address real notifications would use for this user.

    Prefers the confirmed notification email, falling back to the
    account (profile) email.

    :param db: Active database session.
    :param user: The user being tested.
    :returns: The effective email address.
    """
    settings = get_or_create_settings(db, user.id)
    return settings.notification_email or user.email


def _send_via_channel(
    channel_key: str, user: User, db: Session
) -> tuple[bool, str]:
    """
    Run a per-user channel test (email or web push).

    :param channel_key: ``email`` or ``webpush``.
    :param user: The user to deliver the test to.
    :param db: Active database session.
    :returns: ``(ok, message)``.
    """
    register_default_channels()
    channel = get_channel(channel_key)
    if channel is None:
        return False, "That channel is not available."

    ctx = _test_context()
    recipient = Recipient(
        user_id=user.id,
        delivery_id=None,
        email=_resolved_email(db, user),
        settings=_forced_settings(user.id, channel_key),
    )
    targets = channel.collect_targets(ctx, [recipient], db)
    if not targets:
        return False, _empty_target_message(channel_key)

    failures = [_try_send(channel, target, ctx, db) for target in targets]
    failed = [f for f in failures if f]
    if failed:
        return False, f"Delivery failed: {failed[0]}"
    return True, f"Sent a test to {len(targets)} target(s)."


def _try_send(channel, target, ctx: EventContext, db: Session) -> str:
    """
    Send one target, returning an error string or ``""`` on success.

    :param channel: The channel performing the send.
    :param target: The target to deliver to.
    :param ctx: The test event context.
    :param db: Active database session.
    :returns: Empty string on success, else the error message.
    """
    try:
        channel.send(target, ctx, db)
        return ""
    except Exception as exc:
        return str(exc)[:160]


def _send_telegram_dm_test(user: User, db: Session) -> tuple[bool, str]:
    """
    Send a test DM to every DM chat the user has linked.

    :param user: The user whose links to use.
    :param db: Active database session.
    :returns: ``(ok, message)``.
    """
    rows = db.execute(
        select(TelegramMemberLink, CircleTelegramConfig)
        .join(
            CircleTelegramConfig,
            CircleTelegramConfig.id
            == TelegramMemberLink.circle_telegram_config_id,
        )
        .where(
            TelegramMemberLink.user_id == user.id,
            CircleTelegramConfig.mode == TELEGRAM_MODE_DM,
        )
    ).all()
    if not rows:
        return False, "You haven't linked any Telegram DM chats yet."

    text = f"{_TEST_TITLE}\n\n{_TEST_BODY}"
    failures: list[str] = []
    for link, config in rows:
        try:
            send_message(config.bot_token, link.chat_id, text)
        except Exception as exc:
            failures.append(str(exc)[:160])
    if failures:
        return False, f"Telegram rejected the test: {failures[0]}"
    return True, f"Sent a test DM to {len(rows)} linked chat(s)."


def send_user_test(
    db: Session, user: User, channel_key: str
) -> tuple[bool, str]:
    """
    Send a real test notification to the user on one channel.

    :param db: Active database session.
    :param user: The authenticated user.
    :param channel_key: ``email`` / ``webpush`` / ``telegram``.
    :returns: ``(ok, message)`` describing the outcome.
    """
    if channel_key == CHANNEL_TELEGRAM:
        return _send_telegram_dm_test(user, db)
    if channel_key in (CHANNEL_EMAIL, CHANNEL_WEBPUSH):
        return _send_via_channel(channel_key, user, db)
    return False, "Unknown channel."


def send_circle_telegram_test(
    db: Session, config: CircleTelegramConfig, user: User
) -> tuple[bool, str]:
    """
    Send a test message for one circle Telegram bot.

    Group-mode bots post to the configured group chat; DM-mode bots
    send to the caller's own linked chat. Admin enforcement for group
    mode is handled by the router.

    :param db: Active database session.
    :param config: The bot config to test.
    :param user: The caller (used for DM-mode addressing).
    :returns: ``(ok, message)`` describing the outcome.
    """
    if config.mode == TELEGRAM_MODE_DM:
        link = db.execute(
            select(TelegramMemberLink).where(
                TelegramMemberLink.circle_telegram_config_id == config.id,
                TelegramMemberLink.user_id == user.id,
            )
        ).scalar_one_or_none()
        if link is None:
            return (
                False,
                "You haven't linked your Telegram chat for this bot.",
            )
        target_chat = link.chat_id
    else:
        if not config.group_chat_id:
            return False, "No group chat is set for this bot yet."
        target_chat = config.group_chat_id

    text = f"{_TEST_TITLE}\n\n{_TEST_BODY}"
    try:
        send_message(config.bot_token, target_chat, text)
    except Exception as exc:
        return False, f"Telegram rejected the test: {str(exc)[:160]}"
    return True, "Sent a test message."
