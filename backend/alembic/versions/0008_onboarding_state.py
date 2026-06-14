"""Add user_onboarding_state table.

Revision ID: 0008_onboarding_state
Revises: 0007_circle_image
Create Date: 2026-06-14 00:00:00.000000

Stores per-user onboarding progress: whether the welcome intro has
been seen and the set of guided-tour tip keys already shown. One row
per user. ``seen_tips`` is a JSONB array treated as a set in the
service layer.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0008_onboarding_state"
down_revision: str | None = "0007_circle_image"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the user_onboarding_state table."""
    op.create_table(
        "user_onboarding_state",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "welcome_seen",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "seen_tips",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_user_onboarding_state_user_id",
        "user_onboarding_state",
        ["user_id"],
        unique=True,
    )
    op.execute(
        "COMMENT ON TABLE user_onboarding_state IS "
        "'Per-user onboarding progress: welcome-seen flag and the "
        "set of guided-tour tip keys already shown (1 row per user).'"
    )


def downgrade() -> None:
    """Drop the user_onboarding_state table."""
    op.drop_index(
        "ix_user_onboarding_state_user_id",
        table_name="user_onboarding_state",
    )
    op.drop_table("user_onboarding_state")
