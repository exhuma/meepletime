# Security Guide

This project is a stateless OAuth2 resource server with ACL-controlled writes.

## Authentication

- Validate JWT signature against `OAUTH_JWKS_URL`.
- Validate token expiration and audience (`OAUTH_AUDIENCE`).
- Keep token validation centralized and identity-provider agnostic.
- Attach authenticated principal to request context after validation.
- Do not introduce session-based auth or server-side session state.

## Browser Token Storage — Two-Store Design

The frontend stores the JWT in two places simultaneously, each
serving a distinct audience:

| Store | Who reads it | Purpose |
|---|---|---|
| `localStorage` (`docroot_token`) | JavaScript | `fetch()` calls construct `Authorization: Bearer <token>` headers. `isAuthenticated()`, the token dialog, and upload forms all read from the reactive `token` ref. |
| `session` cookie (`HttpOnly; SameSite=Lax`) | The browser | Attached automatically to every same-origin request, including `<iframe>` navigations that cannot carry custom headers. nginx's `auth_request` subrequest inherits the cookie, enabling access-controlled doc serving inside the iframe. |

Neither store can be dropped:

- The `session` cookie is `HttpOnly`, so JavaScript cannot read
  it. The SPA therefore needs `localStorage` to hold the raw
  token for use in `Authorization` headers.
- `localStorage` values are invisible to automatic browser
  credential attachment on navigations, so the cookie is still
  required for the iframe.

The exchange flow is:

1. User supplies a bearer token via the token dialog.
2. `setToken(t)` in `auth.ts` writes the token to `localStorage`
   and calls `POST /api/auth/session` with the token in the
   `Authorization` header.
3. The backend validates the JWT and responds with
   `Set-Cookie: session=<token>; HttpOnly; SameSite=Lax; Path=/`.
4. Subsequent iframe navigations and page refreshes carry the
   `session` cookie automatically.
5. On logout, `setToken(null)` removes the `localStorage` entry
   and calls `DELETE /api/auth/session`, which clears the cookie
   via `Max-Age=0`.
6. On page refresh, `auth.ts` calls `POST /api/auth/session`
   immediately if a token is already in `localStorage`, keeping
   the cookie current across hard reloads.

On the backend, `get_optional_auth` resolves credentials in
priority order: `Authorization` header → `session` cookie →
unauthenticated (`None`). No server-side state is created; the
cookie payload is the raw JWT and is validated identically to
the header path.

## Role Extraction and Authorization

- Use pluggable role extraction (`OAUTH_ROLE_EXTRACTOR`).
- Role extractor receives raw token value only after successful validation.
- Role extractor context must include issuer and audience.
- Namespace ACL in `namespace.toml` controls read/write authorization.
- `public_read=true` allows unauthenticated reads only.
- All writes require valid JWT and ACL write permission.

## Upload Security

- Accept ZIP uploads only when namespace/project authorization is valid.
- Reject traversal paths and symlink entries in ZIP archives.
- Require top-level `index.html` in archive content.
- Enforce extraction size and file-count limits.
- Ignore uploaded `metadata.toml`; generate metadata server-side.
- Keep extraction and final write on same filesystem for atomic rename.

## Filesystem and Immutability

- `/data` is the authoritative data store.
- Never allow overwriting existing version+locale artifacts.
- Perform all writes through storage abstraction.
- Ensure atomic creation and `latest` symlink updates.

## Resolution and Fallback Safety

- Use resolver for every version lookup, including `latest`.
- Locale fallback order is fixed and deterministic:
  requested locale, then `en`, then any existing locale, then `404`.
- If fallback occurs, UI should show a gentle notice.

## nginx and Exposure Controls

- nginx serves static documentation from `/data`.
- nginx enforces upload request limits and max body size.
- FastAPI should not stream large static files directly.
- Every static documentation request MUST pass through the
  FastAPI `auth_request` gate (`GET /api/auth`) before nginx
  serves the file.  nginx uses the `auth_request` directive to
  delegate authorization; FastAPI returns 200 (allow), 401
  (unauthenticated), or 403 (forbidden) based on the namespace
  ACL.
- The internal auth location (`/internal/auth`) is marked
  `internal` in nginx and cannot be accessed by external
  clients.
- The `X-Original-URI` header carries the original request path
  to `GET /api/auth` so it can extract the namespace and
  evaluate the correct ACL.
- When the API server is unreachable, nginx fails closed
  (returns 500) rather than open.

## Security Review Checklist

- Auth check runs before every write operation.
- ACL write check is present for all mutating endpoints.
- ZIP validation includes traversal and symlink rejection.
- Filesystem writes are atomic and immutable.
- Resolver is used for `latest` and locale handling everywhere.
- Static documentation routes are guarded by nginx
  `auth_request` delegating to `GET /api/auth`.
