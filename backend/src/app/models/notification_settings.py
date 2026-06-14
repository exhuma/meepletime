"""ORM models for per-user and per-circle notification settings.

These tables hold *addressing* and *opt-in* data for the delivery
layer:

- :class:`UserNotificationSettings` — global per-user channel toggles
  (email / web push / telegram DM).
- :class:`WebPushSubscription` — one row per browser/device a user has
  subscribed for background Web Push.
- :class:`CircleTelegramConfig` — a Telegram bot configured inline on a
  circle (owner/admin managed). Telegram is circle-scoped, not global.
- :class:`TelegramMemberLink` — a member's private chat id for a circle
  bot configured in per-member DM mode.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Channel keys are the stable identifiers shared between the channel
# registry and the per-user enabled flags below.
CHANNEL_EMAIL = "email"
CHANNEL_WEBPUSH = "webpush"
CHANNEL_TELEGRAM = "telegram"

# Telegram delivery modes for a circle bot configuration.
TELEGRAM_MODE_GROUP = "group"
TELEGRAM_MODE_DM = "dm"


class UserNotificationSettings(Base):
    """
    Global per-user notification channel preferences.

    One row per user. Holds only enable/disable flags for the
    per-user channels; Telegram bot addressing lives on the circle
    (see :class:`CircleTelegramConfig`).
    """

    __tablename__ = "user_notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    email_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    webpush_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    telegram_dm_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    notification_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def is_channel_enabled(self, key: str) -> bool:
        """
        Return whether the named channel is enabled for this user.

        :param key: A channel key (``email`` / ``webpush`` /
            ``telegram``).
        :returns: ``True`` when the matching per-user flag is set.
        """
        return {
            CHANNEL_EMAIL: self.email_enabled,
            CHANNEL_WEBPUSH: self.webpush_enabled,
            CHANNEL_TELEGRAM: self.telegram_dm_enabled,
        }.get(key, False)


class WebPushSubscription(Base):
    """
    A single Web Push subscription endpoint owned by a user.

    A user may have many subscriptions (one per browser/device).
    The triplet ``(endpoint, p256dh, auth)`` is the standard
    ``PushSubscription`` payload produced by the browser.
    """

    __tablename__ = "web_push_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "endpoint", name="uq_webpush_user_endpoint"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class CircleTelegramConfig(Base):
    """
    A Telegram bot attached to a circle (configured inline).

    Owner/admin managed. A circle may have several configs ("multiple
    bots"); the same bot may be reused across circles by entering the
    same token. ``mode`` selects group-chat broadcast vs per-member DM.
    """

    __tablename__ = "circle_telegram_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    # Secret bot token from BotFather. Never returned by the API.
    bot_token: Mapped[str] = mapped_column(String(255), nullable=False)
    # Delivery mode: "group" (broadcast) or "dm" (per-member).
    mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default=TELEGRAM_MODE_GROUP
    )
    # Target chat id for group mode; null for dm mode.
    group_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class TelegramMemberLink(Base):
    """
    A member's private Telegram chat id for a circle bot (DM mode).

    Captured when a member links their account to a circle's bot so
    that per-member direct messages can be addressed.
    """

    __tablename__ = "telegram_member_links"
    __table_args__ = (
        UniqueConstraint(
            "circle_telegram_config_id",
            "user_id",
            name="uq_telegram_link_config_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    circle_telegram_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circle_telegram_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chat_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class EmailConfirmation(Base):
    """
    A pending notification-email confirmation for one user.

    At most one row per user (``unique(user_id)``). Holds the opaque
    confirmation ``token`` (re-sent verbatim on retry), the address
    awaiting confirmation, and the expiry deadline. The row is deleted
    when the address is confirmed or cleared.
    """

    __tablename__ = "email_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    pending_email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
