"""Circle-scoped Telegram configuration router (owner/admin only)."""

from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import (
    get_current_active_user,
    get_db,
    get_membership_or_403,
    require_admin_or_owner,
)
from app.models.notification_settings import TELEGRAM_MODE_GROUP
from app.models.user import User
from app.schemas.circle_telegram import (
    CircleTelegramConfigCreate,
    CircleTelegramConfigOut,
    CircleTelegramConfigUpdate,
    DetectChatOut,
    TelegramDmBotOut,
    TelegramLinkIn,
    UserDmBotOut,
)
from app.schemas.notification_settings import NotificationTestOut
from app.services.circle_telegram import (
    create_config,
    delete_config,
    delete_member_link,
    get_config_or_404,
    get_dm_config_or_404,
    list_configs,
    list_dm_bots_with_link_state,
    list_user_dm_bots,
    upsert_member_link,
)
from app.services.notifications.test_delivery import (
    send_circle_telegram_test,
)
from app.services.telegram_api import get_chat_options
from app.utils import apply_partial_update

router = APIRouter(tags=["notifications"])


def _require_circle_admin(
    db: Session, circle_id: uuid.UUID, user: User
) -> None:
    """
    Ensure the caller is an owner/admin of the circle.

    :param db: Active database session.
    :param circle_id: The circle being managed.
    :param user: The authenticated user.
    :raises HTTPException: 403 when not an owner/admin member.
    """
    membership = get_membership_or_403(db, circle_id, user.id)
    require_admin_or_owner(membership)


@router.get(
    "/circles/{circle_id}/telegram",
    response_model=list[CircleTelegramConfigOut],
)
def list_telegram_configs(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CircleTelegramConfigOut]:
    """
    List the circle's Telegram bots (tokens masked). Owner/admin only.

    :param circle_id: The circle to list bots for.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: The circle's bot configs with masked tokens.
    """
    _require_circle_admin(db, circle_id, current_user)
    return [
        CircleTelegramConfigOut.from_model(c)
        for c in list_configs(db, circle_id)
    ]


