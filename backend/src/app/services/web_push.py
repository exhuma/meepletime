"""Service layer for Web Push subscriptions."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_settings import WebPushSubscription


def upsert_subscription(
    db: Session,
    user_id: uuid.UUID,
    endpoint: str,
    p256dh: str,
    auth: str,
) -> WebPushSubscription:
    """
    Create or refresh a Web Push subscription for a user.

    Uniqueness is on ``(user_id, endpoint)``; re-subscribing the same
    endpoint updates its keys rather than duplicating it.

    :param db: Active database session.
    :param user_id: Owning user.
    :param endpoint: Push service endpoint URL.
    :param p256dh: Client public key.
    :param auth: Client auth secret.
    :returns: The persisted subscription.
    """
    existing = db.execute(
        select(WebPushSubscription).where(
            WebPushSubscription.user_id == user_id,
            WebPushSubscription.endpoint == endpoint,
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.p256dh = p256dh
        existing.auth = auth
        db.commit()
        db.refresh(existing)
        return existing

    sub = WebPushSubscription(
        user_id=user_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def delete_subscription(db: Session, user_id: uuid.UUID, endpoint: str) -> None:
    """
    Remove a user's subscription for an endpoint, if present.

    :param db: Active database session.
    :param user_id: Owning user.
    :param endpoint: Push service endpoint URL to remove.
    """
    sub = db.execute(
        select(WebPushSubscription).where(
            WebPushSubscription.user_id == user_id,
            WebPushSubscription.endpoint == endpoint,
        )
    ).scalar_one_or_none()
    if sub is not None:
        db.delete(sub)
        db.commit()
