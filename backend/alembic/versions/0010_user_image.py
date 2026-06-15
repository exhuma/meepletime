"""Add user profile pictures: users.picture_url + user_images table.

Revision ID: 0010_user_image
Revises: 0009_email_confirmation
Create Date: 2026-06-15 00:00:00.000000

Adds the identity-provider ``picture`` URL captured at provisioning
and a one-row-per-user table holding an uploaded profile-picture blob.
Both feed the avatar resolution chain (upload > IDP picture > gravatar
> initials). Mirrors ``circle_images``.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010_user_image"
down_revision: str | None = "0009_email_confirmation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add picture_url and create the user_images table."""
    op.add_column(
        "users",
        sa.Column("picture_url", sa.String(length=512), nullable=True),
    )
    op.create_table(
        "user_images",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        "COMMENT ON TABLE user_images IS "
        "'Uploaded profile-picture bytes for a user (1:1). Served by a "
        "public endpoint keyed on the user UUID.'"
    )


def downgrade() -> None:
    """Drop the user_images table and the picture_url column."""
    op.drop_table("user_images")
    op.drop_column("users", "picture_url")
