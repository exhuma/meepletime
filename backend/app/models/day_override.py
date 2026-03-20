import uuid
from datetime import datetime, date, timezone

from sqlalchemy import Date, DateTime, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DayOverride(Base):
    __tablename__ = "day_overrides"
    __table_args__ = (UniqueConstraint("circle_id", "local_date", name="uq_override_circle_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("circles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    override_host_needed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    override_minimum_attendees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    override_soft_max_attendees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    override_hard_max_attendees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    circle: Mapped["Circle"] = relationship("Circle", back_populates="day_overrides")
