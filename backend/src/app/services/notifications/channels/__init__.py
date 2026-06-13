"""Channel registry for the notification delivery layer.

Concrete channels register themselves here at import time via
:func:`register`. The dispatcher iterates the registered channels;
tests may pass an explicit channel list to ``dispatch_event`` instead.
"""

from __future__ import annotations

from app.services.notifications.channels.base import (
    ChannelTarget,
    NotificationChannel,
    Recipient,
)

_REGISTRY: dict[str, NotificationChannel] = {}


def register(channel: NotificationChannel) -> None:
    """
    Register (or replace) a channel by its key.

    :param channel: The channel instance to register.
    """
    _REGISTRY[channel.key] = channel


def iter_channels() -> list[NotificationChannel]:
    """
    Return all registered channels.

    :returns: The registered channel instances.
    """
    return list(_REGISTRY.values())


def get_channel(key: str) -> NotificationChannel | None:
    """
    Return the channel registered under *key*, if any.

    :param key: Channel key.
    :returns: The channel or ``None``.
    """
    return _REGISTRY.get(key)


def register_default_channels() -> None:
    """
    Register the built-in channels (idempotent).

    Concrete channel modules are imported here as they are added in
    later delivery phases; each calls :func:`register` on import.
    """
    from app.services.notifications.channels import (  # noqa: F401
        email,
        telegram,
        webpush,
    )


__all__ = [
    "ChannelTarget",
    "NotificationChannel",
    "Recipient",
    "register",
    "iter_channels",
    "get_channel",
    "register_default_channels",
]
