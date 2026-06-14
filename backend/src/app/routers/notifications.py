"""Per-user notification settings router.

All endpoints are scoped to the authenticated user; a user can only
read and modify their own settings.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_db
from app.models.notification_settings import EmailConfirmation
from app.models.user import User
from app.schemas.notification_settings import (
    EmailConfirmIn,
    EmailConfirmOut,
    NotificationEmailIn,
    NotificationSettingsOut,
    NotificationSettingsUpdate,
    NotificationTestIn,
    NotificationTestOut,
    WebPushKeyOut,
    WebPushSubscriptionIn,
)
from app.services.email import is_smtp_configured
from app.services.email_confirmation import (
    ConfirmStatus,
    NoPendingConfirmation,
    ResendTooSoon,
    clear_email,
    confirm,
    get_pending,
    resend_confirmation,
    start_confirmation,
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


def _settings_response(
    db: Session, current_user: User
) -> NotificationSettingsOut:
    """
    Build the settings response, including any pending confirmation.

    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: The caller's settings plus pending-confirmation state.
    """
    settings = get_or_create_settings(db, current_user.id)
    pending = get_pending(db, current_user.id)
    return NotificationSettingsOut(
        email_enabled=settings.email_enabled,
        webpush_enabled=settings.webpush_enabled,
        telegram_dm_enabled=settings.telegram_dm_enabled,
        notification_email=settings.notification_email,
        pending_email=pending.pending_email if pending else None,
        pending_expires_at=pending.expires_at if pending else None,
    )


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
    return _settings_response(db, current_user)


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
    return _settings_response(db, current_user)


@router.post("/email", response_model=NotificationSettingsOut)
def set_notification_email(
    payload: NotificationEmailIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Start confirming a new notification address and send the link.

    The previously confirmed address (if any) keeps receiving mail
    until the new one is confirmed.

    :param payload: The address to confirm.
    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated settings including the pending address.
    """
    if not is_smtp_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery isn't configured on this server.",
        )
    try:
        start_confirmation(db, current_user.id, str(payload.email))
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the confirmation email.",
        )
    return _settings_response(db, current_user)


@router.post("/email/resend", response_model=NotificationSettingsOut)
def resend_notification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Resend the pending confirmation link with a fresh deadline.

    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated settings including the pending address.
    """
    try:
        resend_confirmation(db, current_user.id)
    except NoPendingConfirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is no pending email to confirm.",
        )
    except ResendTooSoon:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=("Please wait a moment before requesting another link."),
        )
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the confirmation email.",
        )
    return _settings_response(db, current_user)


@router.delete("/email", response_model=NotificationSettingsOut)
def clear_notification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Clear the confirmed notification address and any pending one.

    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated settings.
    """
    clear_email(db, current_user.id)
    return _settings_response(db, current_user)


@router.post("/email/confirm", response_model=EmailConfirmOut)
def confirm_notification_email(
    payload: EmailConfirmIn,
    db: Session = Depends(get_db),
) -> EmailConfirmOut:
    """
    Confirm a notification address from an emailed code.

    Unauthenticated: the opaque token is the authority. The response
    describes only the code state and never reveals account
    existence.

    :param payload: The submitted confirmation code.
    :param db: Database session.
    :returns: The confirmation outcome.
    """
    pending = db.execute(
        select(EmailConfirmation).where(EmailConfirmation.token == payload.code)
    ).scalar_one_or_none()
    confirmed_email = pending.pending_email if pending is not None else None
    result = confirm(db, payload.code)
    return EmailConfirmOut(
        status=result.value,
        email=(confirmed_email if result is ConfirmStatus.CONFIRMED else None),
    )


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


@router.delete(
    "/webpush/subscriptions",
    status_code=status.HTTP_204_NO_CONTENT,
)
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
