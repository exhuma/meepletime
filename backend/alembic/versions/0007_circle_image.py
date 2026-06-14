"""Add circle_images table for stored hero image blobs.

Revision ID: 0007_circle_image
Revises: 0006_notification_delivery
Create Date: 2026-06-14 00:00:00.000000

Stores uploaded circle hero images as binary blobs in the database
(one row per circle). Kept separate from ``circles`` so listing
circles never loads the blob. ``circles.image_ref`` continues to
hold an opaque string and points at the public serving endpoint
once an image is uploaded.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007_circle_image"
down_revision: str | None = "0006_notification_delivery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the circle_images table."""
    op.create_table(
        "circle_images",
        sa.Column(
            "circle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("circles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        "COMMENT ON TABLE circle_images IS "
        "'Uploaded hero image bytes for a circle (1:1). Served by a "
        "public endpoint keyed on the circle UUID.'"
    )


def downgrade() -> None:
    """Drop the circle_images table."""
    op.drop_table("circle_images")
