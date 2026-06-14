# Notification Email with Confirmation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user set a dedicated notification email that is verified by a 24h confirmation link (with retry), falling back to the profile email when none is confirmed and email notifications are enabled.

**Architecture:** A confirmed address lives on `UserNotificationSettings.notification_email`; transient pending state (opaque token, pending email, expiry) lives in a new 1-row-per-user `EmailConfirmation` table. New `/notifications/email*` endpoints drive set/resend/confirm/clear. The email dispatch layer resolves `notification_email or user.email`. A public SPA route confirms the code.

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest (SQLite); Vue 3 `<script setup>`, Vuetify 3, vue-router, Vite.

**Spec:** `docs/superpowers/specs/2026-06-14-notification-email-confirmation-design.md`

**Project rules (non-negotiable):** 80-char line limit on all files. Backend: `cd backend && uv run ...`. Ruff `E,W,F,I,UP`. Add an Alembic migration for every model change. Every public function gets a docstring with `:param:`/`:returns:` (match existing style). Frontend is `<script setup lang="ts">` only.

**Instruction kits:** Before coding backend tasks, load the FastAPI / SQLAlchemy / Alembic / Postgres / code-style kits via the `instructions-exhuma` MCP (`select_kits` with traits `python, fastapi, sqlalchemy, alembic, postgresql, rest-api, code-style, backend`); before frontend tasks load the Vue / Vuetify kits (`typescript, vue, vuetify, web-ui, frontend`). Their rules override this plan where stricter.

---

## File Structure

**Backend**

- Modify `backend/src/app/config.py` — add `EMAIL_CONFIRMATION_TTL_HOURS`.
- Modify `backend/src/app/models/notification_settings.py` — add `notification_email` column + `EmailConfirmation` model.
- Modify `backend/src/app/models/__init__.py` — export `EmailConfirmation`.
- Create `backend/alembic/versions/0009_email_confirmation.py` — migration.
- Create `backend/src/app/services/email.py` — generic SMTP send helper.
- Modify `backend/src/app/services/notifications/channels/email.py` — reuse the helper (DRY).
- Create `backend/src/app/services/email_confirmation.py` — start/resend/confirm/clear logic.
- Modify `backend/src/app/schemas/notification_settings.py` — extended settings out + email schemas.
- Modify `backend/src/app/routers/notifications.py` — new endpoints + extended settings response.
- Modify `backend/src/app/services/notifications/dispatch.py` — effective-email resolution.
- Create `backend/tests/test_notification_email.py` — confirmation flow tests.
- Modify `backend/tests/test_notification_settings.py` — extended GET shape.
- Modify `backend/tests/test_notifications_dispatch.py` — resolution test (append).

**Frontend**

- Modify `frontend/src/types.ts` — extended `NotificationSettings` + `EmailConfirmResult`.
- Modify `frontend/src/composables/useNotificationSettings.ts` — new actions.
- Modify `frontend/src/views/ProfileSettingsView.vue` — notification-email field/UI.
- Create `frontend/src/views/ConfirmEmailView.vue` — public confirmation page.
- Modify `frontend/src/router/index.ts` — public `/confirm-email` route.

**Docs**

- Modify `docs/operator/notifications.md` and `docs/user/notifications.md`.

---

## Task 1: Config — confirmation TTL setting

**Files:**

- Modify: `backend/src/app/config.py`

- [ ] **Step 1: Add the setting**

In the `Settings` class body, immediately after the line `NOTIFICATION_DEBOUNCE_SECONDS: int = 10`, add:

```python
    EMAIL_CONFIRMATION_TTL_HOURS: int = 24
```

And in the class docstring `:param:` block (near the SMTP params), add a line:

```python
    :param EMAIL_CONFIRMATION_TTL_HOURS: Validity window, in hours,
        for a notification-email confirmation link.
```

- [ ] **Step 2: Verify import still works**

Run: `cd backend && uv run python -c "from app.config import Settings; print(Settings.model_fields['EMAIL_CONFIRMATION_TTL_HOURS'].default)"`
Expected: `24`

- [ ] **Step 3: Commit**

```bash
git add backend/src/app/config.py
git commit -m "feat: add EMAIL_CONFIRMATION_TTL_HOURS setting"
```

---

## Task 2: Model — notification_email column + EmailConfirmation

**Files:**

- Modify: `backend/src/app/models/notification_settings.py`
- Modify: `backend/src/app/models/__init__.py`

- [ ] **Step 1: Add the confirmed-address column**

In `notification_settings.py`, inside `UserNotificationSettings`, add this column right after the `telegram_dm_enabled` column definition:

```python
    notification_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
```

- [ ] **Step 2: Add the EmailConfirmation model**

At the end of `notification_settings.py` (after `TelegramMemberLink`), add:

```python
class EmailConfirmation(Base):
    """
    A pending notification-email confirmation for one user.

    At most one row per user (``unique(user_id)``). Holds the opaque
    confirmation ``token`` (re-sent verbatim on retry), the address
    awaiting confirmation, and the expiry deadline. The row is deleted
    when the address is confirmed or cleared.
    """

    __tablename__ = "email_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    pending_email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
```

- [ ] **Step 3: Export the model**

