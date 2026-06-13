"""Thin synchronous client for the Telegram Bot API.

Only the two methods MeepleTime needs are wrapped: ``sendMessage`` for
delivery and ``getUpdates`` for chat-id discovery. All calls are
outbound to ``api.telegram.org`` with a hard timeout, so no inbound
webhook needs to be exposed through the reverse proxy.
"""

from __future__ import annotations

import httpx

# Hard network timeout for Telegram API calls, in seconds.
_TELEGRAM_TIMEOUT = 5
_API_BASE = "https://api.telegram.org"


def _method_url(bot_token: str, method: str) -> str:
    """
    Return the full Bot API URL for a method.

    :param bot_token: The bot's secret token.
    :param method: Bot API method name, e.g. ``sendMessage``.
    :returns: Fully qualified request URL.
    """
    return f"{_API_BASE}/bot{bot_token}/{method}"


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    """
    Send a plain-text message to a chat.

    :param bot_token: The bot's secret token.
    :param chat_id: Target chat id (group or private).
    :param text: Message body.
    :raises httpx.HTTPError: On transport or non-2xx response.
    """
    with httpx.Client(timeout=_TELEGRAM_TIMEOUT) as client:
        response = client.post(
            _method_url(bot_token, "sendMessage"),
            json={"chat_id": chat_id, "text": text},
        )
        response.raise_for_status()


def get_chat_options(bot_token: str) -> list[dict[str, str]]:
    """
    Return distinct chats the bot has recently seen, via getUpdates.

    Lets an admin pick a group chat id after adding the bot to a group
    and posting a message there, without configuring a webhook.

    :param bot_token: The bot's secret token.
    :returns: Distinct ``{chat_id, name, type}`` options.
    :raises httpx.HTTPError: On transport or non-2xx response.
    """
    with httpx.Client(timeout=_TELEGRAM_TIMEOUT) as client:
        response = client.get(_method_url(bot_token, "getUpdates"))
        response.raise_for_status()
        payload = response.json()

    options: dict[str, dict[str, str]] = {}
    for update in payload.get("result", []):
        message = update.get("message") or update.get("channel_post")
        chat = (message or {}).get("chat")
        if not chat:
            continue
        chat_id = str(chat.get("id"))
        name = (
            chat.get("title")
            or chat.get("username")
            or chat.get("first_name")
            or chat_id
        )
        options[chat_id] = {
            "chat_id": chat_id,
            "name": name,
            "type": chat.get("type", ""),
        }
    return list(options.values())
