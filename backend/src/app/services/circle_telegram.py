"""Service layer for circle-scoped Telegram bot configuration."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.circle import Circle
from app.models.membership import CircleMembership
from app.models.notification_settings import (
    TELEGRAM_MODE_DM,
    CircleTelegramConfig,
    TelegramMemberLink,
)


def list_configs(
    db: Session, circle_id: uuid.UUID
) -> list[CircleTelegramConfig]:
    """
    Return all Telegram bot configs for a circle.

    :param db: Active database session.
    :param circle_id: The circle whose configs to list.
    :returns: The circle's bot configurations.
    """
    return list(
        db.execute(
            select(CircleTelegramConfig).where(
                CircleTelegramConfig.circle_id == circle_id
            )
        )
        .scalars()
        .all()
    )


def get_config_or_404(
    db: Session, circle_id: uuid.UUID, config_id: uuid.UUID
) -> CircleTelegramConfig:
    """
    Return a circle's bot config, or raise HTTP 404.

    :param db: Active database session.
    :param circle_id: The owning circle.
    :param config_id: The config to fetch.
    :returns: The matching config.
    :raises HTTPException: 404 when not found in this circle.
    """
    config = db.execute(
        select(CircleTelegramConfig).where(
            CircleTelegramConfig.id == config_id,
            CircleTelegramConfig.circle_id == circle_id,
        )
    ).scalar_one_or_none()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram config not found",
        )
    return config


def create_config(
    db: Session,
    circle_id: uuid.UUID,
    label: str,
    bot_token: str,
    mode: str,
    group_chat_id: str | None,
) -> CircleTelegramConfig:
    """
    Create a Telegram bot config for a circle.

    :param db: Active database session.
    :param circle_id: The owning circle.
    :param label: Human label for the bot.
    :param bot_token: The bot's secret token.
    :param mode: Delivery mode (``group`` or ``dm``).
    :param group_chat_id: Target group chat id (group mode).
    :returns: The persisted config.
    """
    config = CircleTelegramConfig(
        circle_id=circle_id,
        label=label,
        bot_token=bot_token,
        mode=mode,
        group_chat_id=group_chat_id,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def delete_config(db: Session, config: CircleTelegramConfig) -> None:
    """
    Delete a Telegram bot config.

    :param db: Active database session.
    :param config: The config to delete.
    """
    db.delete(config)
    db.commit()


def get_dm_config_or_404(
    db: Session, circle_id: uuid.UUID, config_id: uuid.UUID
) -> CircleTelegramConfig:
    """
    Return a DM-mode bot config for a circle, or raise HTTP 404.

    :param db: Active database session.
    :param circle_id: The owning circle.
    :param config_id: The config to fetch.
    :returns: The matching DM-mode config.
    :raises HTTPException: 404 when not found or not DM mode.
    """
    config = get_config_or_404(db, circle_id, config_id)
    if config.mode != TELEGRAM_MODE_DM:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram config not found",
        )
    return config


def list_dm_bots_with_link_state(
    db: Session, circle_id: uuid.UUID, user_id: uuid.UUID
) -> list[tuple[CircleTelegramConfig, bool]]:
    """
    Return the circle's DM-mode bots and whether the user is linked.

    :param db: Active database session.
    :param circle_id: The circle to inspect.
    :param user_id: The member asking.
    :returns: ``(config, linked)`` pairs for each DM-mode bot.
    """
    configs = [
        c for c in list_configs(db, circle_id) if c.mode == TELEGRAM_MODE_DM
    ]
    if not configs:
        return []
    linked_ids = set(
        db.execute(
            select(TelegramMemberLink.circle_telegram_config_id).where(
                TelegramMemberLink.user_id == user_id,
                TelegramMemberLink.circle_telegram_config_id.in_(
                    c.id for c in configs
                ),
            )
        ).scalars()
    )
    return [(c, c.id in linked_ids) for c in configs]


def list_user_dm_bots(
    db: Session, user_id: uuid.UUID
) -> list[tuple[CircleTelegramConfig, str, bool]]:
    """
    Return DM-mode bots across all circles the user belongs to.

    Gated by membership: only bots of circles the user is a member of
    are returned, satisfying "DMs may only go out to members of these
    circles".

    :param db: Active database session.
    :param user_id: The member asking.
    :returns: ``(config, circle_name, linked)`` triples.
    """
    rows = db.execute(
        select(CircleTelegramConfig, Circle.name)
        .join(Circle, Circle.id == CircleTelegramConfig.circle_id)
        .join(
            CircleMembership,
            CircleMembership.circle_id == CircleTelegramConfig.circle_id,
        )
        .where(
            CircleMembership.user_id == user_id,
            CircleTelegramConfig.mode == TELEGRAM_MODE_DM,
        )
    ).all()
    if not rows:
        return []
    config_ids = [config.id for config, _ in rows]
    linked_ids = set(
        db.execute(
            select(TelegramMemberLink.circle_telegram_config_id).where(
                TelegramMemberLink.user_id == user_id,
                TelegramMemberLink.circle_telegram_config_id.in_(config_ids),
            )
        ).scalars()
    )
    return [(config, name, config.id in linked_ids) for config, name in rows]


def upsert_member_link(
    db: Session,
    config_id: uuid.UUID,
    user_id: uuid.UUID,
    chat_id: str,
) -> TelegramMemberLink:
    """
    Create or update a member's DM chat link for a bot.

    :param db: Active database session.
    :param config_id: The DM-mode bot config.
    :param user_id: The linking member.
    :param chat_id: The member's private chat id.
    :returns: The persisted link.
    """
    link = db.execute(
        select(TelegramMemberLink).where(
            TelegramMemberLink.circle_telegram_config_id == config_id,
            TelegramMemberLink.user_id == user_id,
        )
    ).scalar_one_or_none()
    if link is not None:
        link.chat_id = chat_id
        db.commit()
        db.refresh(link)
        return link

    link = TelegramMemberLink(
        circle_telegram_config_id=config_id,
        user_id=user_id,
        chat_id=chat_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def delete_member_link(
    db: Session, config_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """
    Remove a member's DM chat link for a bot, if present.

    :param db: Active database session.
    :param config_id: The DM-mode bot config.
    :param user_id: The member unlinking.
    """
    link = db.execute(
        select(TelegramMemberLink).where(
            TelegramMemberLink.circle_telegram_config_id == config_id,
            TelegramMemberLink.user_id == user_id,
        )
    ).scalar_one_or_none()
    if link is not None:
        db.delete(link)
        db.commit()
