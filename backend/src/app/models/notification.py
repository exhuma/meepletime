"""ORM models for notification events and deliveries."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    circle: Mapped["Circle"] = relationship(
        "Circle", back_populates="notification_events"
    )
    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        "NotificationDelivery", back_populates="notification_event"
    )


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    notification_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    notification_event: Mapped["NotificationEvent"] = relationship(
        "NotificationEvent", back_populates="deliveries"
    )


class NotificationChannelAttempt(Base):
    """
    Audit row for one delivery attempt on one channel.

    Linked to the event always; ``delivery_id``/``user_id`` are set for
    per-user channels (email, web push, telegram DM) and left null for
    circle-level broadcasts (telegram group), which have no single
    recipient user.
    """

    __tablename__ = "notification_channel_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    notification_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_deliveries.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    # Channel key: "email" / "webpush" / "telegram".
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    # Outcome: "sent" / "failed" / "skipped".
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
