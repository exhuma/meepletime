"""Application entry point: creates the FastAPI app via factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    VersionHeaderMiddleware,
)

LOG = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Build and return the configured FastAPI application.

    Registers routers, middleware, and the lifespan handler.
    No router, middleware, or exception handler is registered
    outside this factory.

    :returns: Fully configured FastAPI application instance.
    """

    @asynccontextmanager
    async def lifespan(
        _app: FastAPI,
    ) -> AsyncGenerator[None, None]:
        """Start and stop background services with the app lifecycle."""
        from app.services.notifications import (
            shutdown_scheduler,
            start_scheduler,
        )

        start_scheduler()
        yield
        shutdown_scheduler()

    settings = get_settings()

    app = FastAPI(
        title="MeepleTime API",
        description=(
            "Backend API for the MeepleTime meeting availability application"
        ),
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # Middleware is applied LIFO: last registered runs first on
    # requests.  CORS must be outermost to catch preflight OPTIONS
    # before auth; security headers and logging are inner layers.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(VersionHeaderMiddleware, version=settings.VERSION)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["DELETE", "GET", "PATCH", "POST", "PUT"],
        allow_headers=["Authorization", "Content-Type"],
    )

    from app.routers import (
        auth,
        availability,
        circle_telegram,
        circles,
        day_notes,
        host_day_constraints,
        memberships,
        notifications,
        onboarding,
        users,
        viability,
    )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(circles.router)
    app.include_router(memberships.router)
    app.include_router(availability.router)
    app.include_router(viability.router)
    app.include_router(host_day_constraints.router)
    app.include_router(day_notes.router)
    app.include_router(notifications.router)
    app.include_router(circle_telegram.router)
    app.include_router(onboarding.router)

    if settings.DEV_AUTH_ENABLED:
        # Dev-only: in-app login without Keycloak. The router is not
        # imported or mounted otherwise, so /auth/dev/* is a plain
        # 404 in production. See app.routers.auth_dev.
        from app.routers import auth_dev

        app.include_router(auth_dev.router)
        LOG.warning(
            "DEV AUTH ENABLED: /auth/dev/* mounted. "
            "Never enable MEEPLETIME_DEV_AUTH_ENABLED in production."
        )

    @app.get("/health")
    def health_check(
        db: Session = Depends(get_db),
    ) -> JSONResponse:
        """
        Return service health status.

        Checks database connectivity. Returns HTTP 503 when any
        dependency is unavailable.

        :param db: Session used for the DB connectivity probe.
        :returns: JSON response with ``status`` key.
        """
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:
            LOG.error("Health check: database unavailable: %s", exc)
            return JSONResponse(
                status_code=503,
                content={"status": "error", "detail": "database"},
            )
        return JSONResponse(content={"status": "ok"})

    return app


app = create_app()
