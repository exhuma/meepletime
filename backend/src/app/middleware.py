"""HTTP middleware for security headers and request logging."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging_utils import clear_correlation_id, set_correlation_id

LOG = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related HTTP headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with its duration and a correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming_id = request.headers.get("X-Correlation-ID")
        correlation_id = incoming_id or str(uuid.uuid4())
        client_host = request.client.host if request.client else "unknown"
        start = time.monotonic()
        set_correlation_id(correlation_id)
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.monotonic() - start) * 1000
            LOG.exception(
                "%s %s from %s failed after %.1f ms",
                request.method,
                request.url.path,
                client_host,
                duration_ms,
            )
            raise
        finally:
            if "response" not in locals():
                clear_correlation_id()

        duration_ms = (time.monotonic() - start) * 1000
        LOG.info(
            "%s %s from %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            client_host,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Correlation-ID"] = correlation_id
        clear_correlation_id()
        return response