In `models/__init__.py`, extend the existing
`from app.models.notification_settings import (...)` block to include
`EmailConfirmation` (keep alphabetical with the others), and add
`"EmailConfirmation",` to the `__all__` list.

- [ ] **Step 4: Verify metadata registers the table**

Run: `cd backend && uv run python -c "import app.models; from app.database import Base; print('email_confirmations' in Base.metadata.tables)"`
Expected: `True`

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/models/notification_settings.py backend/src/app/models/__init__.py
git commit -m "feat: add notification_email column and EmailConfirmation model"
```

---

## Task 3: Alembic migration

**Files:**

- Create: `backend/alembic/versions/0009_email_confirmation.py`

- [ ] **Step 1: Write the migration**

```python
"""Add notification_email column and email_confirmations table.

Revision ID: 0009_email_confirmation
Revises: 0008_onboarding_state
Create Date: 2026-06-14 00:00:00.000000

Adds the confirmed notification address on user_notification_settings
and a one-row-per-user table holding the pending confirmation token,
the address awaiting confirmation, and its expiry.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_email_confirmation"
down_revision: str | None = "0008_onboarding_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the column and the email_confirmations table."""
    op.add_column(
        "user_notification_settings",
        sa.Column("notification_email", sa.String(length=255), nullable=True),
    )
    op.create_table(
        "email_confirmations",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pending_email", sa.String(length=255), nullable=False
        ),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column(
            "expires_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
    )
    op.create_index(
        "ix_email_confirmations_user_id",
        "email_confirmations",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_email_confirmations_token",
        "email_confirmations",
        ["token"],
    )


def downgrade() -> None:
    """Drop the table and the column."""
    op.drop_index(
        "ix_email_confirmations_token", table_name="email_confirmations"
    )
    op.drop_index(
        "ix_email_confirmations_user_id", table_name="email_confirmations"
    )
    op.drop_table("email_confirmations")
    op.drop_column("user_notification_settings", "notification_email")
```

- [ ] **Step 2: Verify the migration chain is consistent**

Run: `cd backend && uv run alembic heads`
Expected: a single head `0009_email_confirmation`.

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/0009_email_confirmation.py
git commit -m "feat: migration for notification email confirmation"
```

---

## Task 4: Generic SMTP send helper (with DRY refactor of the email channel)

**Files:**

- Create: `backend/src/app/services/email.py`
- Modify: `backend/src/app/services/notifications/channels/email.py`

- [ ] **Step 1: Write the helper module**

```python
"""Low-level SMTP send helper shared by notification + confirmation mail.

Uses the standard-library synchronous SMTP client with a hard timeout
so it is safe to call from a request thread or the scheduler worker.
Delivery is inert (``is_smtp_configured`` is ``False``) when SMTP host
and from-address are not configured.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import get_settings

# Hard network timeout for SMTP operations, in seconds.
SMTP_TIMEOUT = 5


def is_smtp_configured() -> bool:
    """
    Return whether SMTP delivery is configured.

    :returns: ``True`` when both host and from-address are set.
    """
    settings = get_settings()
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_email(to: str, subject: str, body: str) -> None:
    """
    Send one plain-text email over SMTP.

    :param to: Recipient address.
    :param subject: Message subject.
    :param body: Plain-text message body.
    :raises OSError: On connection or SMTP transport failure.
    """
    settings = get_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message.set_content(body)

    with smtplib.SMTP(
        settings.SMTP_HOST, settings.SMTP_PORT, timeout=SMTP_TIMEOUT
    ) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
```

- [ ] **Step 2: Refactor the notification email channel to reuse it**

In `channels/email.py`, replace the `import smtplib` / `from email.message import EmailMessage` imports and the `_SMTP_TIMEOUT` constant with:

```python
from app.services.email import is_smtp_configured, send_email
```

Change `_is_configured` to delegate:

```python
    def _is_configured(self) -> bool:
        """
        Return whether SMTP delivery is configured.

        :returns: ``True`` when host and from-address are set.
        """
        return is_smtp_configured()
```

Replace the body of `send` (the `EmailMessage`/`smtplib.SMTP` block) with:

```python
        send_email(
            target.address,
            ctx.title,
            f"{ctx.body}\n\n{ctx.url}\n",
        )
```

Remove the now-unused `get_settings` import in `channels/email.py` if it is no longer referenced (check the file — `send` no longer reads settings directly).

- [ ] **Step 3: Verify nothing broke in the channel**

Run: `cd backend && uv run pytest tests/test_notification_test_delivery.py -q`
Expected: PASS (channel still constructs/sends as before).

- [ ] **Step 4: Commit**

```bash
git add backend/src/app/services/email.py backend/src/app/services/notifications/channels/email.py
git commit -m "refactor: extract shared SMTP send helper"
```

---

## Task 5: Confirmation service

**Files:**

- Create: `backend/src/app/services/email_confirmation.py`

- [ ] **Step 1: Write the service**

