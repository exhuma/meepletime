"""Email notification channel (self-hosted SMTP).

A per-user channel: one target per recipient who has email enabled.
Uses the standard-library synchronous SMTP client with a hard timeout
so it is safe to call from the scheduler worker thread. The channel is
inert (returns no targets) when SMTP is not configured.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.email import is_smtp_configured, send_email
from app.services.notifications.channels import register
from app.services.notifications.channels.base import (
    ChannelTarget,
    Recipient,
)
from app.services.notifications.context import EventContext


class EmailChannel:
    """Deliver notifications by email over SMTP."""

    key = "email"

    def _is_configured(self) -> bool:
        """
        Return whether SMTP delivery is configured.

        :returns: ``True`` when host and from-address are set.
        """
        return is_smtp_configured()

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
        send_email(
            target.address,
            ctx.title,
            f"{ctx.body}\n\n{ctx.url}\n",
        )


register(EmailChannel())
