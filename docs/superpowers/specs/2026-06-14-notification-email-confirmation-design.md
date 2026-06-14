# Notification email with confirmation — design

Date: 2026-06-14
Status: Approved (brainstorming) — ready for implementation plan

## Goal

Let a user set a dedicated **notification email** that is verified by a
confirmation link before it is used. Setting an address sends a link
valid for 24h; the user can request a retry that resends the *same*
link with a fresh deadline; a successful confirmation invalidates the
code. If no confirmed notification email exists, fall back to the
user's profile email — but only while email notifications are enabled.

## Context (existing system)

- `User.email` is the **profile email**, provisioned from the Keycloak
  OIDC token. It is already verified by the IdP and needs no
  confirmation.
- `UserNotificationSettings` (1 row per user) holds per-channel on/off
  flags including `email_enabled`. It carries no address today.
- The email channel
  (`backend/src/app/services/notifications/channels/email.py`) sends
  over SMTP and only emits a target when
  `recipient.settings.is_channel_enabled("email")` is true.
- `dispatch._load_recipients` (`dispatch.py:88`) currently sets
  `email=user.email` directly.
- SMTP config and `APP_BASE_URL` (public frontend base, used to build
  links) already exist in `config.py`.
- `ProfileSettingsView.vue` already renders a Notifications section with
  an "Email" toggle whose helper text reads "Sends a message to your
  account email address."

The contract (`contract.md`) leaves notification transport/addressing
open, so a confirmed notification address is in-scope and excluded by
nothing.

## Decisions

- **Scope:** full-stack (backend + `ProfileSettingsView` UI + a public
  confirmation route).
- **Confirmation link target:** a frontend SPA route
  (`/confirm-email?code=…`) that POSTs the code to the backend and
  renders the result. No auth on the link.
- **Replacement behaviour:** when a user with an already-confirmed
  address sets a new one, the old confirmed address keeps receiving
  notifications until the new one is confirmed (no notification gap).
- **Toggle independence:** confirming an address does **not** auto-enable
  `email_enabled`. The address and the on/off switch stay independent.

## Data model

1. **`UserNotificationSettings.notification_email`** — new nullable
   `String(255)` column. Holds only the **confirmed** address. `NULL`
   means "fall back to profile email".
2. **New `EmailConfirmation` table** — at most one row per user
   (`unique(user_id)`), holding the transient pending state:
   - `id` (UUID PK)
   - `user_id` (FK `users.id`, `ondelete=CASCADE`, unique, indexed)
   - `pending_email` (`String(255)`)
   - `token` (`String(64)`, indexed) — an opaque high-entropy
     `secrets.token_urlsafe(32)`. Stored as-is (not hashed) because the
     **retry** requirement re-sends *the same link*, so the token must be
     reproducible on resend; a one-way hash could not be. It is never
     returned by any API response.
   - `expires_at` (`DateTime(timezone=True)`)
   - `created_at` (`DateTime(timezone=True)`)

Keeping the pending state in its own table (not on the settings row)
keeps the token out of any settings serialization and makes "confirm =
delete the pending row" a clean operation. One Alembic migration adds
the column and the table.

## Effective-email resolution

Single source of truth used by `dispatch._load_recipients`:

```
address = settings.notification_email or user.email
```

The existing `email_enabled` gate in the email channel is unchanged and
acts as the master switch:

- email disabled → no email is sent, regardless of address.
- email enabled → use the confirmed `notification_email` if present,
  otherwise the profile email.

A pending (unconfirmed) address is never used for delivery because it
lives only in `EmailConfirmation`, never in `notification_email`.

## Endpoints (extending the `/notifications` router)

All authenticated and self-scoped except the confirm endpoint.

- `POST /notifications/email` — body `{ "email": <EmailStr> }`.
  Start confirmation for a new address: upsert the `EmailConfirmation`
  row with a **new** token and `expires_at = now + TTL`, then send the
  link. Any previously confirmed `notification_email` stays active.
- `POST /notifications/email/resend` — **retry**: reuse the *same*
  token on the existing pending row, reset `expires_at = now + TTL`,
  resend the same link. `400` if nothing is pending. A short cooldown
  (60s) guards against repeated taps; the last send time is derived as
  `expires_at - TTL`, so no extra column is needed.
- `POST /notifications/email/confirm` — body `{ "code": <str> }`,
  **unauthenticated** (the token is the authority). Look up by
  `token_hash`; if found and not expired, set
  `notification_email = pending_email`, delete the pending row (single
  use — the code is no longer valid afterward), and report success.
  Distinct, non-enumerating responses for success / expired / invalid.
- `DELETE /notifications/email` — clear the confirmed address and any
  pending row (revert to profile fallback).
- `GET /notifications/settings` — extended to surface
  `notification_email`, `pending_email`, and `pending_expires_at` so the
  UI can render confirmed / pending / expired state.

### Retry semantics

- "Set a new address" (`POST /notifications/email`) → new token.
- "Retry" (`POST /notifications/email/resend`) → same token, new
  deadline. This is what makes the originally emailed link keep working
  after a retry.

## Frontend

- `ProfileSettingsView.vue`, Notifications section: an email input plus
  state-aware affordances — "Send confirmation" / "Resend link",
  confirmed / pending / expired chips, and a clear action — wired
  through `useNotificationSettings`. Update the "Email" toggle helper
  text to reflect the configurable address and the profile-email
  fallback.
- New public route `/confirm-email` → `ConfirmEmailView.vue`: read
  `?code=`, POST to `/notifications/email/confirm`, render
  success / expired / invalid. No auth guard.
- Extend `useNotificationSettings` / the API client with the new calls
  and the extended settings shape.

## Config

- `EMAIL_CONFIRMATION_TTL_HOURS` (default `24`) on `Settings`, so the
  validity window is tunable and tests can shorten it.

## Security notes

- Token is 256-bit (`secrets.token_urlsafe(32)`), unguessable, and
  never returned by any API response or logged. It is stored as-is (not
  hashed) because retry must re-send the identical link; the residual
  risk is limited to an attacker with full DB read access, for whom the
  system is already compromised.
- Tokens are single-use (row deleted on confirm) and time-limited.
- Confirm endpoint does not reveal whether an email/account exists;
  responses describe the code state only.
- Email addresses validated via pydantic `EmailStr`.
- Resend cooldown limits abuse of the send path.

## Testing (security-sensitive → required)

Backend pytest:

- set → confirm sets `notification_email` and clears the pending row.
- retry resends with a new deadline on the **same** token; the original
  link still confirms.
- confirming invalidates the code (a second confirm fails).
- expired code is rejected.
- replacing a confirmed address keeps the old one active for delivery
  until the new one is confirmed.
- effective-email resolution: confirmed address wins; profile email used
  as fallback; nothing sent when `email_enabled` is false.
- confirm endpoint requires no auth and rejects unknown/expired codes
  without leaking existence.

## Docs

- Operator docs: note the notification-email confirmation flow alongside
  the existing SMTP configuration.
- Reflect the helper-text/behaviour change where relevant.

## Out of scope

- Changing the profile email itself (owned by Keycloak).
- Per-circle notification email overrides.
- HTML/multipart confirmation emails (plain text, matching the existing
  email channel).
