"""Background scheduling and debounce for notification evaluation.

Wraps APScheduler's synchronous ``BackgroundScheduler`` to debounce
derived-state evaluation per ``(circle_id, local_date)`` as required by
the notification contract (§12.1).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.notifications.channels import register_default_channels
from app.services.notifications.evaluation import evaluate_and_notify

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
# Tracks pending debounce jobs: key = (circle_id_str, date_str) -> job_id
_pending_jobs: dict[tuple[str, str], str] = {}

# A callable returning a fresh Session for use inside scheduled jobs.
DbFactory = Callable[[], Session]


def start_scheduler() -> None:
    """
    Start the scheduler and register built-in channels if needed.
    """
    register_default_channels()
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler() -> None:
    """
    Shut down the scheduler without waiting for pending jobs.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)


def _make_key(circle_id: uuid.UUID, local_date: date) -> tuple[str, str]:
    """
    Return a stable dict key for *(circle_id, local_date)*.

    :param circle_id: Circle identifier.
    :param local_date: Circle-local date.
    :returns: A hashable ``(str, str)`` key.
    """
    return (str(circle_id), str(local_date))


def trigger_notification_eval(
    circle_id: uuid.UUID, local_date: date, db_factory: DbFactory
) -> None:
    """
    Schedule a debounced notification evaluation.

    Collapses repeated calls within the debounce window into one
    evaluation.

    :param circle_id: Circle whose day changed.
    :param local_date: The circle-local date that changed.
    :param db_factory: Callable returning a fresh Session for the job.
    """
    key = _make_key(circle_id, local_date)
    existing_job_id = _pending_jobs.get(key)
    if existing_job_id:
        try:
            scheduler.remove_job(existing_job_id)
        except Exception:
            # The job may have already executed — this is expected.
            logger.debug(
                "Could not remove pending job %s (already ran?)",
                existing_job_id,
            )

    run_at = datetime.now(UTC) + timedelta(
        seconds=get_settings().NOTIFICATION_DEBOUNCE_SECONDS
    )
    job = scheduler.add_job(
        _run_evaluation,
        "date",
        run_date=run_at,
        args=[circle_id, local_date, db_factory],
        id=str(uuid.uuid4()),
    )
    _pending_jobs[key] = job.id


def _run_evaluation(
    circle_id: uuid.UUID, local_date: date, db_factory: DbFactory
) -> None:
    """
    Execute the evaluation job and clean up the pending registry.

    :param circle_id: Circle being evaluated.
    :param local_date: Circle-local date being evaluated.
    :param db_factory: Callable returning a fresh Session.
    """
    key = _make_key(circle_id, local_date)
    _pending_jobs.pop(key, None)
    db = db_factory()
    try:
        evaluate_and_notify(circle_id, local_date, db)
    except Exception as exc:
        logger.exception(
            "Error evaluating notifications for %s %s: %s",
            circle_id,
            local_date,
            exc,
        )
    finally:
        db.close()
