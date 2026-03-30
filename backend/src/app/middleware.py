"""HTTP middleware for security headers and request logging."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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
        correlation_id = str(uuid.uuid4())
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        LOG.info(
            "%s %s → %d (%.1f ms) cid=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            correlation_id,
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response
