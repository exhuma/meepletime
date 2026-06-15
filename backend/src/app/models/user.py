"""ORM model for the local user profile."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    Project-local user profile.

    Identity is established exclusively via auth_identities.
    No credentials are stored on this table.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    # Profile picture URL from the identity provider's ``picture``
    # claim, captured at provisioning. Used as the avatar fallback
    # when the user has not uploaded their own image.
    picture_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
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

    memberships: Mapped[list[CircleMembership]] = relationship(
        "CircleMembership",
        back_populates="user",
    )
    availabilities: Mapped[list[DayAvailability]] = relationship(
        "DayAvailability",
        back_populates="user",
    )
    day_notes: Mapped[list[DayNote]] = relationship(
        "DayNote",
        back_populates="user",
    )
    host_day_constraints: Mapped[list[HostDayConstraint]] = relationship(
        "HostDayConstraint",
        back_populates="user",
    )
    auth_identities: Mapped[list[AuthIdentity]] = relationship(
        "AuthIdentity",
        back_populates="user",
    )
    image: Mapped[UserImage | None] = relationship(
        "UserImage",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
