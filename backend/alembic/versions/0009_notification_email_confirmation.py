"""Add notification_email column and email_confirmations table.

Revision ID: 0009_email_confirmation
Revises: 0008_onboarding_state
Create Date: 2026-06-14 00:00:00.000000

Adds the confirmed notification address on user_notification_settings
and a one-row-per-user table holding the pending confirmation token,
the address awaiting confirmation, and its expiry.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_email_confirmation"
down_revision: str | None = "0008_onboarding_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the column and the email_confirmations table."""
    op.add_column(
        "user_notification_settings",
        sa.Column("notification_email", sa.String(length=255), nullable=True),
    )
    op.create_table(
        "email_confirmations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pending_email", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_email_confirmations_user_id",
        "email_confirmations",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_email_confirmations_token",
        "email_confirmations",
        ["token"],
    )


def downgrade() -> None:
    """Drop the table and the column."""
    op.drop_index(
        "ix_email_confirmations_token", table_name="email_confirmations"
    )
    op.drop_index(
        "ix_email_confirmations_user_id", table_name="email_confirmations"
    )
    op.drop_table("email_confirmations")
    op.drop_column("user_notification_settings", "notification_email")
