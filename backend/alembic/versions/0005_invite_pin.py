"""Replace UUID invite_token with a short human-typable PIN.

Revision ID: 0005_invite_pin
Revises: 0004_host_day_constraints
Create Date: 2026-06-12 00:00:00.000000

The ``circles.invite_token`` column changes from a 36-char UUID to a
6-char unambiguous base32 PIN (alphabet excludes ``0 O 1 I L``).

Data-loss note: a UUID cannot be losslessly shortened, so every
existing invite token is *replaced* with a freshly generated PIN.
Previously shared invite links / QR codes become invalid. This is
acceptable: invite tokens are explicitly regenerable. The downgrade
likewise replaces every PIN with a fresh UUID.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.services.invite import generate_pin

revision: str = "0005_invite_pin"
down_revision: str | None = "0004_host_day_constraints"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Swap the UUID invite_token for a unique 6-char PIN."""
    conn = op.get_bind()

    # 1. Temporary nullable column to hold the new PINs.
    op.add_column(
        "circles",
        sa.Column("invite_pin", sa.String(6), nullable=True),
    )

    # 2. Backfill a distinct PIN for every existing circle.
    rows = conn.execute(sa.text("SELECT id FROM circles")).fetchall()
    used: set[str] = set()
    for (circle_id,) in rows:
        pin = generate_pin()
        while pin in used:
            pin = generate_pin()
        used.add(pin)
        conn.execute(
            sa.text("UPDATE circles SET invite_pin = :pin WHERE id = :id"),
            {"pin": pin, "id": circle_id},
        )

    # 3. Enforce NOT NULL, drop the old UUID column (and its implicit
    #    unique constraint), then promote the temp column.
    op.alter_column("circles", "invite_pin", nullable=False)
    op.drop_column("circles", "invite_token")
    op.alter_column("circles", "invite_pin", new_column_name="invite_token")
    op.create_unique_constraint(
        "uq_circles_invite_token", "circles", ["invite_token"]
    )
    op.execute(
        "COMMENT ON COLUMN circles.invite_token IS "
        "'Unambiguous 6-char base32 invite PIN (excludes 0/O/1/I/L), "
        "globally unique, regenerable.'"
    )


def downgrade() -> None:
    """Restore a UUID invite_token, replacing every PIN."""
    conn = op.get_bind()

    op.drop_constraint("uq_circles_invite_token", "circles", type_="unique")
    op.add_column(
        "circles",
        sa.Column(
            "invite_uuid",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    rows = conn.execute(sa.text("SELECT id FROM circles")).fetchall()
    for (circle_id,) in rows:
        conn.execute(
            sa.text("UPDATE circles SET invite_uuid = :tok WHERE id = :id"),
            {"tok": str(uuid.uuid4()), "id": circle_id},
        )

    op.alter_column("circles", "invite_uuid", nullable=False)
    op.drop_column("circles", "invite_token")
    op.alter_column("circles", "invite_uuid", new_column_name="invite_token")
    # Recreate the original implicitly-named unique constraint.
    op.create_unique_constraint(
        "circles_invite_token_key", "circles", ["invite_token"]
    )
