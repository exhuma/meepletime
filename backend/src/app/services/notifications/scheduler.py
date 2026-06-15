"""Background scheduling and debounce for notification evaluation.

Wraps APScheduler's synchronous ``BackgroundScheduler`` to debounce
derived-state evaluation per ``circle_id`` as required by the
notification contract (§12.1). Repeated availability changes anywhere
in a circle collapse into one evaluation that emits a single aggregated
summary notification, instead of one notification per changed day.
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.services.notifications.channels import register_default_channels
from app.services.notifications.evaluation import evaluate_and_notify_batch

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# Guards the pending-state dicts; ``trigger_notification_eval`` runs in
# request threads while jobs run in APScheduler worker threads.
_lock = threading.Lock()
# Per-circle pending state, keyed by ``str(circle_id)``.
_pending_dates: dict[str, set[date]] = {}
_pending_jobs: dict[str, str] = {}
_pending_since: dict[str, datetime] = {}

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


def _compute_run_at(
    now: datetime, since: datetime, settings: Settings
) -> datetime:
    """
    Return the next run time for a circle's pending evaluation.

    The sliding window pushes the run time out on every change, but it
    is capped at ``since + max_wait`` so a circle that is edited
    continuously still flushes a summary eventually.

    :param now: Current time (UTC).
    :param since: When this pending batch first accumulated.
    :param settings: Application settings.
    :returns: The clamped run time (never earlier than ``now``).
    """
    run_at = now + timedelta(
        seconds=settings.NOTIFICATION_AGGREGATION_WINDOW_SECONDS
    )
    max_run_at = since + timedelta(
        seconds=settings.NOTIFICATION_AGGREGATION_MAX_WAIT_SECONDS
    )
    if run_at > max_run_at:
        run_at = max_run_at
    if run_at < now:
        run_at = now
    return run_at


def trigger_notification_eval(
    circle_id: uuid.UUID, local_date: date, db_factory: DbFactory
) -> None:
    """
    Schedule a debounced, per-circle notification evaluation.

    Accumulates the changed date for the circle and (re)schedules a
    single job. Repeated calls within the sliding window collapse into
    one evaluation; the run time is capped so continuous editing still
    flushes (see :func:`_compute_run_at`).

    :param circle_id: Circle whose day changed.
    :param local_date: The circle-local date that changed.
    :param db_factory: Callable returning a fresh Session for the job.
    """
    settings = get_settings()
    key = str(circle_id)
    now = datetime.now(UTC)
    with _lock:
        _pending_dates.setdefault(key, set()).add(local_date)
        since = _pending_since.setdefault(key, now)

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

        run_at = _compute_run_at(now, since, settings)
        job = scheduler.add_job(
            _run_evaluation_batch,
            "date",
            run_date=run_at,
            args=[circle_id, db_factory],
            id=str(uuid.uuid4()),
        )
        _pending_jobs[key] = job.id


def _run_evaluation_batch(circle_id: uuid.UUID, db_factory: DbFactory) -> None:
    """
    Execute the per-circle batch evaluation and clean up state.

    The pending date set is popped under the lock at the very start so
    that any change arriving between this job firing and the pop is not
    lost — it stays pending and reschedules a fresh job.

    :param circle_id: Circle being evaluated.
    :param db_factory: Callable returning a fresh Session.
    """
    key = str(circle_id)
    with _lock:
        dates = _pending_dates.pop(key, set())
        _pending_jobs.pop(key, None)
        _pending_since.pop(key, None)
    if not dates:
        return
    db = db_factory()
    try:
        evaluate_and_notify_batch(circle_id, sorted(dates), db)
    except Exception as exc:
        logger.exception(
            "Error evaluating notifications for circle %s: %s",
            circle_id,
            exc,
        )
    finally:
        db.close()
