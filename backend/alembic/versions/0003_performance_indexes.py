"""Add performance indexes missing from initial schema.

Revision ID: 0003_performance_indexes
Revises: 0002_oidc_auth
Create Date: 2026-03-30 00:00:00.000000

Adds two indexes identified as hot paths after post-migration
query analysis:

* ``ix_circles_created_by_user_id`` — speeds up FK lookups and
  any ad-hoc "circles I created" queries.
* ``ix_day_notes_circle_id_local_date`` — composite index for the
  common pattern of fetching all notes for a specific
  (circle, date) pair without scanning individual single-column
  indexes.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_performance_indexes"
down_revision: str | None = "0002_oidc_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing performance indexes."""
    op.create_index(
        "ix_circles_created_by_user_id",
        "circles",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_day_notes_circle_id_local_date",
        "day_notes",
        ["circle_id", "local_date"],
    )


def downgrade() -> None:
    """Remove indexes added by this revision."""
    op.drop_index("ix_day_notes_circle_id_local_date", table_name="day_notes")
    op.drop_index("ix_circles_created_by_user_id", table_name="circles")