```python
"""Service layer for notification-email confirmation.

Drives the set / retry / confirm / clear lifecycle of a user's
notification email. A confirmed address lands on
``UserNotificationSettings.notification_email``; the transient pending
state lives in :class:`EmailConfirmation` (at most one row per user).
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.notification_settings import EmailConfirmation
from app.services.email import send_email
from app.services.notification_settings import get_or_create_settings

# Entropy for the opaque confirmation token, in bytes.
_TOKEN_BYTES = 32
# Minimum seconds between confirmation sends (retry throttle).
RESEND_COOLDOWN_SECONDS = 60


class ConfirmStatus(str, Enum):
    """Outcome of a confirmation-code submission."""

    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    INVALID = "invalid"


class NoPendingConfirmation(Exception):
    """Raised when a resend is requested but nothing is pending."""


class ResendTooSoon(Exception):
    """Raised when a resend is requested inside the cooldown window."""


def _now() -> datetime:
    """:returns: The current UTC time."""
    return datetime.now(UTC)


def _ttl() -> timedelta:
    """:returns: The configured confirmation validity window."""
    return timedelta(hours=get_settings().EMAIL_CONFIRMATION_TTL_HOURS)


def get_pending(
    db: Session, user_id: uuid.UUID
) -> EmailConfirmation | None:
    """
    Return the user's pending confirmation row, if any.

    :param db: Active database session.
    :param user_id: The owning user.
    :returns: The pending row, or ``None``.
    """
    return db.execute(
        select(EmailConfirmation).where(
            EmailConfirmation.user_id == user_id
        )
    ).scalar_one_or_none()


def _confirmation_body(token: str) -> str:
    """
    Return the plain-text confirmation email body.

    :param token: The opaque confirmation token to embed.
    :returns: The message body including the confirmation link.
    """
    base = get_settings().APP_BASE_URL.rstrip("/")
    hours = get_settings().EMAIL_CONFIRMATION_TTL_HOURS
    link = f"{base}/confirm-email?code={token}"
    return (
        "Confirm this address to receive MeepleTime notifications "
        "here.\n\n"
        f"{link}\n\n"
        f"This link is valid for {hours} hours. If you did not request "
        "this, you can ignore this email.\n"
    )


def _send(row: EmailConfirmation) -> None:
    """
    Send the confirmation email for a pending row.

    :param row: The pending confirmation row.
    :raises OSError: On SMTP transport failure.
    """
    send_email(
        row.pending_email,
        "Confirm your MeepleTime notification email",
        _confirmation_body(row.token),
    )


def start_confirmation(
    db: Session, user_id: uuid.UUID, email: str
) -> EmailConfirmation:
    """
    Begin confirming a new notification address (new token, fresh TTL).

    Replaces any existing pending row for the user. Does **not** touch
    the currently confirmed address, which keeps receiving mail until
    the new one is confirmed.

    :param db: Active database session.
    :param user_id: The requesting user.
    :param email: The address to confirm.
    :returns: The persisted pending row.
    :raises OSError: On SMTP transport failure.
    """
    row = get_pending(db, user_id)
    if row is None:
        row = EmailConfirmation(user_id=user_id)
        db.add(row)
    row.pending_email = email
    row.token = secrets.token_urlsafe(_TOKEN_BYTES)
    row.expires_at = _now() + _ttl()
    row.created_at = _now()
    db.flush()
    _send(row)
    db.commit()
    db.refresh(row)
    return row


def resend_confirmation(
    db: Session, user_id: uuid.UUID
) -> EmailConfirmation:
    """
    Resend the *same* pending link with a refreshed deadline.

    :param db: Active database session.
    :param user_id: The requesting user.
    :returns: The refreshed pending row.
    :raises NoPendingConfirmation: When nothing is pending.
    :raises ResendTooSoon: When inside the cooldown window.
    :raises OSError: On SMTP transport failure.
    """
    row = get_pending(db, user_id)
    if row is None:
        raise NoPendingConfirmation
    last_send = row.expires_at - _ttl()
    if (_now() - last_send).total_seconds() < RESEND_COOLDOWN_SECONDS:
        raise ResendTooSoon
    row.expires_at = _now() + _ttl()
    db.flush()
    _send(row)
    db.commit()
    db.refresh(row)
    return row


def confirm(db: Session, code: str) -> ConfirmStatus:
    """
    Confirm a code: promote the pending address and consume the row.

    :param db: Active database session.
    :param code: The token from the confirmation link.
    :returns: The confirmation outcome.
    """
    row = db.execute(
        select(EmailConfirmation).where(EmailConfirmation.token == code)
    ).scalar_one_or_none()
    if row is None:
        return ConfirmStatus.INVALID
    if row.expires_at <= _now():
        return ConfirmStatus.EXPIRED
    settings = get_or_create_settings(db, row.user_id)
    settings.notification_email = row.pending_email
    db.delete(row)
    db.commit()
    return ConfirmStatus.CONFIRMED


def clear_email(db: Session, user_id: uuid.UUID) -> None:
    """
    Clear the confirmed address and any pending confirmation.

    :param db: Active database session.
    :param user_id: The requesting user.
    """
    settings = get_or_create_settings(db, user_id)
    settings.notification_email = None
    row = get_pending(db, user_id)
    if row is not None:
        db.delete(row)
    db.commit()
```

- [ ] **Step 2: Verify it imports**

Run: `cd backend && uv run python -c "import app.services.email_confirmation as m; print(m.ConfirmStatus.CONFIRMED.value)"`
Expected: `confirmed`

- [ ] **Step 3: Commit**

```bash
git add backend/src/app/services/email_confirmation.py
git commit -m "feat: notification-email confirmation service"
```

---

## Task 6: Schemas

**Files:**

