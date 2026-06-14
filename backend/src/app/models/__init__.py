"""ORM model registry — imports all models for SQLAlchemy metadata."""

from app.models.auth_identity import AuthIdentity
from app.models.availability import AvailabilityState, DayAvailability
from app.models.circle import Circle
from app.models.circle_image import CircleImage
from app.models.day_note import DayNote
from app.models.host_day_constraint import HostDayConstraint
from app.models.membership import CircleMembership, MemberRole
from app.models.notification import (
    NotificationChannelAttempt,
    NotificationDelivery,
    NotificationEvent,
)
from app.models.notification_settings import (
    CircleTelegramConfig,
    TelegramMemberLink,
    UserNotificationSettings,
    WebPushSubscription,
)
from app.models.user import User

__all__ = [
    "AuthIdentity",
    "User",
    "Circle",
    "CircleImage",
    "CircleMembership",
    "MemberRole",
    "DayAvailability",
    "AvailabilityState",
    "HostDayConstraint",
    "DayNote",
    "NotificationEvent",
    "NotificationDelivery",
    "NotificationChannelAttempt",
    "UserNotificationSettings",
    "WebPushSubscription",
    "CircleTelegramConfig",
    "TelegramMemberLink",
]
