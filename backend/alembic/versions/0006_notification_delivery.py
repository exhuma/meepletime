"""Add notification delivery settings, addressing, and audit tables.

Revision ID: 0006_notification_delivery
Revises: 0005_invite_pin
Create Date: 2026-06-13 00:00:00.000000

Adds the tables that back the multi-channel delivery layer:

- ``user_notification_settings`` — global per-user channel toggles.
- ``web_push_subscriptions`` — per-device Web Push endpoints.
- ``circle_telegram_configs`` — circle-scoped Telegram bots (inline).
- ``telegram_member_links`` — per-member DM chat ids for a circle bot.
- ``notification_channel_attempts`` — per-channel delivery audit.

No data migration is required; all tables are new.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_notification_delivery"
down_revision: str | None = "0005_invite_pin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the delivery-layer tables, indexes, and comments."""
    op.create_table(
        "user_notification_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email_enabled", sa.Boolean(), nullable=False),
        sa.Column("webpush_enabled", sa.Boolean(), nullable=False),
        sa.Column("telegram_dm_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "uq_user_notif_settings_user",
        "user_notification_settings",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "web_push_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "user_id", "endpoint", name="uq_webpush_user_endpoint"
        ),
    )
    op.create_index(
        "ix_web_push_subscriptions_user_id",
        "web_push_subscriptions",
        ["user_id"],
    )

    op.create_table(
        "circle_telegram_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "circle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("circles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("bot_token", sa.String(255), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("group_chat_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_circle_telegram_configs_circle_id",
        "circle_telegram_configs",
        ["circle_id"],
    )
    op.execute(
        "COMMENT ON COLUMN circle_telegram_configs.bot_token IS "
        "'Secret Telegram bot token (BotFather). Never returned by the "
        "API.'"
    )
    op.execute(
        "COMMENT ON COLUMN circle_telegram_configs.mode IS "
        "'Delivery mode: group (broadcast) or dm (per-member).'"
    )

    op.create_table(
        "telegram_member_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "circle_telegram_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("circle_telegram_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "circle_telegram_config_id",
            "user_id",
            name="uq_telegram_link_config_user",
        ),
    )
    op.create_index(
        "ix_telegram_member_links_config_id",
        "telegram_member_links",
        ["circle_telegram_config_id"],
    )
    op.create_index(
        "ix_telegram_member_links_user_id",
        "telegram_member_links",
        ["user_id"],
    )

    op.create_table(
        "notification_channel_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "notification_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "delivery_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_deliveries.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error", sa.String(512), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_notif_channel_attempts_event_id",
        "notification_channel_attempts",
        ["notification_event_id"],
    )
    op.execute(
        "COMMENT ON COLUMN notification_channel_attempts.channel IS "
        "'Channel key: email, webpush, or telegram.'"
    )
    op.execute(
        "COMMENT ON COLUMN notification_channel_attempts.status IS "
        "'Attempt outcome: sent, failed, or skipped.'"
    )


def downgrade() -> None:
    """Drop the delivery-layer tables in reverse dependency order."""
    op.drop_index(
        "ix_notif_channel_attempts_event_id",
        table_name="notification_channel_attempts",
    )
    op.drop_table("notification_channel_attempts")

    op.drop_index(
        "ix_telegram_member_links_user_id",
        table_name="telegram_member_links",
    )
    op.drop_index(
        "ix_telegram_member_links_config_id",
        table_name="telegram_member_links",
    )
    op.drop_table("telegram_member_links")

    op.drop_index(
        "ix_circle_telegram_configs_circle_id",
        table_name="circle_telegram_configs",
    )
    op.drop_table("circle_telegram_configs")

    op.drop_index(
        "ix_web_push_subscriptions_user_id",
        table_name="web_push_subscriptions",
    )
    op.drop_table("web_push_subscriptions")

    op.drop_index(
        "uq_user_notif_settings_user",
        table_name="user_notification_settings",
    )
    op.drop_table("user_notification_settings")
