"""Pydantic schemas for circle Telegram configuration endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.notification_settings import CircleTelegramConfig

TelegramMode = Literal["group", "dm"]


def _token_hint(token: str) -> str:
    """
    Return a non-secret hint for a bot token (last 4 chars).

    :param token: The full bot token.
    :returns: A masked hint such as ``…AbCd``.
    """
    return f"…{token[-4:]}" if token else ""


class CircleTelegramConfigOut(BaseModel):
    """A circle Telegram bot config, with the token masked."""

    id: uuid.UUID
    label: str
    mode: str
    group_chat_id: str | None
    token_hint: str
    created_at: datetime

    @classmethod
    def from_model(
        cls, config: CircleTelegramConfig
    ) -> CircleTelegramConfigOut:
        """
        Build a response from an ORM config, masking the token.

        :param config: The persisted config.
        :returns: A safe-to-return representation.
        """
        return cls(
            id=config.id,
            label=config.label,
            mode=config.mode,
            group_chat_id=config.group_chat_id,
            token_hint=_token_hint(config.bot_token),
            created_at=config.created_at,
        )


class CircleTelegramConfigCreate(BaseModel):
    """Payload to register a Telegram bot on a circle."""

    label: str
    bot_token: str
    mode: TelegramMode = "group"
    group_chat_id: str | None = None


class CircleTelegramConfigUpdate(BaseModel):
    """Partial update of a circle Telegram bot config."""

    label: str | None = None
    bot_token: str | None = None
    mode: TelegramMode | None = None
    group_chat_id: str | None = None


class DetectChatOption(BaseModel):
    """One chat the bot has recently seen."""

    chat_id: str
    name: str
    type: str


class DetectChatOut(BaseModel):
    """Result of a chat-id detection request."""

    chats: list[DetectChatOption]


class TelegramDmBotOut(BaseModel):
    """A DM-mode bot a member may link to, with their link state."""

    id: uuid.UUID
    label: str
    linked: bool


class TelegramLinkIn(BaseModel):
    """Payload to link a member's private Telegram chat."""

    chat_id: str
