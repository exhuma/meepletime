import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class MemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class CircleMembership(Base):
    __tablename__ = "circle_memberships"
    __table_args__ = (UniqueConstraint("circle_id", "pseudonym", name="uq_circle_pseudonym"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("circles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pseudonym: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[MemberRole] = mapped_column(
        SAEnum(MemberRole, name="memberrole"), nullable=False, default=MemberRole.member
    )
    can_host_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notification_preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    circle: Mapped["Circle"] = relationship("Circle", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")
