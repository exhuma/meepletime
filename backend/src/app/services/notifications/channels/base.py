"""Channel abstraction for the notification delivery layer.

A :class:`NotificationChannel` knows how to turn an event plus the set
of eligible recipients into zero or more :class:`ChannelTarget` sends.
The dispatcher is transport- and scope-agnostic: per-user channels
(email, web push) return one target per recipient, while circle-level
channels (telegram group broadcast) return one target per circle
config with no associated user.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from sqlalchemy.orm import Session

from app.models.notification_settings import UserNotificationSettings
from app.services.notifications.context import EventContext


@dataclass
class Recipient:
    """
    One eligible (non-muted) recipient of an event.

    :param user_id: The recipient user's id.
    :param delivery_id: The id of the user's delivery row.
    :param email: The recipient's email address.
    :param settings: The user's resolved notification settings.
    """

    user_id: uuid.UUID
    delivery_id: uuid.UUID
    email: str
    settings: UserNotificationSettings


@dataclass
class ChannelTarget:
    """
    A single addressable send for a channel.

    :param address: Primary address (email / chat id / push endpoint).
    :param user_id: Owning user, or ``None`` for circle broadcasts.
    :param delivery_id: Delivery row, or ``None`` for broadcasts.
    :param extra: Channel-specific addressing data (keys, tokens).
    """

    address: str
    user_id: uuid.UUID | None = None
    delivery_id: uuid.UUID | None = None
    extra: dict = field(default_factory=dict)


@runtime_checkable
class NotificationChannel(Protocol):
    """Protocol implemented by every delivery channel."""

    key: str

    def collect_targets(
        self,
        ctx: EventContext,
        recipients: list[Recipient],
        db: Session,
    ) -> list[ChannelTarget]:
        """
        Return the targets this channel should send to.

        Returns an empty list when the channel is not configured for
        this event, so the dispatcher need not special-case it.

        :param ctx: The event context being delivered.
        :param recipients: Eligible (non-muted) recipients.
        :param db: Active database session.
        :returns: Zero or more channel targets.
        """
        ...

    def send(
        self, target: ChannelTarget, ctx: EventContext, db: Session
    ) -> None:
        """
        Deliver one target. Raise on failure.

        Implementations must use a hard network timeout; the dispatcher
        runs inside a synchronous scheduler worker thread. The session
        is provided so a channel can prune dead addressing rows (e.g. an
        expired Web Push subscription) before re-raising.

        :param target: The target to deliver to.
        :param ctx: The event context being delivered.
        :param db: Active database session.
        :raises Exception: On any delivery failure.
        """
        ...
