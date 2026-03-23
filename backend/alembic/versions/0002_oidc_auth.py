"""migrate users table and add auth_identities for OIDC

Revision ID: 0002_oidc_auth
Revises: 0001_initial
Create Date: 2024-01-02 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_oidc_auth"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove local-auth columns, add OIDC identity table."""
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "is_active")

    op.add_column(
        "users",
        sa.Column("display_name", sa.String(255), nullable=True),
    )
    op.execute(
        "COMMENT ON COLUMN users.display_name IS "
        "'Display name sourced from OIDC name claim.'"
    )

    op.create_table(
        "auth_identities",
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
            "provider",
            sa.String(512),
            nullable=False,
        ),
        sa.Column(
            "subject",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_auth_identities_user_id",
        "auth_identities",
        ["user_id"],
    )
    op.create_unique_constraint(
        "uq_auth_identities_provider_subject",
        "auth_identities",
        ["provider", "subject"],
    )
    op.execute(
        "COMMENT ON TABLE auth_identities IS "
        "'Maps an external OIDC identity to a local user.'"
    )
    op.execute(
        "COMMENT ON COLUMN auth_identities.provider IS "
        "'OIDC issuer URL (Keycloak realm URL).'"
    )
    op.execute(
        "COMMENT ON COLUMN auth_identities.subject IS "
        "'The sub claim from the OIDC access token.'"
    )


def downgrade() -> None:
    """
    Re-add local-auth columns, remove OIDC identity table.

    Note: hashed_password data cannot be recovered after downgrade.
    """
    op.drop_table("auth_identities")
    op.drop_column("users", "display_name")
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "hashed_password",
            sa.String(255),
            nullable=False,
            server_default="",
        ),
    )
