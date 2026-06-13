"""Notification scheduling, evaluation, and delivery package.

Public API is re-exported here so existing import sites
(``from app.services.notifications import ...``) keep working after the
single-module file was split into this package.
"""

from app.services.notifications.evaluation import evaluate_and_notify
from app.services.notifications.scheduler import (
    shutdown_scheduler,
    start_scheduler,
    trigger_notification_eval,
)

__all__ = [
    "evaluate_and_notify",
    "trigger_notification_eval",
    "start_scheduler",
    "shutdown_scheduler",
]
