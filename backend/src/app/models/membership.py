"""ORM model for circle memberships."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class CircleMembership(Base):
    __tablename__ = "circle_memberships"
    __table_args__ = (
        UniqueConstraint("circle_id", "pseudonym", name="uq_circle_pseudonym"),
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
    pseudonym: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[MemberRole] = mapped_column(
        SAEnum(MemberRole, name="memberrole"),
        nullable=False,
        default=MemberRole.member,
    )
    can_host_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    notification_preferences: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )

    circle: Mapped["Circle"] = relationship(
        "Circle", back_populates="memberships"
    )
    user: Mapped["User"] = relationship("User", back_populates="memberships")
