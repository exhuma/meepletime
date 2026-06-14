"""ORM model for circle hero images stored as binary blobs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CircleImage(Base):
    """
    Hero image bytes for a circle, stored in the database.

    One row per circle (1:1). Kept in a separate table from
    ``circles`` so that listing circles never loads the image blob.
    The bytes are served by a public endpoint keyed on the
    unguessable circle UUID; ``Circle.image_ref`` points at that
    endpoint with a cache-busting version derived from ``updated_at``.
    """

    __tablename__ = "circle_images"

    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
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

    circle: Mapped[Circle] = relationship("Circle", back_populates="image")
