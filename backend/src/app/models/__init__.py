"""ORM model registry — imports all models for SQLAlchemy metadata."""

from app.models.auth_identity import AuthIdentity
from app.models.availability import AvailabilityState, DayAvailability
from app.models.circle import Circle
from app.models.circle_image import CircleImage
from app.models.day_description import DayDescription
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
    EmailConfirmation,
    TelegramMemberLink,
    UserNotificationSettings,
    WebPushSubscription,
)
from app.models.onboarding import UserOnboardingState
from app.models.user import User
from app.models.user_image import UserImage

__all__ = [
    "AuthIdentity",
    "User",
    "UserImage",
    "Circle",
    "CircleImage",
    "CircleMembership",
    "MemberRole",
    "DayAvailability",
    "AvailabilityState",
    "HostDayConstraint",
    "DayNote",
    "DayDescription",
    "NotificationEvent",
    "NotificationDelivery",
    "NotificationChannelAttempt",
    "EmailConfirmation",
    "UserNotificationSettings",
    "WebPushSubscription",
    "CircleTelegramConfig",
    "TelegramMemberLink",
    "UserOnboardingState",
]
