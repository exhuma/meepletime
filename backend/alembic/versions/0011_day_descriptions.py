"""Add day_descriptions: static per-day session detail.

Revision ID: 0011_day_descriptions
Revises: 0010_user_image
Create Date: 2026-06-16 00:00:00.000000

A description is static session detail for a circle-day, distinct from
the threaded ``day_notes``. The nullable ``host_user_id`` distinguishes
the single circle-wide description (NULL) from per-host descriptions.
The canonical payload is a Quill Delta document stored as JSONB. The
unique constraint uses NULLS NOT DISTINCT so the circle-wide row is a
true singleton.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011_day_descriptions"
down_revision: str | None = "0010_user_image"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the day_descriptions table."""
    op.create_table(
        "day_descriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "circle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("circles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column(
            "host_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("content_delta", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "circle_id",
            "local_date",
            "host_user_id",
            name="uq_day_description",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(
        "ix_day_descriptions_circle_id_local_date",
        "day_descriptions",
        ["circle_id", "local_date"],
    )


def downgrade() -> None:
    """Drop the day_descriptions table."""
    op.drop_index(
        "ix_day_descriptions_circle_id_local_date",
        table_name="day_descriptions",
    )
    op.drop_table("day_descriptions")
