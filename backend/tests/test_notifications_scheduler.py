"""Tests for the per-circle notification debounce scheduler."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.notifications import scheduler as sched


class _FakeJob:
    """A stand-in for an APScheduler job."""

    def __init__(self, job_id: str, run_date: datetime) -> None:
        """Record the job id and scheduled run time."""
        self.id = job_id
        self.run_date = run_date


class _FakeScheduler:
    """Records add/remove calls without running anything."""

    def __init__(self) -> None:
        """Start with no jobs."""
        self.jobs: dict[str, _FakeJob] = {}

    def add_job(self, func, trigger, run_date, args, id):  # noqa: A002
        """Store a fake job and return it."""
        job = _FakeJob(id, run_date)
        self.jobs[id] = job
        return job

    def remove_job(self, job_id: str) -> None:
        """Remove a job or raise if it is unknown."""
        if job_id not in self.jobs:
            raise KeyError(job_id)
        del self.jobs[job_id]


@pytest.fixture
def fake_scheduler(monkeypatch: pytest.MonkeyPatch) -> _FakeScheduler:
    """Swap the module scheduler for a fake and reset pending state."""
    fake = _FakeScheduler()
    monkeypatch.setattr(sched, "scheduler", fake)
    sched._pending_dates.clear()
    sched._pending_jobs.clear()
    sched._pending_since.clear()
    yield fake
    sched._pending_dates.clear()
    sched._pending_jobs.clear()
    sched._pending_since.clear()


def _noop_factory():
    """Return a db factory that must never be called in these tests."""

    def _factory():
        raise AssertionError("db_factory should not be called")

    return _factory


def test_collapses_dates_into_single_job(
    fake_scheduler: _FakeScheduler,
) -> None:
    """Ensure many changed days for a circle share one pending job."""
    circle_id = uuid.uuid4()
    key = str(circle_id)
    days = [
        date(2026, 6, 20),
        date(2026, 6, 21),
        date(2026, 6, 22),
    ]
    for day in days:
        sched.trigger_notification_eval(circle_id, day, _noop_factory())

    assert sched._pending_dates[key] == set(days)
    # Each reschedule removed the prior job, leaving exactly one.
    assert len(fake_scheduler.jobs) == 1
    assert sched._pending_jobs[key] in fake_scheduler.jobs


def test_separate_circles_keep_separate_jobs(
    fake_scheduler: _FakeScheduler,
) -> None:
    """Ensure two circles debounce independently."""
    circle_a = uuid.uuid4()
    circle_b = uuid.uuid4()
    sched.trigger_notification_eval(
        circle_a, date(2026, 6, 20), _noop_factory()
    )
    sched.trigger_notification_eval(
        circle_b, date(2026, 6, 20), _noop_factory()
    )
    assert len(fake_scheduler.jobs) == 2
    assert str(circle_a) in sched._pending_jobs
    assert str(circle_b) in sched._pending_jobs


def test_run_batch_pops_state_and_evaluates(
    fake_scheduler: _FakeScheduler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the job pops pending state and evaluates sorted dates."""
    circle_id = uuid.uuid4()
    key = str(circle_id)
    sched._pending_dates[key] = {
        date(2026, 6, 22),
        date(2026, 6, 20),
    }
    sched._pending_jobs[key] = "job-1"
    sched._pending_since[key] = datetime.now(UTC)

    seen: dict[str, object] = {}

    def _fake_eval(cid, dates, db):
        seen["circle_id"] = cid
        seen["dates"] = dates

    closed = {"value": False}

    class _FakeDb:
        def close(self) -> None:
            closed["value"] = True

    monkeypatch.setattr(sched, "evaluate_and_notify_batch", _fake_eval)
    sched._run_evaluation_batch(circle_id, lambda: _FakeDb())

    assert seen["circle_id"] == circle_id
    assert seen["dates"] == [
        date(2026, 6, 20),
        date(2026, 6, 22),
    ]
    assert closed["value"] is True
    assert key not in sched._pending_dates
    assert key not in sched._pending_jobs
    assert key not in sched._pending_since


def test_run_batch_empty_is_noop(
    fake_scheduler: _FakeScheduler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure an empty pending set skips evaluation and the db factory."""
    called = {"value": False}

    def _fake_eval(cid, dates, db):
        called["value"] = True

    monkeypatch.setattr(sched, "evaluate_and_notify_batch", _fake_eval)
    sched._run_evaluation_batch(uuid.uuid4(), _noop_factory())

    assert called["value"] is False


def _settings(window: int, max_wait: int) -> SimpleNamespace:
    """Return a settings stub with the given aggregation windows."""
    return SimpleNamespace(
        NOTIFICATION_AGGREGATION_WINDOW_SECONDS=window,
        NOTIFICATION_AGGREGATION_MAX_WAIT_SECONDS=max_wait,
    )


def test_compute_run_at_uses_sliding_window() -> None:
    """Ensure a fresh batch runs one window from now."""
    now = datetime(2026, 6, 14, 12, 0, 0, tzinfo=UTC)
    run_at = sched._compute_run_at(now, now, _settings(120, 600))
    assert run_at == now + timedelta(seconds=120)


def test_compute_run_at_clamps_to_max_wait() -> None:
    """Ensure long editing is bounded by the max-wait cap."""
    now = datetime(2026, 6, 14, 12, 0, 0, tzinfo=UTC)
    since = now - timedelta(seconds=550)
    run_at = sched._compute_run_at(now, since, _settings(120, 600))
    assert run_at == since + timedelta(seconds=600)


def test_compute_run_at_never_in_the_past() -> None:
    """Ensure an exhausted max-wait flushes immediately, not earlier."""
    now = datetime(2026, 6, 14, 12, 0, 0, tzinfo=UTC)
    since = now - timedelta(seconds=900)
    run_at = sched._compute_run_at(now, since, _settings(120, 600))
    assert run_at == now
