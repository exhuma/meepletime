"""Email notification channel (self-hosted SMTP).

A per-user channel: one target per recipient who has email enabled.
Uses the standard-library synchronous SMTP client with a hard timeout
so it is safe to call from the scheduler worker thread. The channel is
inert (returns no targets) when SMTP is not configured.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.notifications.channels import register
from app.services.notifications.channels.base import (
    ChannelTarget,
    Recipient,
)
from app.services.notifications.context import EventContext

# Hard network timeout for SMTP operations, in seconds. The scheduler
# worker thread must never block indefinitely on a stuck server.
_SMTP_TIMEOUT = 5


class EmailChannel:
    """Deliver notifications by email over SMTP."""

    key = "email"

    def _is_configured(self) -> bool:
        """
        Return whether SMTP delivery is configured.

        :returns: ``True`` when host and from-address are set.
        """
        settings = get_settings()
        return bool(settings.SMTP_HOST and settings.SMTP_FROM)

    def collect_targets(
        self,
        ctx: EventContext,
        recipients: list[Recipient],
        db: Session,
    ) -> list[ChannelTarget]:
        """
        Return one target per recipient with email enabled.

        :param ctx: The event context being delivered.
        :param recipients: Eligible recipients.
        :param db: Active database session (unused).
        :returns: Email targets, or empty when SMTP is unconfigured.
        """
        if not self._is_configured():
            return []
        targets: list[ChannelTarget] = []
        for recipient in recipients:
            if not recipient.email:
                continue
            if not recipient.settings.is_channel_enabled(self.key):
                continue
            targets.append(
                ChannelTarget(
                    address=recipient.email,
                    user_id=recipient.user_id,
                    delivery_id=recipient.delivery_id,
                )
            )
        return targets

    def send(
        self, target: ChannelTarget, ctx: EventContext, db: Session
    ) -> None:
        """
        Send one notification email.

        :param target: The email target to deliver to.
        :param ctx: The event context being delivered.
        :param db: Active database session (unused).
        :raises OSError: On connection or SMTP transport failure.
        """
        settings = get_settings()
        message = EmailMessage()
        message["Subject"] = ctx.title
        message["From"] = settings.SMTP_FROM
        message["To"] = target.address
        message.set_content(f"{ctx.body}\n\n{ctx.url}\n")

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=_SMTP_TIMEOUT,
        ) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)


register(EmailChannel())
