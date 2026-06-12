"""Invite PIN generation and normalization service.

Invite codes are short, human-typable PINs rather than UUIDs. The
alphabet is an unambiguous base32 set (Crockford-style) that omits the
visually confusable characters ``0 O 1 I L``.
"""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.circle import Circle

# Unambiguous uppercase base32 alphabet (no 0, O, 1, I, L).
INVITE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
INVITE_LENGTH = 6
_MAX_GENERATION_ATTEMPTS = 10


def generate_pin() -> str:
    """Return a fresh random invite PIN (no uniqueness guarantee)."""
    return "".join(
        secrets.choice(INVITE_ALPHABET) for _ in range(INVITE_LENGTH)
    )


def generate_unique_pin(db: Session) -> str:
    """
    Return an invite PIN not currently used by any circle.

    Retries a bounded number of times against the database. The unique
    constraint on ``circles.invite_token`` remains the hard backstop.

    :raises RuntimeError: If no free PIN was found within the attempt
        budget (astronomically unlikely for the configured key space).
    """
    for _ in range(_MAX_GENERATION_ATTEMPTS):
        pin = generate_pin()
        taken = db.execute(
            select(Circle.id).where(Circle.invite_token == pin)
        ).first()
        if taken is None:
            return pin
    raise RuntimeError("Could not generate a unique invite PIN")


def normalize_pin(raw: str) -> str:
    """Canonicalize user-supplied PIN input (strip separators, upper)."""
    return raw.replace(" ", "").replace("-", "").strip().upper()


def is_valid_pin(value: str) -> bool:
    """Return True if *value* is a well-formed, in-alphabet PIN."""
    return len(value) == INVITE_LENGTH and all(
        ch in INVITE_ALPHABET for ch in value
    )
