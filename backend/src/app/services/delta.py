"""Quill Delta validation and plain-text rendering.

Day descriptions store a Quill *Delta* document as the canonical
representation. HTML is never stored or trusted — it is derived on the
client at render time. This module validates an incoming Delta's
structure on ingress against a strict allowlist (matching the editor
toolbar) and renders a Delta to plain text for email notifications.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Bounds on a single description document. Generous for session detail
# while preventing unbounded payloads.
MAX_OPS = 400
MAX_TEXT_LENGTH = 16_000

# Inline/line formats permitted, matching the editor toolbar. Anything
# outside this set is rejected so stored Deltas render to a small,
# predictable, email-safe HTML subset on the client.
_BOOL_ATTRS = {"bold", "italic", "underline"}
_ALLOWED_HEADERS = {3, 4}
_ALLOWED_LISTS = {"ordered", "bullet"}
_SAFE_LINK_SCHEMES = ("http://", "https://", "mailto:")
_MAX_LINK_LENGTH = 2048


def _validate_attributes(value: dict[str, Any]) -> dict[str, Any]:
    """Reject any attribute outside the editor's allowlist."""
    for key, val in value.items():
        if key in _BOOL_ATTRS:
            if not isinstance(val, bool):
                raise ValueError(f"{key} must be a boolean")
        elif key == "link":
            if not isinstance(val, str) or len(val) > _MAX_LINK_LENGTH:
                raise ValueError("link must be a short string")
            if not val.startswith(_SAFE_LINK_SCHEMES):
                raise ValueError("link scheme not allowed")
        elif key == "header":
            if val not in _ALLOWED_HEADERS:
                raise ValueError("header must be 3 or 4")
        elif key == "list":
            if val not in _ALLOWED_LISTS:
                raise ValueError("list must be 'ordered' or 'bullet'")
        else:
            raise ValueError(f"disallowed attribute: {key}")
    return value


class DeltaOp(BaseModel):
    """One Quill Delta operation.

    Only text inserts are accepted; embed objects (images, video) are
    rejected by typing ``insert`` as ``str``.
    """

    model_config = ConfigDict(extra="forbid")

    insert: str
    attributes: dict[str, Any] | None = None

    @field_validator("attributes")
    @classmethod
    def _check_attributes(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return value
        return _validate_attributes(value)


class DeltaDoc(BaseModel):
    """A validated Quill Delta document."""

    model_config = ConfigDict(extra="forbid")

    ops: list[DeltaOp] = Field(min_length=1, max_length=MAX_OPS)

    @field_validator("ops")
    @classmethod
    def _check_total_length(cls, ops: list[DeltaOp]) -> list[DeltaOp]:
        total = sum(len(op.insert) for op in ops)
        if total > MAX_TEXT_LENGTH:
            raise ValueError("description is too long")
        return ops


def delta_to_text(content_delta: dict[str, Any]) -> str:
    """Render a stored Delta document to plain text.

    Concatenates the text of every op (Quill inserts already carry
    their own newlines) and trims surrounding whitespace. Used for the
    plain-text body folded into viability emails.
    """
    ops = content_delta.get("ops", [])
    parts = [
        op["insert"]
        for op in ops
        if isinstance(op, dict) and isinstance(op.get("insert"), str)
    ]
    return "".join(parts).strip()