@router.post(
    "/circles/{circle_id}/telegram",
    response_model=CircleTelegramConfigOut,
    status_code=status.HTTP_201_CREATED,
)
def add_telegram_config(
    circle_id: uuid.UUID,
    payload: CircleTelegramConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CircleTelegramConfigOut:
    """
    Register a Telegram bot on the circle. Owner/admin only.

    :param circle_id: The circle to attach the bot to.
    :param payload: The bot configuration.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: The created config with a masked token.
    """
    _require_circle_admin(db, circle_id, current_user)
    config = create_config(
        db,
        circle_id,
        payload.label,
        payload.bot_token,
        payload.mode,
        payload.group_chat_id,
    )
    return CircleTelegramConfigOut.from_model(config)


@router.put(
    "/circles/{circle_id}/telegram/{config_id}",
    response_model=CircleTelegramConfigOut,
)
def update_telegram_config(
    circle_id: uuid.UUID,
    config_id: uuid.UUID,
    payload: CircleTelegramConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CircleTelegramConfigOut:
    """
    Update a circle's Telegram bot config. Owner/admin only.

    :param circle_id: The owning circle.
    :param config_id: The config to update.
    :param payload: Partial update fields.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: The updated config with a masked token.
    """
    _require_circle_admin(db, circle_id, current_user)
    config = get_config_or_404(db, circle_id, config_id)
    apply_partial_update(config, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(config)
    return CircleTelegramConfigOut.from_model(config)


@router.delete(
    "/circles/{circle_id}/telegram/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_telegram_config(
    circle_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Remove a circle's Telegram bot config. Owner/admin only.

    :param circle_id: The owning circle.
    :param config_id: The config to delete.
    :param db: Database session.
    :param current_user: Authenticated user.
    """
    _require_circle_admin(db, circle_id, current_user)
    config = get_config_or_404(db, circle_id, config_id)
    delete_config(db, config)


@router.post(
    "/circles/{circle_id}/telegram/{config_id}/detect-chat",
    response_model=DetectChatOut,
)
def detect_telegram_chat(
    circle_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DetectChatOut:
    """
    List chats the bot has recently seen, to pick a group chat id.

    Add the bot to your group and post a message there first, then
    call this to read back the chat id. Owner/admin only.

    :param circle_id: The owning circle.
    :param config_id: The bot config to query.
    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: Distinct chats the bot can see.
    :raises HTTPException: 502 when the Telegram API is unreachable.
    """
    _require_circle_admin(db, circle_id, current_user)
    config = get_config_or_404(db, circle_id, config_id)
    try:
        chats = get_chat_options(config.bot_token)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Telegram for this bot",
        )
    return DetectChatOut(chats=chats)


@router.post(
    "/circles/{circle_id}/telegram/{config_id}/detect-dm",
    response_model=DetectChatOut,
)
def detect_telegram_dm_chat(
    circle_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DetectChatOut:
    """
    List private chats a DM-mode bot has recently seen.

    Start a private chat with the bot and send it any message first,
    then call this to pick your own chat id. Any circle member may
    call this for a DM-mode bot; only private chats are returned.

    \r

    :raises HTTPException: 404 when the config is not a DM bot in this
        circle, 502 when the Telegram API is unreachable.
    """
    get_membership_or_403(db, circle_id, current_user.id)
    config = get_dm_config_or_404(db, circle_id, config_id)
    try:
        chats = get_chat_options(config.bot_token)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Telegram for this bot",
        )
    private = [c for c in chats if c.get("type") == "private"]
    return DetectChatOut(chats=private)


@router.get(
    "/users/me/telegram/dm-bots",
    response_model=list[UserDmBotOut],
)
def list_my_dm_bots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[UserDmBotOut]:
    """
    List DM-mode bots across every circle the caller belongs to.

    Powers the per-user opt-in on the profile page. Results are scoped
    to the caller's memberships and never expose bot tokens.

    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: DM-mode bots with their circle and the caller's link
        status.
    """
    return [
        UserDmBotOut(
            circle_id=config.circle_id,
            circle_name=name,
            config_id=config.id,
            label=config.label,
            linked=linked,
        )
        for config, name, linked in list_user_dm_bots(db, current_user.id)
    ]


@router.get(
    "/circles/{circle_id}/telegram/dm-bots",
    response_model=list[TelegramDmBotOut],
)
def list_dm_bots(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TelegramDmBotOut]:
    """
    List the circle's DM-mode bots and the caller's link state.

    Any circle member may call this to find a bot to receive personal
    direct messages from. Bot tokens are never exposed.

    :param circle_id: The circle to inspect.
    :param db: Database session.
    :param current_user: Authenticated member.
    :returns: DM-mode bots with the caller's link status.
    """
    get_membership_or_403(db, circle_id, current_user.id)
    return [
        TelegramDmBotOut(id=config.id, label=config.label, linked=linked)
        for config, linked in list_dm_bots_with_link_state(
            db, circle_id, current_user.id
        )
    ]


@router.put(
    "/circles/{circle_id}/telegram/{config_id}/link",
    status_code=status.HTTP_204_NO_CONTENT,
)
def link_telegram_dm(
    circle_id: uuid.UUID,
    config_id: uuid.UUID,
    payload: TelegramLinkIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Link the caller's private Telegram chat to a DM-mode bot.

    The member obtains their chat id (e.g. via @userinfobot) after
    starting a private chat with the bot. Any circle member may link
    their own chat.

    :param circle_id: The owning circle.
    :param config_id: The DM-mode bot to link to.
    :param payload: The caller's private chat id.
    :param db: Database session.
    :param current_user: Authenticated member.
    """
    get_membership_or_403(db, circle_id, current_user.id)
    get_dm_config_or_404(db, circle_id, config_id)
    upsert_member_link(db, config_id, current_user.id, payload.chat_id)


@router.delete(
    "/circles/{circle_id}/telegram/{config_id}/link",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_telegram_dm(
    circle_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Remove the caller's DM link to a bot.

    :param circle_id: The owning circle.
    :param config_id: The DM-mode bot to unlink from.
    :param db: Database session.
    :param current_user: Authenticated member.
    """
    get_membership_or_403(db, circle_id, current_user.id)
    delete_member_link(db, config_id, current_user.id)


@router.post(
    "/circles/{circle_id}/telegram/{config_id}/test",
    response_model=NotificationTestOut,
)
def test_telegram_config(
    circle_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationTestOut:
    """
    Send a real test message for one bot, reporting the outcome.

    Group-mode bots post to the configured group chat (owner/admin
    only); DM-mode bots send to the caller's own linked chat.

    :param circle_id: The owning circle.
    :param config_id: The bot config to test.
    :param db: Database session.
    :param current_user: Authenticated member.
    :returns: The test outcome.
    """
    membership = get_membership_or_403(db, circle_id, current_user.id)
    config = get_config_or_404(db, circle_id, config_id)
    if config.mode == TELEGRAM_MODE_GROUP:
        require_admin_or_owner(membership)
    ok, message = send_circle_telegram_test(db, config, current_user)
    return NotificationTestOut(ok=ok, message=message)
