"""Database engine, session factory, and ORM base for the application."""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


def _make_engine_url(raw_url: str) -> str:
    """
    Inject the psycopg dialect modifier into a standard PostgreSQL DSN.

    :param raw_url: Plain postgresql:// DSN from the environment.
    :returns: URL with +psycopg modifier for SQLAlchemy.
    """
    return raw_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )


engine = create_engine(
    _make_engine_url(str(get_settings().DATABASE_URL)),
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for the duration of a request.

    Always closed in finally, whether or not an exception occurs.

    :returns: SQLAlchemy Session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
