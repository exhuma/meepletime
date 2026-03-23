"""ORM model for day availability records."""

import enum
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AvailabilityState(str, enum.Enum):
    attending = "attending"
    hosting = "hosting"


class DayAvailability(Base):
    __tablename__ = "day_availabilities"
    __table_args__ = (
        UniqueConstraint(
            "circle_id", "user_id", "local_date", name="uq_circle_user_date"
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
    state: Mapped[AvailabilityState] = mapped_column(
        SAEnum(AvailabilityState, name="availabilitystate"), nullable=False
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

    circle: Mapped["Circle"] = relationship(
        "Circle", back_populates="availabilities"
    )
    user: Mapped["User"] = relationship("User", back_populates="availabilities")