- Modify: `backend/src/app/schemas/notification_settings.py`

- [ ] **Step 1: Add the import and email schemas**

At the top, change the imports to include `datetime` and `EmailStr`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr
```

- [ ] **Step 2: Extend `NotificationSettingsOut`**

Add three fields to `NotificationSettingsOut` (after the existing flags):

```python
    notification_email: str | None = None
    pending_email: str | None = None
    pending_expires_at: datetime | None = None
```

(The router builds this object explicitly, so `from_attributes` is not relied on for the pending fields.)

- [ ] **Step 3: Add the request/response schemas**

Append at the end of the file:

```python
EmailConfirmStatusValue = Literal["confirmed", "expired", "invalid"]


class NotificationEmailIn(BaseModel):
    """Request to start confirming a notification address."""

    email: EmailStr


class EmailConfirmIn(BaseModel):
    """A confirmation code submitted from the email link."""

    code: str


class EmailConfirmOut(BaseModel):
    """Outcome of submitting a confirmation code."""

    status: EmailConfirmStatusValue
    email: str | None = None
```

- [ ] **Step 4: Verify it imports**

Run: `cd backend && uv run python -c "from app.schemas.notification_settings import NotificationEmailIn, EmailConfirmOut; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/schemas/notification_settings.py
git commit -m "feat: schemas for notification email confirmation"
```

---

## Task 7: Router endpoints + extended settings response

**Files:**

- Modify: `backend/src/app/routers/notifications.py`

- [ ] **Step 1: Add imports**

Add to the imports at the top of `notifications.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.notification_settings import EmailConfirmation
from app.schemas.notification_settings import (
    EmailConfirmIn,
    EmailConfirmOut,
    NotificationEmailIn,
    NotificationSettingsOut,
    NotificationSettingsUpdate,
    NotificationTestIn,
    NotificationTestOut,
    WebPushKeyOut,
    WebPushSubscriptionIn,
)
from app.services.email import is_smtp_configured
from app.services.email_confirmation import (
    ConfirmStatus,
    NoPendingConfirmation,
    ResendTooSoon,
    clear_email,
    confirm,
    get_pending,
    resend_confirmation,
    start_confirmation,
)
```

(Merge with the existing import lines; do not duplicate `APIRouter`/`Depends`/`status` or the settings-service imports.)

- [ ] **Step 2: Add a response builder helper**

Above `read_settings`, add:

```python
def _settings_response(
    db: Session, current_user: User
) -> NotificationSettingsOut:
    """
    Build the settings response, including any pending confirmation.

    :param db: Database session.
    :param current_user: Authenticated user.
    :returns: The caller's settings plus pending-confirmation state.
    """
    settings = get_or_create_settings(db, current_user.id)
    pending = get_pending(db, current_user.id)
    return NotificationSettingsOut(
        email_enabled=settings.email_enabled,
        webpush_enabled=settings.webpush_enabled,
        telegram_dm_enabled=settings.telegram_dm_enabled,
        notification_email=settings.notification_email,
        pending_email=pending.pending_email if pending else None,
        pending_expires_at=pending.expires_at if pending else None,
    )
```

- [ ] **Step 3: Use the helper in the existing GET/PUT handlers**

Replace the body of `read_settings` return with:

```python
    return _settings_response(db, current_user)
```

In `write_settings`, after the `update_settings(...)` call, replace the
`return NotificationSettingsOut.model_validate(settings)` line with:

```python
    return _settings_response(db, current_user)
```

- [ ] **Step 4: Add the email endpoints**

After `write_settings` (before the webpush handlers), add:

```python
@router.post("/email", response_model=NotificationSettingsOut)
def set_notification_email(
    payload: NotificationEmailIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Start confirming a new notification address and send the link.

    The previously confirmed address (if any) keeps receiving mail
    until the new one is confirmed.

    :param payload: The address to confirm.
    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated settings including the pending address.
    """
    if not is_smtp_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery isn't configured on this server.",
        )
    try:
        start_confirmation(db, current_user.id, str(payload.email))
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the confirmation email.",
        )
    return _settings_response(db, current_user)


@router.post("/email/resend", response_model=NotificationSettingsOut)
def resend_notification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Resend the pending confirmation link with a fresh deadline.

    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated settings including the pending address.
    """
    try:
        resend_confirmation(db, current_user.id)
    except NoPendingConfirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is no pending email to confirm.",
        )
    except ResendTooSoon:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait a moment before requesting another link.",
        )
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the confirmation email.",
        )
    return _settings_response(db, current_user)


@router.delete("/email", response_model=NotificationSettingsOut)
def clear_notification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsOut:
    """
    Clear the confirmed notification address and any pending one.

    :param current_user: Authenticated user.
    :param db: Database session.
    :returns: The updated settings.
    """
    clear_email(db, current_user.id)
    return _settings_response(db, current_user)


@router.post("/email/confirm", response_model=EmailConfirmOut)
def confirm_notification_email(
    payload: EmailConfirmIn,
    db: Session = Depends(get_db),
) -> EmailConfirmOut:
    """
    Confirm a notification address from an emailed code.

    Unauthenticated: the opaque token is the authority. The response
    describes only the code state and never reveals account existence.

    :param payload: The submitted confirmation code.
    :param db: Database session.
    :returns: The confirmation outcome.
    """
    pending = db.execute(
        select(EmailConfirmation).where(
            EmailConfirmation.token == payload.code
        )
    ).scalar_one_or_none()
    confirmed_email = (
        pending.pending_email if pending is not None else None
    )
    result = confirm(db, payload.code)
    return EmailConfirmOut(
        status=result.value,
        email=confirmed_email if result is ConfirmStatus.CONFIRMED else None,
    )
