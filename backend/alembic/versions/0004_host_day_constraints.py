"""Replace day_overrides with per-host host_day_constraints.

Revision ID: 0004_host_day_constraints
Revises: 0003_performance_indexes
Create Date: 2026-04-02 00:00:00.000000

Drops the ``day_overrides`` table (circle-day scoped) and creates
``host_day_constraints`` (member-day scoped).  No data is preserved
— the application has not been deployed.

Key differences from the old table:

* Adds ``user_id`` FK; constraint is now per hosting member per day.
* Drops ``override_host_needed``; ``host_needed`` is a circle-level
  policy and is not overridable by individual hosts.
* Unique constraint is ``(circle_id, user_id, local_date)`` instead
  of ``(circle_id, local_date)``.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_host_day_constraints"
down_revision: str | None = "0003_performance_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop day_overrides, create host_day_constraints."""
    op.drop_table("day_overrides")

    op.create_table(
        "host_day_constraints",
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
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column(
            "override_minimum_attendees",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "override_soft_max_attendees",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "override_hard_max_attendees",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "circle_id",
            "user_id",
            "local_date",
            name="uq_host_constraint_circle_user_date",
        ),
    )
    op.create_index(
        "ix_host_day_constraints_circle_id",
        "host_day_constraints",
        ["circle_id"],
    )
    op.create_index(
        "ix_host_day_constraints_user_id",
        "host_day_constraints",
        ["user_id"],
    )
    op.execute(
        "COMMENT ON TABLE host_day_constraints IS "
        "'Situational capacity limits set by a hosting member "
        "for a specific date. Merged with circle defaults using "
        "most-restrictive-wins per field.'"
    )
    op.execute(
        "COMMENT ON COLUMN host_day_constraints.local_date IS "
        "'Date interpreted in the circle timezone, not UTC.'"
    )
    op.execute(
        "COMMENT ON COLUMN "
        "host_day_constraints.override_minimum_attendees IS "
        "'Host-specific floor on attendee count. Merged with "
        "circle default: max(circle, override) applies.'"
    )
    op.execute(
        "COMMENT ON COLUMN "
        "host_day_constraints.override_soft_max_attendees IS "
        "'Host-specific soft capacity ceiling. Merged with "
        "circle default: min(circle, override) applies. "
        "Exceeding this marks the day but keeps it viable.'"
    )
    op.execute(
        "COMMENT ON COLUMN "
        "host_day_constraints.override_hard_max_attendees IS "
        "'Host-specific hard capacity ceiling. Merged with "
        "circle default: min(circle, override) applies. "
        "Exceeding this makes the host non-viable for the day.'"
    )


def downgrade() -> None:
    """Drop host_day_constraints, restore day_overrides."""
    op.drop_table("host_day_constraints")

    op.create_table(
        "day_overrides",
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
        sa.Column("override_host_needed", sa.Boolean(), nullable=True),
        sa.Column(
            "override_minimum_attendees",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "override_soft_max_attendees",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "override_hard_max_attendees",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "circle_id",
            "local_date",
            name="uq_override_circle_date",
        ),
    )
    op.create_index(
        "ix_day_overrides_circle_id", "day_overrides", ["circle_id"]
    )
    op.create_index(
        "ix_day_overrides_local_date", "day_overrides", ["local_date"]
    )
