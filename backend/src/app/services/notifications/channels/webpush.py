"""Web Push notification channel (VAPID, background).

A per-user channel: one target per subscribed browser/device of a
recipient who has web push enabled. Uses ``pywebpush`` with a hard
timeout. Subscriptions rejected by the push service as gone
(HTTP 404/410) are pruned before the failure is re-raised.

The channel is inert when the VAPID key material is not configured.
"""

from __future__ import annotations

import json

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.notification_settings import WebPushSubscription
from app.services.notifications.channels import register
from app.services.notifications.channels.base import (
    ChannelTarget,
    Recipient,
)
from app.services.notifications.context import EventContext

# Hard network timeout for push delivery, in seconds.
_WEBPUSH_TIMEOUT = 5
# Statuses that mean the subscription is permanently gone.
_GONE_STATUSES = {404, 410}


class WebPushChannel:
    """Deliver notifications via background Web Push."""

    key = "webpush"

    def _is_configured(self) -> bool:
        """
        Return whether VAPID key material is configured.

        :returns: ``True`` when public key, private key, and subject
            are all set.
        """
        settings = get_settings()
        return bool(
            settings.VAPID_PUBLIC_KEY
            and settings.VAPID_PRIVATE_KEY
            and settings.VAPID_SUBJECT
        )

    def collect_targets(
        self,
        ctx: EventContext,
        recipients: list[Recipient],
        db: Session,
    ) -> list[ChannelTarget]:
        """
        Return one target per subscription of an enabled recipient.

        :param ctx: The event context being delivered.
        :param recipients: Eligible recipients.
        :param db: Active database session.
        :returns: Push targets, or empty when unconfigured.
        """
        if not self._is_configured():
            return []
        by_user = {
            r.user_id: r
            for r in recipients
            if r.settings.is_channel_enabled(self.key)
        }
        if not by_user:
            return []

        subs = (
            db.execute(
                select(WebPushSubscription).where(
                    WebPushSubscription.user_id.in_(by_user.keys())
                )
            )
            .scalars()
            .all()
        )
        targets: list[ChannelTarget] = []
        for sub in subs:
            recipient = by_user[sub.user_id]
            targets.append(
                ChannelTarget(
                    address=sub.endpoint,
                    user_id=sub.user_id,
                    delivery_id=recipient.delivery_id,
                    extra={
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                        "subscription_id": sub.id,
                    },
                )
            )
        return targets

    def send(
        self, target: ChannelTarget, ctx: EventContext, db: Session
    ) -> None:
        """
        Push one notification to a subscription endpoint.

        :param target: The push target to deliver to.
        :param ctx: The event context being delivered.
        :param db: Active database session (used to prune dead subs).
        :raises WebPushException: On any push delivery failure.
        """
        settings = get_settings()
        payload = json.dumps(
            {"title": ctx.title, "body": ctx.body, "url": ctx.url}
        )
        subscription_info = {
            "endpoint": target.address,
            "keys": {
                "p256dh": target.extra["p256dh"],
                "auth": target.extra["auth"],
            },
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                timeout=_WEBPUSH_TIMEOUT,
            )
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            if status in _GONE_STATUSES:
                self._prune(db, target)
            raise

    def _prune(self, db: Session, target: ChannelTarget) -> None:
        """
        Delete a subscription that the push service reported as gone.

        :param db: Active database session.
        :param target: The target whose subscription is dead.
        """
        sub_id = target.extra.get("subscription_id")
        if sub_id is None:
            return
        sub = db.get(WebPushSubscription, sub_id)
        if sub is not None:
            db.delete(sub)
            db.flush()


register(WebPushChannel())
