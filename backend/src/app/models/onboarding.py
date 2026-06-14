"""ORM model for per-user onboarding / guided-tour state.

Holds whether a user has seen the welcome intro and the open-ended
set of guided-tour tip keys they have already been shown. One row
per user, mirroring :class:`UserNotificationSettings`.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserOnboardingState(Base):
    """
    Per-user onboarding progress. One row per user.

    ``seen_tips`` is an open-ended JSON array of tour-tip keys the
    user has already been shown; it is treated as a set in the
    service layer. The ``JSON`` column type degrades to ``TEXT``
    under the SQLite test engine.
    """

    __tablename__ = "user_onboarding_state"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    welcome_seen: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    seen_tips: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
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
