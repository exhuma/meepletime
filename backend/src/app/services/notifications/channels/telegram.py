"""Telegram notification channel (circle-scoped).

Telegram is configured per circle (owner/admin managed), not per user.
In ``group`` mode the channel broadcasts one message to each circle bot
config's group chat. Per-member DM mode is added separately.

The channel is inert for circles with no Telegram config.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_settings import (
    TELEGRAM_MODE_DM,
    TELEGRAM_MODE_GROUP,
    CircleTelegramConfig,
    TelegramMemberLink,
)
from app.services.notifications.channels import register
from app.services.notifications.channels.base import (
    ChannelTarget,
    Recipient,
)
from app.services.notifications.context import EventContext
from app.services.telegram_api import send_message


class TelegramChannel:
    """Deliver notifications to circle-scoped Telegram chats."""

    key = "telegram"

    def collect_targets(
        self,
        ctx: EventContext,
        recipients: list[Recipient],
        db: Session,
    ) -> list[ChannelTarget]:
        """
        Return Telegram targets for the event's circle.

        Group-mode configs broadcast once to their group chat; DM-mode
        configs send one message per linked member who has Telegram DMs
        enabled globally.

        :param ctx: The event context being delivered.
        :param recipients: Eligible recipients.
        :param db: Active database session.
        :returns: Group and/or per-member Telegram targets.
        """
        configs = (
            db.execute(
                select(CircleTelegramConfig).where(
                    CircleTelegramConfig.circle_id == ctx.circle_id
                )
            )
            .scalars()
            .all()
        )
        targets: list[ChannelTarget] = []
        for config in configs:
            if config.mode == TELEGRAM_MODE_GROUP and config.group_chat_id:
                targets.append(
                    ChannelTarget(
                        address=config.group_chat_id,
                        extra={"bot_token": config.bot_token},
                    )
                )
        targets.extend(self._dm_targets(configs, recipients, db))
        return targets

    def _dm_targets(
        self,
        configs: list[CircleTelegramConfig],
        recipients: list[Recipient],
        db: Session,
    ) -> list[ChannelTarget]:
        """
        Return per-member DM targets for DM-mode configs.

        A member is targeted only when they enabled Telegram DMs
        globally and have linked a chat for that bot.

        :param configs: The circle's bot configs.
        :param recipients: Eligible recipients.
        :param db: Active database session.
        :returns: Per-member DM targets.
        """
        dm_configs = {c.id: c for c in configs if c.mode == TELEGRAM_MODE_DM}
        enabled = {
            r.user_id: r
            for r in recipients
            if r.settings.is_channel_enabled(self.key)
        }
        if not dm_configs or not enabled:
            return []

        links = (
            db.execute(
                select(TelegramMemberLink).where(
                    TelegramMemberLink.circle_telegram_config_id.in_(
                        dm_configs.keys()
                    ),
                    TelegramMemberLink.user_id.in_(enabled.keys()),
                )
            )
            .scalars()
            .all()
        )
        targets: list[ChannelTarget] = []
        for link in links:
            recipient = enabled[link.user_id]
            config = dm_configs[link.circle_telegram_config_id]
            targets.append(
                ChannelTarget(
                    address=link.chat_id,
                    user_id=recipient.user_id,
                    delivery_id=recipient.delivery_id,
                    extra={"bot_token": config.bot_token},
                )
            )
        return targets

    def send(
        self, target: ChannelTarget, ctx: EventContext, db: Session
    ) -> None:
        """
        Send one Telegram message to a chat.

        :param target: The chat target (carries the bot token).
        :param ctx: The event context being delivered.
        :param db: Active database session (unused).
        :raises httpx.HTTPError: On transport or non-2xx response.
        """
        text = f"{ctx.title}\n\n{ctx.body}\n{ctx.url}"
        send_message(target.extra["bot_token"], target.address, text)


register(TelegramChannel())
