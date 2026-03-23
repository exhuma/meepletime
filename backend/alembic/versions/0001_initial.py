"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "circles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_ref", sa.String(512), nullable=True),
        sa.Column(
            "timezone", sa.String(64), nullable=False, server_default="UTC"
        ),
        sa.Column(
            "invite_token",
            postgresql.UUID(as_uuid=True),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "host_needed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("minimum_attendees", sa.Integer(), nullable=True),
        sa.Column("soft_max_attendees", sa.Integer(), nullable=True),
        sa.Column("hard_max_attendees", sa.Integer(), nullable=True),
        sa.Column("external_links", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "circle_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column("pseudonym", sa.String(64), nullable=False),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "member", name="memberrole"),
            nullable=False,
        ),
        sa.Column(
            "can_host_default",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notification_preferences", postgresql.JSON(), nullable=True),
        sa.UniqueConstraint(
            "circle_id", "pseudonym", name="uq_circle_pseudonym"
        ),
    )
    op.create_index(
        "ix_circle_memberships_circle_id", "circle_memberships", ["circle_id"]
    )
    op.create_index(
        "ix_circle_memberships_user_id", "circle_memberships", ["user_id"]
    )

    op.create_table(
        "day_availabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
            "state",
            sa.Enum("attending", "hosting", name="availabilitystate"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "circle_id", "user_id", "local_date", name="uq_circle_user_date"
        ),
    )
    op.create_index(
        "ix_day_availabilities_circle_id", "day_availabilities", ["circle_id"]
    )
    op.create_index(
        "ix_day_availabilities_user_id", "day_availabilities", ["user_id"]
    )
    op.create_index(
        "ix_day_availabilities_local_date", "day_availabilities", ["local_date"]
    )

    op.create_table(
        "day_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "circle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("circles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("override_host_needed", sa.Boolean(), nullable=True),
        sa.Column("override_minimum_attendees", sa.Integer(), nullable=True),
        sa.Column("override_soft_max_attendees", sa.Integer(), nullable=True),
        sa.Column("override_hard_max_attendees", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "circle_id", "local_date", name="uq_override_circle_date"
        ),
    )
    op.create_index(
        "ix_day_overrides_circle_id", "day_overrides", ["circle_id"]
    )
    op.create_index(
        "ix_day_overrides_local_date", "day_overrides", ["local_date"]
    )

    op.create_table(
        "day_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_day_notes_circle_id", "day_notes", ["circle_id"])
    op.create_index("ix_day_notes_user_id", "day_notes", ["user_id"])
    op.create_index("ix_day_notes_local_date", "day_notes", ["local_date"])

    op.create_table(
        "notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "circle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("circles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_notification_events_circle_id", "notification_events", ["circle_id"]
    )
    op.create_index(
        "ix_notification_events_local_date",
        "notification_events",
        ["local_date"],
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "notification_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_notification_deliveries_event_id",
        "notification_deliveries",
        ["notification_event_id"],
    )
    op.create_index(
        "ix_notification_deliveries_user_id",
        "notification_deliveries",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("notification_deliveries")
    op.drop_table("notification_events")
    op.drop_table("day_notes")
    op.drop_table("day_overrides")
    op.drop_table("day_availabilities")
    op.drop_table("circle_memberships")
    op.drop_table("circles")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS memberrole")
    op.execute("DROP TYPE IF EXISTS availabilitystate")
