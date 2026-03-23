"""Application entry point: creates the FastAPI app via factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


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
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.FRONTEND_URL,
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import (
        auth,
        availability,
        circles,
        day_notes,
        day_overrides,
        memberships,
        viability,
    )

    app.include_router(auth.router)
    app.include_router(circles.router)
    app.include_router(memberships.router)
    app.include_router(availability.router)
    app.include_router(viability.router)
    app.include_router(day_overrides.router)
    app.include_router(day_notes.router)

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """
        Return service health status.

        :returns: JSON object with ``status`` key.
        """
        return {"status": "ok"}

    return app


app = create_app()