```

- [ ] **Step 5: Add the `select` import**

Ensure `from sqlalchemy import select` is present at the top of
`notifications.py` (the confirm handler uses it). Add it if missing.

- [ ] **Step 6: Verify the app boots and routes register**

Run: `cd backend && uv run python -c "from app.main import create_app; app = create_app(); print(sorted({r.path for r in app.routes if '/notifications/email' in getattr(r, 'path', '')}))"`
Expected includes: `/notifications/email`, `/notifications/email/confirm`, `/notifications/email/resend`

- [ ] **Step 7: Commit**

```bash
git add backend/src/app/routers/notifications.py
git commit -m "feat: notification-email endpoints"
```

---

## Task 8: Effective-email resolution in dispatch

**Files:**

- Modify: `backend/src/app/services/notifications/dispatch.py:88`

- [ ] **Step 1: Resolve confirmed-or-profile email**

In `_load_recipients`, change the `Recipient(...)` construction so the
email is the confirmed notification address when present:

```python
        recipients.append(
            Recipient(
                user_id=user.id,
                delivery_id=delivery.id,
                email=settings.notification_email or user.email,
                settings=settings,
            )
        )
```

(`settings` is already resolved a few lines above; the transient
`_default_settings` has `notification_email is None`, so it falls back
to `user.email` automatically.)

- [ ] **Step 2: Verify dispatch tests still pass**

Run: `cd backend && uv run pytest tests/test_notifications_dispatch.py -q`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/src/app/services/notifications/dispatch.py
git commit -m "feat: route notifications to confirmed email when set"
```

---

## Task 9: Backend tests — confirmation flow

**Files:**

- Create: `backend/tests/test_notification_email.py`

These tests monkeypatch the SMTP layer so no real mail is sent. They
patch `is_smtp_configured` to `True` and capture `send_email` calls at
the two modules that reference them (`app.routers.notifications` for the
config gate, `app.services.email_confirmation` for the send).

- [ ] **Step 1: Write the test module**

```python
"""Integration tests for the notification-email confirmation flow."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

import app.routers.notifications as notif_router
import app.services.email_confirmation as confirm_svc


class _Mailbox:
    """Collects (to, subject, body) tuples in place of real SMTP."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def __call__(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


@pytest.fixture()
def mailbox(monkeypatch) -> _Mailbox:
    """Patch SMTP config + send so confirmation mail is captured."""
    box = _Mailbox()
    monkeypatch.setattr(notif_router, "is_smtp_configured", lambda: True)
    monkeypatch.setattr(confirm_svc, "send_email", box)
    return box


def _code_from(body: str) -> str:
    """Extract the ``code`` query param from a confirmation body."""
    match = re.search(r"[?&]code=([^\s&]+)", body)
    assert match, f"no code in body: {body!r}"
    return match.group(1)


def test_set_email_sends_link_and_marks_pending(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Setting an address sends a link and reports it as pending."""
    res = client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["pending_email"] == "notify@example.com"
    assert body["notification_email"] is None
    assert len(mailbox.sent) == 1
    assert mailbox.sent[0][0] == "notify@example.com"


def test_confirm_promotes_address_and_consumes_code(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Confirming sets notification_email and invalidates the code."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    code = _code_from(mailbox.sent[0][2])

    res = client.post("/notifications/email/confirm", json={"code": code})
    assert res.status_code == 200
    assert res.json() == {
        "status": "confirmed",
        "email": "notify@example.com",
    }

    settings = client.get(
        "/notifications/settings", headers=auth_headers
    ).json()
    assert settings["notification_email"] == "notify@example.com"
    assert settings["pending_email"] is None

    # Code is single-use now.
    again = client.post(
        "/notifications/email/confirm", json={"code": code}
    )
    assert again.json()["status"] == "invalid"


def test_confirm_endpoint_needs_no_auth(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """The confirm endpoint works without an Authorization header."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    code = _code_from(mailbox.sent[0][2])
    res = client.post("/notifications/email/confirm", json={"code": code})
    assert res.status_code == 200
    assert res.json()["status"] == "confirmed"


def test_confirm_unknown_code_is_invalid(client: TestClient) -> None:
    """An unknown code reports 'invalid' without leaking existence."""
    res = client.post(
        "/notifications/email/confirm", json={"code": "nope"}
    )
    assert res.status_code == 200
    assert res.json() == {"status": "invalid", "email": None}


def test_expired_code_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    mailbox: _Mailbox,
    monkeypatch,
) -> None:
    """A code past its deadline reports 'expired'."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    code = _code_from(mailbox.sent[0][2])

    # Force every pending row to be already expired.
    from datetime import UTC, datetime, timedelta

    real_now = confirm_svc._now

    def _past() -> datetime:
        return real_now() + timedelta(hours=48)

    monkeypatch.setattr(confirm_svc, "_now", _past)

    res = client.post("/notifications/email/confirm", json={"code": code})
    assert res.json()["status"] == "expired"


def test_retry_resends_same_token_with_new_deadline(
    client: TestClient,
    auth_headers: dict[str, str],
    mailbox: _Mailbox,
    monkeypatch,
) -> None:
    """Retry reuses the same token and refreshes the deadline."""
    client.post(
        "/notifications/email",
        json={"email": "notify@example.com"},
        headers=auth_headers,
    )
    first_settings = client.get(
        "/notifications/settings", headers=auth_headers
    ).json()
    first_code = _code_from(mailbox.sent[0][2])

    # Skip past the resend cooldown.
    from datetime import timedelta

    real_now = confirm_svc._now

    def _later():
        return real_now() + timedelta(seconds=120)

    monkeypatch.setattr(confirm_svc, "_now", _later)

    res = client.post(
        "/notifications/email/resend", headers=auth_headers
    )
    assert res.status_code == 200
    second_code = _code_from(mailbox.sent[1][2])
    assert second_code == first_code
    assert (
        res.json()["pending_expires_at"]
        > first_settings["pending_expires_at"]
    )


def test_resend_without_pending_is_400(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Resending with nothing pending returns 400."""
    res = client.post(
        "/notifications/email/resend", headers=auth_headers
    )
    assert res.status_code == 400


def test_replacing_keeps_old_until_confirmed(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """Setting a new address leaves the old confirmed one active."""
    # Confirm the first address.
    client.post(
        "/notifications/email",
        json={"email": "first@example.com"},
        headers=auth_headers,
    )
    client.post(
        "/notifications/email/confirm",
        json={"code": _code_from(mailbox.sent[0][2])},
    )
    # Start confirming a second address.
    res = client.post(
        "/notifications/email",
        json={"email": "second@example.com"},
        headers=auth_headers,
    ).json()
    assert res["notification_email"] == "first@example.com"
    assert res["pending_email"] == "second@example.com"


def test_clear_email_removes_confirmed_and_pending(
    client: TestClient, auth_headers: dict[str, str], mailbox: _Mailbox
) -> None:
    """DELETE clears both the confirmed address and any pending one."""
    client.post(
        "/notifications/email",
        json={"email": "first@example.com"},
        headers=auth_headers,
    )
    client.post(
        "/notifications/email/confirm",
        json={"code": _code_from(mailbox.sent[0][2])},
    )
    res = client.delete(
        "/notifications/email", headers=auth_headers
    ).json()
    assert res["notification_email"] is None
    assert res["pending_email"] is None
```

