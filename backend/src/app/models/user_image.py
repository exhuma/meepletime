"""ORM model for user profile images stored as binary blobs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserImage(Base):
    """
    Uploaded profile-picture bytes for a user, stored in the database.

    One row per user (1:1). Kept in a separate table from ``users`` so
    that loading a user never pulls the image blob. The bytes are
    served by a public endpoint keyed on the unguessable user UUID,
    mirroring :class:`CircleImage`; the resolved ``avatar_ref`` points
    at that endpoint with a cache-busting version from ``updated_at``.
    """

    __tablename__ = "user_images"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="image")
