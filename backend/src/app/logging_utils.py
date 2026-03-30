"""Logging helpers shared by app code and uvicorn log config."""

from __future__ import annotations

import logging
from contextvars import ContextVar

from gouge.colourcli import Simple, clr
from gouge.preformatters import uvicorn_access

_correlation_id: ContextVar[str] = ContextVar(
    "correlation_id",
    default="-",
)


def set_correlation_id(value: str) -> None:
    """Store the current request correlation ID in a context variable."""
    _correlation_id.set(value)


def clear_correlation_id() -> None:
    """Reset the current request correlation ID to its empty marker."""
    _correlation_id.set("-")


def get_correlation_id() -> str:
    """Return the correlation ID for the current execution context."""
    return _correlation_id.get()


class CorrelationIdFilter(logging.Filter):
    """Inject the current correlation ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True


class MeepleFormatter(Simple):
    """Gouge formatter extended with request correlation IDs."""

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        correlation_id = getattr(record, "correlation_id", "-")
        if correlation_id == "-":
            return rendered
        return (
            f"{rendered} {clr.Style.DIM}[cid={correlation_id}]"
            f"{clr.Style.RESET_ALL}"
        )


def build_dev_formatter() -> MeepleFormatter:
    """Return the development console formatter for dictConfig/YAML."""
    clr.init(strip=None)
    return MeepleFormatter(
        show_exc=True,
        pre_formatters={"uvicorn.access": [uvicorn_access]},
    )


def build_prod_formatter() -> MeepleFormatter:
    """Return the production console formatter for dictConfig/YAML."""
    clr.init(strip=None)
    return MeepleFormatter(
        show_exc=True,
        pre_formatters={"uvicorn.access": [uvicorn_access]},
    )