- [ ] **Step 2: Run the new tests**

Run: `cd backend && uv run pytest tests/test_notification_email.py -q`
Expected: PASS (all tests).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_notification_email.py
git commit -m "test: notification-email confirmation flow"
```

---

## Task 10: Backend tests — resolution + extended settings shape

**Files:**

- Modify: `backend/tests/test_notification_settings.py`
- Modify: `backend/tests/test_notifications_dispatch.py`

- [ ] **Step 1: Update the defaults-shape assertion**

In `test_notification_settings.py`, `test_get_settings_returns_defaults`,
replace the equality assertion with one that tolerates the new fields:

```python
    assert body == {
        "email_enabled": True,
        "webpush_enabled": False,
        "telegram_dm_enabled": False,
        "notification_email": None,
        "pending_email": None,
        "pending_expires_at": None,
    }
```

- [ ] **Step 2: Add a resolution unit test**

Append to `test_notifications_dispatch.py` this test, which reuses the
file's existing `_seed_event` helper (creates `ok_user`/`fail_user` with
delivery rows) and the already-imported `Session`:

```python
def test_load_recipients_prefers_notification_email(
    db_session: Session,
) -> None:
    """A confirmed notification_email overrides the profile email."""
    from app.models.notification_settings import (
        UserNotificationSettings,
    )
    from app.services.notifications.dispatch import _load_recipients

    event, users = _seed_event(db_session)
    db_session.add(
        UserNotificationSettings(
            user_id=users["ok"].id,
            email_enabled=True,
            notification_email="notify@x.test",
        )
    )
    db_session.flush()

    recipients = _load_recipients(event, db_session)
    by_user = {r.user_id: r for r in recipients}
    # ok_user has a confirmed notification address -> it wins.
    assert by_user[users["ok"].id].email == "notify@x.test"
    # fail_user has no settings row -> falls back to the profile email.
    assert by_user[users["fail"].id].email == "fail@x.test"
```

- [ ] **Step 3: Run the affected tests**

Run: `cd backend && uv run pytest tests/test_notification_settings.py tests/test_notifications_dispatch.py -q`
Expected: PASS

- [ ] **Step 4: Run the full backend suite + lint**

Run: `cd backend && uv run pytest -q`
Expected: PASS
Run: `cd backend && uv run ruff check src tests && uv run ruff format --check src tests`
Expected: ruff + format clean (fix any 80-char or import-order issues).

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_notification_settings.py backend/tests/test_notifications_dispatch.py
git commit -m "test: email resolution and extended settings shape"
```

---

## Task 11: Frontend types + composable actions

**Files:**

- Modify: `frontend/src/types.ts:85-89`
- Modify: `frontend/src/composables/useNotificationSettings.ts`

- [ ] **Step 1: Extend the types**

