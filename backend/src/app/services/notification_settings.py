"""Service layer for per-user notification settings."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_settings import UserNotificationSettings


def get_or_create_settings(
    db: Session, user_id: uuid.UUID
) -> UserNotificationSettings:
    """
    Return the user's settings row, creating defaults on first use.

    :param db: Active database session.
    :param user_id: The user whose settings to load.
    :returns: The persisted settings row.
    """
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user_id
        )
    ).scalar_one_or_none()
    if settings is None:
        settings = UserNotificationSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(
    db: Session,
    settings: UserNotificationSettings,
    *,
    email_enabled: bool | None = None,
    webpush_enabled: bool | None = None,
    telegram_dm_enabled: bool | None = None,
) -> UserNotificationSettings:
    """
    Apply a partial update to a settings row and persist it.

    Only non-``None`` fields are changed.

    :param db: Active database session.
    :param settings: The settings row to mutate.
    :param email_enabled: New email flag, if provided.
    :param webpush_enabled: New web-push flag, if provided.
    :param telegram_dm_enabled: New telegram-DM flag, if provided.
    :returns: The refreshed settings row.
    """
    if email_enabled is not None:
        settings.email_enabled = email_enabled
    if webpush_enabled is not None:
        settings.webpush_enabled = webpush_enabled
    if telegram_dm_enabled is not None:
        settings.telegram_dm_enabled = telegram_dm_enabled
    db.commit()
    db.refresh(settings)
    return settings
