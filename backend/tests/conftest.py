"""Shared pytest fixtures for the MeepleTime backend test suite.

Environment bootstrapping
--------------------------
These variables are given safe defaults below so that app module
imports (which call ``get_settings()`` at load time) succeed in
environments without a real database.  The overrides are applied
via ``os.environ.setdefault``, meaning actual shell variables and
the project ``.env`` file take precedence.

For the in-memory SQLite test engine the ``DATABASE_URL`` default
is intentionally set to a placeholder; the real DB is never used
because ``get_db`` is overridden in the ``client`` fixture.
"""

from __future__ import annotations

import os

# ------------------------------------------------------------------ #
# Environment defaults — must be set BEFORE any app module is        #
# imported so that the module-level create_engine() call succeeds.   #
# ------------------------------------------------------------------ #
os.environ.setdefault(
    "MEEPLETIME_DATABASE_URL",
    "postgresql://meepletime:meepletime@localhost:5432/meepletime_test",
)
os.environ.setdefault(
    "MEEPLETIME_OIDC_AUTHORITY",
    "https://keycloak.test/realms/meepletime",
)
os.environ.setdefault(
    "MEEPLETIME_OIDC_AUDIENCE",
    "meepletime-backend",
)
os.environ.setdefault(
    "MEEPLETIME_OIDC_ISSUER",
    "https://keycloak.test/realms/meepletime",
)
os.environ.setdefault(
    "MEEPLETIME_DEV_SHARED_SECRET",
    "test-secret-with-at-least-thirty-two-chars!",
)

# ------------------------------------------------------------------ #
# Standard imports — after env bootstrap                             #
# ------------------------------------------------------------------ #
from collections.abc import Generator  # noqa: E402
from datetime import UTC, datetime, timedelta  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from typing import cast  # noqa: E402

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.config import Settings, get_settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import create_app  # noqa: E402

# ------------------------------------------------------------------ #
# Constants                                                           #
# ------------------------------------------------------------------ #
_TEST_SECRET = "test-secret-with-at-least-thirty-two-chars!"
_TEST_AUDIENCE = "meepletime-backend"
_TEST_ISSUER = "https://keycloak.test/realms/meepletime"


def _make_test_settings() -> Settings:
    """Return minimal Settings suitable for unit/integration tests."""
    return cast(
        Settings,
        SimpleNamespace(
            DATABASE_URL=(
                "postgresql://meepletime:meepletime"
                "@localhost:5432/meepletime_test"
            ),
            DEV_SHARED_SECRET=_TEST_SECRET,
            OIDC_AUDIENCE=_TEST_AUDIENCE,
            OIDC_ISSUER=_TEST_ISSUER,
            OIDC_AUTHORITY=_TEST_ISSUER,
            NOTIFICATION_DEBOUNCE_SECONDS=60,
            FRONTEND_URL="http://localhost:5173",
            CORS_ORIGINS=["http://localhost:5173"],
            INVITE_REGEN_LIMIT=3,
            INVITE_REGEN_WINDOW_SECONDS=60,
        ),
    )


# ------------------------------------------------------------------ #
# Database fixtures                                                   #
# ------------------------------------------------------------------ #


@pytest.fixture(scope="session")
def test_engine():
    """Create a shared in-memory SQLite engine with the full schema.

    Uses ``Base.metadata.create_all`` (ORM model definitions) so
    no migration tooling is needed for tests.  PostgreSQL-specific
    column types degrade gracefully to their SQLite equivalents
    (VARCHAR for UUID, TEXT for JSON).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """Yield a session that rolls back all changes after each test.

    A savepoint is used so that the schema is not recreated between
    tests, keeping the fixture fast.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection, autoflush=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ------------------------------------------------------------------ #
# Token helpers                                                       #
# ------------------------------------------------------------------ #


def _make_token(
    sub: str = "test-subject-001",
    email: str = "test@example.com",
    name: str = "Test User",
    **extra: object,
) -> str:
    """Return a signed HS256 dev JWT suitable for test requests."""
    now = datetime.now(tz=UTC)
    payload: dict[str, object] = {
        "sub": sub,
        "aud": _TEST_AUDIENCE,
        "iss": _TEST_ISSUER,
        "email": email,
        "name": name,
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    payload.update(extra)
    return jwt.encode(payload, _TEST_SECRET, algorithm="HS256")


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Return Authorization headers for the default test identity."""
    return {"Authorization": f"Bearer {_make_token()}"}


@pytest.fixture()
def token_factory():
    """Expose ``_make_token`` to tests that need custom identities.

    Usage::

        def test_something(client, token_factory):
            headers = {
                "Authorization": (
                    f"Bearer {token_factory(sub='other', email='x@y.z')}"
                )
            }
    """
    return _make_token


# ------------------------------------------------------------------ #
# Application fixture                                                 #
# ------------------------------------------------------------------ #


@pytest.fixture()
def client(
    db_session: Session,
) -> Generator[TestClient, None, None]:
    """Yield a TestClient with overridden DB session and settings.

    No real database or Keycloak instance is required.
    """
    test_settings = _make_test_settings()
    app = create_app()

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