Replace the `NotificationSettings` interface with:

```ts
export interface NotificationSettings {
  email_enabled: boolean
  webpush_enabled: boolean
  telegram_dm_enabled: boolean
  notification_email: string | null
  pending_email: string | null
  pending_expires_at: string | null
}

export interface EmailConfirmResult {
  status: 'confirmed' | 'expired' | 'invalid'
  email: string | null
}
```

- [ ] **Step 2: Add composable actions**

In `useNotificationSettings.ts`, import the new type:

```ts
import type {
  EmailConfirmResult,
  NotificationSettings,
  NotificationTestResult,
} from '../types'
```

Add these functions inside `useNotificationSettings` (before `return`):

```ts
/** Start confirming a notification address; stores updated state. */
async function setNotificationEmail(email: string): Promise<void> {
  settings.value = await api.post<NotificationSettings>(
    '/notifications/email',
    { email },
  )
}

/** Resend the pending confirmation link with a fresh deadline. */
async function resendNotificationEmail(): Promise<void> {
  settings.value = await api.post<NotificationSettings>(
    '/notifications/email/resend',
  )
}

/** Clear the confirmed address and any pending confirmation. */
async function clearNotificationEmail(): Promise<void> {
  settings.value = await api.delete<NotificationSettings>(
    '/notifications/email',
  )
}

/** Submit a confirmation code (no auth required). */
async function confirmNotificationEmail(
  code: string,
): Promise<EmailConfirmResult> {
  return api.post<EmailConfirmResult>('/notifications/email/confirm', {
    code,
  })
}
```

Add the four names to the returned object.

- [ ] **Step 3: Type-check**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/composables/useNotificationSettings.ts
git commit -m "feat: frontend notification-email API actions"
```

---

## Task 12: ProfileSettingsView — notification email field

**Files:**

- Modify: `frontend/src/views/ProfileSettingsView.vue`

- [ ] **Step 1: Add the email-address sub-section under the Email row**

In the template, replace the existing Email-row hint paragraph
(`Sends a message to your account email address.`) with copy that
reflects the configurable address:

```html
<p class="text-caption text-medium-emphasis ps-row__hint">
  Emails go to your confirmed notification address, or your account email if
  none is set.
</p>
```

Then, immediately after the closing `</div>` of the Email row's
`ps-row` block (before the `<v-divider class="my-3" />`), insert:

```html
<!-- Notification email address -->
<div class="ps-email">
  <v-text-field
    v-model="emailInput"
    label="Notification email"
    type="email"
    density="comfortable"
    :disabled="saving"
    hide-details="auto"
    placeholder="Use account email"
  />
  <div v-if="pendingEmail" class="ps-email__status">
    <v-chip size="small" color="warning" variant="tonal">
      Pending: {{ pendingEmail }}
    </v-chip>
    <MtButton
      variant="soft"
      tone="primary"
      :loading="emailBusy"
      @click="onResendEmail"
    >
      Resend link
    </MtButton>
  </div>
  <div v-else-if="confirmedEmail" class="ps-email__status">
    <v-chip size="small" color="success" variant="tonal">
      Confirmed: {{ confirmedEmail }}
    </v-chip>
  </div>
  <div class="ps-email__actions">
    <MtButton
      variant="solid"
      tone="primary"
      :loading="emailBusy"
      :disabled="!emailInput || emailInput === confirmedEmail"
      @click="onSaveEmail"
    >
      Send confirmation
    </MtButton>
    <MtButton
      v-if="confirmedEmail || pendingEmail"
      variant="soft"
      tone="neutral"
      :loading="emailBusy"
      @click="onClearEmail"
    >
      Use account email
    </MtButton>
  </div>
  <p v-if="emailMessage" class="text-caption ps-email__msg">
    {{ emailMessage }}
  </p>
</div>
```

- [ ] **Step 2: Add the script state and handlers**

In `<script setup>`, pull the new actions from the composable
destructure (add to the existing `useNotificationSettings()` call):

```ts
const {
  settings,
  fetchSettings,
  updateSettings,
  subscribeWebPush,
  unsubscribeWebPush,
  testChannel,
  setNotificationEmail,
  resendNotificationEmail,
  clearNotificationEmail,
} = useNotificationSettings()
```

Add reactive state (near the other `ref`s):

```ts
const emailInput = ref('')
const emailBusy = ref(false)
const emailMessage = ref('')

const confirmedEmail = computed(
  () => settings.value?.notification_email ?? null,
)
const pendingEmail = computed(() => settings.value?.pending_email ?? null)
```

Ensure `computed` is imported from `vue` (add it to the existing
`import { ref } from 'vue'` line).

In the existing settings-load handler (where `emailEnabled.value` is set
from `settings.value`), also seed the input:

```ts
emailInput.value = settings.value?.notification_email ?? ''
```

Add the handlers (near `onTest`):

```ts
async function onSaveEmail(): Promise<void> {
  emailBusy.value = true
  emailMessage.value = ''
  try {
    await setNotificationEmail(emailInput.value.trim())
    emailMessage.value = 'Confirmation link sent. Check your inbox.'
  } catch {
    emailMessage.value = 'Could not send the confirmation link.'
  } finally {
    emailBusy.value = false
  }
}

