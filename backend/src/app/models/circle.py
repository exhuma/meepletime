"""ORM model for circles."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Circle(Base):
    __tablename__ = "circles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="UTC"
    )
    invite_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    host_needed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    minimum_attendees: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    soft_max_attendees: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    hard_max_attendees: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    external_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
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

    memberships: Mapped[list["CircleMembership"]] = relationship(
        "CircleMembership", back_populates="circle"
    )
    availabilities: Mapped[list["DayAvailability"]] = relationship(
        "DayAvailability", back_populates="circle"
    )
    host_day_constraints: Mapped[list["HostDayConstraint"]] = relationship(
        "HostDayConstraint", back_populates="circle"
    )
    day_notes: Mapped[list["DayNote"]] = relationship(
        "DayNote", back_populates="circle"
    )
    notification_events: Mapped[list["NotificationEvent"]] = relationship(
        "NotificationEvent", back_populates="circle"
    )
