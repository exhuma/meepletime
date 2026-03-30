"""Rate limiting helpers powered by the ``limits`` library."""

from __future__ import annotations

from dataclasses import dataclass
from time import time

from fastapi import HTTPException, status
from limits import RateLimitItemPerSecond
from limits.storage import storage_from_string
from limits.strategies import MovingWindowRateLimiter


@dataclass(frozen=True)
class RateLimitResult:
    """Result of a single rate-limit check."""

    allowed: bool
    remaining: int
    reset_seconds: int


_storage = storage_from_string("memory://")
_limiter = MovingWindowRateLimiter(_storage)


def _check_limit(
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> RateLimitResult:
    """Evaluate whether *key* may perform one more action now."""
    item = RateLimitItemPerSecond(limit, window_seconds)
    allowed = _limiter.hit(item, key)
    stats = _limiter.get_window_stats(item, key)
    reset_seconds = max(1, int(stats.reset_time - time()))
    return RateLimitResult(
        allowed=allowed,
        remaining=max(0, stats.remaining),
        reset_seconds=reset_seconds,
    )


def enforce_limit_or_429(
    *,
    key: str,
    limit: int,
    window_seconds: int,
    scope: str,
) -> None:
    """
    Enforce a rate limit or raise HTTP 429 with standard headers.

    :param key: Stable key for throttling (for example user+IP).
    :param limit: Allowed requests per window.
    :param window_seconds: Window size in seconds.
    :param scope: Human-readable action name for error detail.
    :raises HTTPException: 429 when the limit is exceeded.
    """
    result = _check_limit(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
    )
    if result.allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded for {scope}",
        headers={
            "RateLimit-Limit": str(limit),
            "RateLimit-Remaining": str(result.remaining),
            "RateLimit-Reset": str(result.reset_seconds),
            "Retry-After": str(result.reset_seconds),
        },
    )
