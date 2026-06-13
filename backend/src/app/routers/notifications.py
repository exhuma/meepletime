"""Per-user notification settings router.

All endpoints are scoped to the authenticated user; a user can only
read and modify their own settings.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.notification_settings import (
    NotificationSettingsOut,
    NotificationSettingsUpdate,
    NotificationTestIn,
    NotificationTestOut,
    WebPushKeyOut,
    WebPushSubscriptionIn,
)
from app.services.notification_settings import (
    get_or_create_settings,
    update_settings,
)
from app.services.notifications.test_delivery import send_user_test
from app.services.web_push import (
    delete_subscription,
    upsert_subscription,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/settings", response_model=NotificationSettingsOut)
def read_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Return the caller's notification channel preferences.

    Defaults are created on first access (email on, others off).

    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The caller's notification settings.
    """
    settings = get_or_create_settings(db, current_user.id)
    return NotificationSettingsOut.model_validate(settings)


@router.put("/settings", response_model=NotificationSettingsOut)
def write_settings(
    payload: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Update the caller's notification channel preferences.

    Only provided fields are changed.

    :param payload: Partial settings update.
    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated notification settings.
    """
    settings = get_or_create_settings(db, current_user.id)
    settings = update_settings(
        db, settings, **payload.model_dump(exclude_unset=True)
    )
    return NotificationSettingsOut.model_validate(settings)


@router.get("/webpush/key", response_model=WebPushKeyOut)
def webpush_key(
    settings: Settings = Depends(get_settings),
) -> WebPushKeyOut:
    """
    Return the server's VAPID public key for Web Push subscription.

    The key is safe to expose; the private key never leaves the
    backend. Returns ``null`` when Web Push is not configured.

    :param settings: Application configuration.
    :returns: The VAPID public key, or null.
    """
    return WebPushKeyOut(vapid_public_key=settings.VAPID_PUBLIC_KEY)


@router.post("/webpush/subscriptions", status_code=status.HTTP_201_CREATED)
def add_webpush_subscription(
    payload: WebPushSubscriptionIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Register (or refresh) a Web Push subscription for this device.

    :param payload: The browser ``PushSubscription`` payload.
    :param current_user: Authenticated user.
    :param db: Database session.
    """
    upsert_subscription(
        db,
        current_user.id,
        payload.endpoint,
        payload.keys.p256dh,
        payload.keys.auth,
    )


@router.delete("/webpush/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def remove_webpush_subscription(
    endpoint: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Unregister a Web Push subscription by its endpoint.

    :param endpoint: The push endpoint URL to remove.
    :param current_user: Authenticated user.
    :param db: Database session.
    """
    delete_subscription(db, current_user.id, endpoint)


@router.post("/test", response_model=NotificationTestOut)
def test_channel(
    payload: NotificationTestIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationTestOut:
    """
    Send a real test notification to the caller on one channel.

    Verifies the channel mechanism regardless of the caller's on/off
    preference, and reports success or the failure reason.

    :param payload: Which channel to test.
    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The test outcome.
    """
    ok, message = send_user_test(db, current_user, payload.channel)
    return NotificationTestOut(ok=ok, message=message)
