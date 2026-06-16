"""ORM model for day descriptions.

A *description* is static session detail attached to a circle-day,
distinct from the threaded :class:`DayNote`. It comes in two shapes
keyed by the nullable ``host_user_id``:

* ``host_user_id IS NULL`` — the single circle-wide description, used
  by circles that do not require a host (owner/admin owned).
* ``host_user_id`` set — that host's own description for the day, used
  by host-required circles so members can compare host offers.

The canonical stored representation is a Quill *Delta* document
(JSON); HTML is only ever derived at render time, never stored.
"""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DayDescription(Base):
    """One description row for a circle-day, optionally per host."""

    __tablename__ = "day_descriptions"
    __table_args__ = (
        # One circle-wide row (host_user_id NULL) and one row per host
        # per day. NULLS NOT DISTINCT makes the NULL-host row a true
        # singleton on Postgres; the router also upserts at the
        # application level (the SQLite test engine ignores the kwarg).
        UniqueConstraint(
            "circle_id",
            "local_date",
            "host_user_id",
            name="uq_day_description",
            postgresql_nulls_not_distinct=True,
        ),
        Index(
            "ix_day_descriptions_circle_id_local_date",
            "circle_id",
            "local_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    host_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    content_delta: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    circle: Mapped["Circle"] = relationship(
        "Circle", back_populates="day_descriptions"
    )
