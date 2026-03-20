import uuid
import logging
from datetime import date, datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
# Tracks pending debounce jobs: key = (circle_id_str, date_str) -> job_id
_pending_jobs: dict[tuple[str, str], str] = {}


def start_scheduler() -> None:
    """Start the APScheduler background scheduler if it is not already running."""
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler() -> None:
    """Shut down the APScheduler background scheduler without waiting for pending jobs."""
    if scheduler.running:
        scheduler.shutdown(wait=False)


def _make_key(circle_id: uuid.UUID, local_date: date) -> tuple[str, str]:
    """Return a stable dict key for *(circle_id, local_date)* tracking pending debounce jobs."""
    return (str(circle_id), str(local_date))


def trigger_notification_eval(circle_id: uuid.UUID, local_date: date, db_factory) -> None:
    """
    Schedule a debounced notification evaluation.
    Collapses repeated calls within the debounce window into one evaluation.
    db_factory is a callable that returns a new Session (used inside the scheduled job).
    """
    key = _make_key(circle_id, local_date)
    existing_job_id = _pending_jobs.get(key)
    if existing_job_id:
        try:
            scheduler.remove_job(existing_job_id)
        except Exception:
            pass

    from datetime import timedelta

    run_at = datetime.now(timezone.utc) + timedelta(seconds=settings.NOTIFICATION_DEBOUNCE_SECONDS)
    job = scheduler.add_job(
        _run_evaluation,
        "date",
        run_date=run_at,
        args=[circle_id, local_date, db_factory],
        id=str(uuid.uuid4()),
    )
    _pending_jobs[key] = job.id


def _run_evaluation(circle_id: uuid.UUID, local_date: date, db_factory) -> None:
    """Execute the notification evaluation job and clean up the pending-job registry."""
    key = _make_key(circle_id, local_date)
    _pending_jobs.pop(key, None)
    db = db_factory()
    try:
        evaluate_and_notify(circle_id, local_date, db)
    except Exception as exc:
        logger.exception("Error evaluating notifications for %s %s: %s", circle_id, local_date, exc)
    finally:
        db.close()


def evaluate_and_notify(circle_id: uuid.UUID, local_date: date, db: Session) -> None:
    """Evaluate derived viability for *(circle_id, local_date)* and create notification events if warranted.

    Anti-storm logic suppresses duplicate events that fall within twice the debounce window.
    """
    from app.models.membership import CircleMembership
    from app.models.notification import NotificationEvent, NotificationDelivery
    from app.services.viability import compute_viability

    circle = db.query(Circle).filter(Circle.id == circle_id).first()
    if not circle:
        return

    viability = compute_viability(circle, local_date, db)

    # Determine event type based on derived state
    if viability.attendee_count == 0:
        return  # No candidate – nothing to notify about

    if viability.is_viable:
        event_type = "viable"
    else:
        event_type = "non_viable_candidate"

    # Anti-storm: check if an identical event was already emitted recently
    from datetime import timedelta

    recent_cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.NOTIFICATION_DEBOUNCE_SECONDS * 2)
    existing = (
        db.query(NotificationEvent)
        .filter(
            NotificationEvent.circle_id == circle_id,
            NotificationEvent.local_date == local_date,
            NotificationEvent.event_type == event_type,
            NotificationEvent.created_at >= recent_cutoff,
        )
        .first()
    )
    if existing:
        return

    event = NotificationEvent(
        circle_id=circle_id,
        local_date=local_date,
        event_type=event_type,
    )
    db.add(event)
    db.flush()

    # Create delivery rows for all members
    members = (
        db.query(CircleMembership).filter(CircleMembership.circle_id == circle_id).all()
    )
    for member in members:
        prefs = member.notification_preferences or {}
        if prefs.get("disabled"):
            continue
        delivery = NotificationDelivery(
            notification_event_id=event.id,
            user_id=member.user_id,
        )
        db.add(delivery)

    db.commit()
    logger.info("Notification event %s created for circle %s on %s", event_type, circle_id, local_date)