async function onResendEmail(): Promise<void> {
  emailBusy.value = true
  emailMessage.value = ''
  try {
    await resendNotificationEmail()
    emailMessage.value = 'A new confirmation link is on its way.'
  } catch {
    emailMessage.value = 'Could not resend the link just yet.'
  } finally {
    emailBusy.value = false
  }
}

async function onClearEmail(): Promise<void> {
  emailBusy.value = true
  emailMessage.value = ''
  try {
    await clearNotificationEmail()
    emailInput.value = ''
    emailMessage.value = 'Notifications will use your account email.'
  } catch {
    emailMessage.value = 'Could not clear the address.'
  } finally {
    emailBusy.value = false
  }
}
```

- [ ] **Step 3: Add minimal styles**

In the component `<style scoped>`, add:

```css
.ps-email {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ps-email__status,
.ps-email__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.ps-email__msg {
  color: rgb(var(--v-theme-on-surface-variant, 120 120 120));
}
```

- [ ] **Step 4: Type-check + build**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/ProfileSettingsView.vue
git commit -m "feat: notification-email field in profile settings"
```

---

## Task 13: ConfirmEmailView + public route

**Files:**

- Create: `frontend/src/views/ConfirmEmailView.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: Create the confirmation view**

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useNotificationSettings } from '../composables/useNotificationSettings'

const route = useRoute()
const { confirmNotificationEmail } = useNotificationSettings()

type Phase = 'working' | 'confirmed' | 'expired' | 'invalid' | 'error'
const phase = ref<Phase>('working')
const email = ref<string | null>(null)

onMounted(async () => {
  const code = route.query.code
  if (typeof code !== 'string' || !code) {
    phase.value = 'invalid'
    return
  }
  try {
    const result = await confirmNotificationEmail(code)
    phase.value = result.status
    email.value = result.email
  } catch {
    phase.value = 'error'
  }
})
</script>

<template>
  <v-container class="confirm-email" max-width="520">
    <v-card class="pa-6 text-center">
      <template v-if="phase === 'working'">
        <v-progress-circular indeterminate color="primary" />
        <p class="mt-4">Confirming your email…</p>
      </template>
      <template v-else-if="phase === 'confirmed'">
        <h1 class="text-h6 mb-2">Email confirmed</h1>
        <p>{{ email }} will now receive your MeepleTime notifications.</p>
      </template>
      <template v-else-if="phase === 'expired'">
        <h1 class="text-h6 mb-2">Link expired</h1>
        <p>
          This confirmation link is no longer valid. Request a new one from your
          profile settings.
        </p>
      </template>
      <template v-else-if="phase === 'invalid'">
        <h1 class="text-h6 mb-2">Invalid link</h1>
        <p>This confirmation link is not recognised.</p>
      </template>
      <template v-else>
        <h1 class="text-h6 mb-2">Something went wrong</h1>
        <p>Please try again in a moment.</p>
      </template>
      <v-btn class="mt-6" color="primary" to="/profile"> Go to settings </v-btn>
    </v-card>
  </v-container>
</template>

<style scoped>
.confirm-email {
  margin-top: 48px;
}
</style>
```

- [ ] **Step 2: Register the public route**

In `router/index.ts`, add a route entry alongside the other top-level
routes (it must NOT have `requiresAuth`, so the guard lets it through):

```ts
  {
    path: '/confirm-email',
    component: () => import('../views/ConfirmEmailView.vue'),
    meta: { title: 'Confirm email' },
  },
```

- [ ] **Step 3: Type-check + build**

Run: `cd frontend && npx vue-tsc --noEmit && npm run build`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ConfirmEmailView.vue frontend/src/router/index.ts
git commit -m "feat: public email-confirmation page and route"
```

---

## Task 14: Docs

**Files:**

- Modify: `docs/operator/notifications.md`
- Modify: `docs/user/notifications.md`

- [ ] **Step 1: Operator note**

In `docs/operator/notifications.md`, near the SMTP configuration
section, add a short paragraph:

> Users can set a dedicated notification email in their profile. Setting
> one sends a confirmation link (valid for `EMAIL_CONFIRMATION_TTL_HOURS`,
> default 24h) using the same SMTP settings as notification delivery; the
> address is used only after the link is confirmed. Until then — or when
> no notification email is set — notifications fall back to the account
> (profile) email while email notifications are enabled.

- [ ] **Step 2: User note**

In `docs/user/notifications.md`, add a short "Notification email"
subsection describing: set an address, confirm via the emailed link
(valid 24h), use "Resend link" to get a fresh one, and that without a
confirmed address your account email is used.

- [ ] **Step 3: Commit**

```bash
git add docs/operator/notifications.md docs/user/notifications.md
git commit -m "docs: notification email confirmation"
```

---

## Final verification

- [ ] **Backend:** `cd backend && uv run pytest -q` → all pass.
- [ ] **Migration round-trips:** against a dev DB,
      `cd backend && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` → clean.
- [ ] **Frontend:** `cd frontend && npx vue-tsc --noEmit && npm run build` → clean.
- [ ] **Lint:** `pre-commit run --all-files` → ruff + prettier pass (80-char limit everywhere).
- [ ] **Manual smoke (optional, needs SMTP):** set an email in `/profile`, click the link in the captured/dev mail, confirm the address flips to "Confirmed", and that a viability notification then targets it.

```

```
