"""Pydantic schemas for notification settings endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

NotificationTestChannel = Literal["email", "webpush", "telegram"]


class NotificationSettingsOut(BaseModel):
    """Per-user notification channel toggles."""

    email_enabled: bool
    webpush_enabled: bool
    telegram_dm_enabled: bool

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    """Partial update of per-user notification channel toggles."""

    email_enabled: bool | None = None
    webpush_enabled: bool | None = None
    telegram_dm_enabled: bool | None = None


class WebPushKeyOut(BaseModel):
    """The server's VAPID public key (or null when unconfigured)."""

    vapid_public_key: str | None = None


class WebPushKeys(BaseModel):
    """The encryption keys from a browser ``PushSubscription``."""

    p256dh: str
    auth: str


class WebPushSubscriptionIn(BaseModel):
    """A browser ``PushSubscription`` registration payload."""

    endpoint: str
    keys: WebPushKeys


class NotificationTestIn(BaseModel):
    """Request to send a real test notification on one channel."""

    channel: NotificationTestChannel


class NotificationTestOut(BaseModel):
    """Outcome of a test notification send."""

    ok: bool
    message: str
