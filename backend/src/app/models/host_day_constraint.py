"""ORM model for per-host per-day capacity constraints."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class HostDayConstraint(Base):
    """
    Situational capacity constraints set by a hosting member for a
    specific date.

    Represents conditions that may differ from circle defaults on a
    given day — for example, reduced space due to renovations. Keyed
    by ``(circle_id, user_id, local_date)``; at most one constraint
    row per member per day per circle.

    Absence of a row means the circle defaults apply for that member.
    """

    __tablename__ = "host_day_constraints"
    __table_args__ = (
        UniqueConstraint(
            "circle_id",
            "user_id",
            "local_date",
            name="uq_host_constraint_circle_user_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    override_minimum_attendees: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    override_soft_max_attendees: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    override_hard_max_attendees: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    circle: Mapped[Circle] = relationship(
        "Circle", back_populates="host_day_constraints"
    )
    user: Mapped[User] = relationship(
        "User", back_populates="host_day_constraints"
    )
