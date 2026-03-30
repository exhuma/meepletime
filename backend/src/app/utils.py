"""Shared utility helpers for the application."""

from __future__ import annotations

from typing import Any


def apply_partial_update(instance: Any, data: dict[str, Any]) -> None:
    """
    Apply a partial-update mapping to a SQLAlchemy model instance.

    Sets each key in *data* as an attribute on *instance*. Only call
    with fields already validated by the Pydantic schema layer.

    :param instance: SQLAlchemy model instance to update.
    :param data: Field names mapped to their new values.
    """
    for field, value in data.items():
        setattr(instance, field, value)
