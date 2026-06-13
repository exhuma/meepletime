# AI Assistant Rules

This is the single source of truth for any AI coding agent working in
this repository (Claude Code, Codex, Cursor, …). `CLAUDE.md` is a thin
pointer to this file.

Before generating or modifying files, load **every** instruction kit
listed below in order. All rules in those kits are non-negotiable unless
`contract.md` explicitly overrides them. Correctness and security take
priority over convenience.

---

## Source-of-truth documents (read these first)

- **`contract.md`** — the authoritative feature/behaviour spec. Do not
  edit it unless explicitly asked, and never implement features it
  excludes. If it ever goes missing, alert the developer before doing
  feature work.
- **`AGENTS.md`** (this file) — mandatory rule-kit loading order and
  task-scoped rules. Treat its rules as non-negotiable unless
  `contract.md` overrides them.
- **`TODO.md`** — current backlog / in-flight work.

When this file / `contract.md` disagree with recent edit history or the
README, the contract and AGENTS.md win.

> **README is partially stale:** its API table and "JWT/local password"
> auth description predate the OIDC migration. Local password login,
> `/auth/register`, and `/auth/token` **do not exist** — see
> Authentication below.

---

## Project

MeepleTime is a self-hosted, mobile-first meeting-availability app for
private "circles". Members mark each day as `can_attend` or `can_host`
(the legacy labels in code are still `attending`/`hosting`); the backend
derives whether a day is a *viable* meetup based on per-circle thresholds
and per-member host constraints.

Backend: Python 3.14, FastAPI, SQLAlchemy 2, PostgreSQL 16, Alembic,
APScheduler. Frontend: Vue 3 (`<script setup lang="ts">` only), Vuetify
3, Vite, vue-router, oidc-client-ts.

---

## Instruction kits

Load these kits at the start of every session that touches backend or
frontend code:

1. `stack-fastapi-vuetify` — core stack rules (always)
2. `module-auth-oidc` — OIDC general rules (Keycloak, Option A)
3. `module-auth-oidc-python` — backend token validation
4. `module-auth-oidc-vue` — frontend OIDC flow (PKCE)
5. `module-database-postgresql` — PostgreSQL / Alembic
6. `module-code-style-python` — Python style and linting

Optional (recommended):

7. `module-dev-tooling-taskfile` — Taskfile conventions
8. `module-docs-sphinx` — Sphinx documentation

### Task-scoped applicability

The baseline list above remains mandatory whenever backend or frontend
code is touched. Use the following as an additional selection rule so
agents do not drift into loading only the most recently edited part of
the stack.

**Backend-only tasks** — still load the full mandatory baseline, then
also consider:

- `module-fastapi` — backend architecture, dependency usage, error
  handling, and endpoint composition
- `module-api-design` — HTTP semantics, status codes, pagination, and
  response consistency
- `module-observability-healthz` — health probes and operational
  readiness checks when the task is ops-facing

**Frontend-only tasks** — still load the full mandatory baseline, then
also consider:

- `module-vue-vuetify` — Vue 3 + Vuetify implementation rules
- `module-api-design` — request/response expectations shared with the
  backend
- `module-release-metadata` — only when exposing build/version metadata
  in the frontend

**Cross-cutting or ops tasks** — prefer adding these on top of the
baseline when relevant:

- `module-dev-tooling-taskfile` — local developer workflow and task
  automation
- `module-observability-healthz` — live/readiness checks and operational
  probes
- `module-library-preferences` — when choosing or replacing dependencies

**Avoiding false narrowing**

- Do not infer that frontend kits are no longer applicable merely
  because the most recent changes were backend-only.
- Do not infer that backend kits are optional merely because a task
  touches only docs or tooling; they may still constrain behavior.
- Use `contract.md` and this file as the primary source of truth when
  kit selection and recent edit history disagree.

---

## Commands

Tasks are run via [Task](https://taskfile.dev) (`Taskfile.yml`). The
backend uses `uv` (not bare `pip`/`venv`).

```bash
task migrate          # alembic upgrade head (backend/)
task backend          # uvicorn dev server w/ reload (runs migrate first)
task frontend         # vite dev server (--host 0.0.0.0)
task build:frontend   # production frontend build
task test:backend     # pytest; pass args after --, e.g. task test:backend -- -k circles
task dev:token        # mint an HS256 dev JWT for headless API calls (see below)
task dev:db           # throwaway Postgres on localhost:5432 for host runs
task dev:db-stop      # stop/remove the throwaway dev DB (drops data)
task db-shell         # psql into $MEEPLETIME_DATABASE_URL
```

Run a single backend test:
`task test:backend -- tests/test_circles.py::test_name` or
`cd backend && uv run pytest -k <expr>`.

Lint/format is via pre-commit (ruff for `backend/`, prettier for
`frontend/`): `pre-commit run --all-files`. Ruff config lives in
`backend/pyproject.toml` (line-length 80, `select = E,W,F,I,UP`).
**80-char line limit applies to all files.**

Full stack via Docker: `docker compose up --build` (frontend on `:80`,
API on `:8000`, `/docs` for Swagger).

---

## Authentication

Option: **A — Keycloak (self-hosted OIDC)**. Auth is **exclusively**
Keycloak OIDC. There is no in-app login form and local password auth
must never be reintroduced. GitHub login is out of scope. Providers
configured inside Keycloak: TBD.

Two Keycloak clients are used: `meepletime-frontend` (public OIDC client
for the PKCE flow) and `meepletime-backend` (bearer-only resource server
for audience-claim propagation). See `module-auth-oidc`.

- **Frontend** is a public OIDC client doing authorization-code + PKCE
  via `oidc-client-ts`. Config in `frontend/src/auth/oidc.ts`; tokens
  live in `sessionStorage`. The router guard
  (`frontend/src/router/index.ts`) redirects to `/login` (which *then*
  calls `signinRedirect()` from `onMounted`) rather than redirecting
  inside the guard — doing the latter causes an infinite redirect loop.
  `client_secret` must never appear in frontend code.
- **Backend** is a stateless bearer-only resource server.
  `get_current_user` in `backend/src/app/dependencies.py` validates
  every request's token and lazily provisions a local `User` +
  `AuthIdentity` on first sight of a subject. RS256 tokens are validated
  against Keycloak JWKS (`auth/jwks.py`, resolved via the OIDC discovery
  doc).
- **Dev tokens:** when `MEEPLETIME_DEV_SHARED_SECRET` is set, the
  backend *also* accepts self-minted **HS256** JWTs (algorithm is chosen
  from the token's `alg` header). This is **development/headless-agent
  only — never set it in production.** Mint one with `task dev:token`.
- **Dev login (in-app, no Keycloak):** for driving the *whole SPA*
  without Keycloak, set `MEEPLETIME_DEV_AUTH_ENABLED=true` (backend)
  and `VITE_DEV_AUTH=true` (frontend dev server). The backend then
  mounts a single `POST /auth/dev/login` that mints a real HS256 token
  for the identity (`sub`/`email`/`name`) in the request body — the
  HTTP twin of `task dev:token` — flowing through the standard
  validator + user-provisioning (**not** a bypass). It has **no**
  notion of named presets and no enumeration endpoint, so no dev
  credentials are baked into the API. The dev-only `LoginView` picker
  offers a few convenience identities (documented in
  `docs/developer/auth.md`, defined only in the stripped-from-prod
  frontend). Roles are per-circle, so an "admin" identity has no global
  powers until it joins/owns a circle. Gating is defense-in-depth —
  backend default off (router unmounted → 404), startup refuses to boot
  if enabled without `DEV_SHARED_SECRET`, and the frontend honours
  `VITE_DEV_AUTH` only under the Vite dev server (`import.meta.env.DEV`),
  so any production build excludes the code entirely. **Never enable
  either flag in production.** See `docs/developer/auth.md`.

---

## Backend architecture

`backend/src/app/` (package importable as `app`; `pythonpath=src`).

- **`main.py`** — the *only* place app wiring happens
  (application-factory pattern, `create_app()`). All routers,
  middleware, and the lifespan handler are registered here. Middleware
  is LIFO: CORS is outermost (to answer preflight before auth), then
  logging, then security headers. The lifespan starts/stops the
  APScheduler notification scheduler.
- **`config.py`** — `Settings` (pydantic-settings) with **`env_prefix =
  "MEEPLETIME_"`**. So locally the real env vars are
  `MEEPLETIME_DATABASE_URL`, `MEEPLETIME_OIDC_AUTHORITY`, etc. (The root
  `.env.example` shows the *docker-compose-level* unprefixed names that
  get remapped into the container.) Settings are cached via `lru_cache`.
- **`routers/`** — one module per resource (circles, memberships,
  availability, viability, host_day_constraints, day_notes, auth).
  `auth.py` only exposes `/auth/me`.
- **`dependencies.py`** — shared FastAPI deps: `get_current_user`, plus
  the authorization helpers `get_circle_or_404`, `get_membership_or_403`,
  `require_admin_or_owner`, `require_owner`, and `validate_date_range`.
  RBAC roles are `MemberRole.owner | admin | member`. Never bypass these
  checks.
- **`models/`** — SQLAlchemy 2 ORM (`Mapped[...]`). All models are
  re-exported from `models/__init__.py` so Alembic sees the full
  metadata. (Ruff `F821` is ignored in `models/*.py` because string
  forward-refs in `Mapped["X"]` look undefined to it.)
- **`schemas/`** — pydantic request/response models (kept separate from
  ORM).
- **`services/viability.py`** — the core domain logic. Per hosting
  member it merges circle defaults with personal `HostDayConstraint`
  taking the *most restrictive* value per field (`max` for minimums,
  `min` for maximums); a day is viable if **any** hosting member's
  effective constraints are satisfied. `has_multiple_viable_hosts`
  signals the UI that members should agree out-of-band on who hosts.
- **`services/notifications.py`** — APScheduler-backed, debounced
  (`MEEPLETIME_NOTIFICATION_DEBOUNCE_SECONDS`) notification evaluation
  keyed by `(circle_id, date)`.

DB schema is migration-driven via Alembic
(`backend/alembic/versions/`). Add a migration for every model change;
never rely on auto-create outside tests.

---

## Frontend architecture

`frontend/src/` — Vue 3 SPA, **`<script setup lang="ts">` only** (no
Options API, no `.js` files in `src/`).

- **`api/index.ts`** — vanilla `fetch` client. Token acquisition is
  delegated to a pluggable `TokenProvider` (`api/token.ts`) so transport
  is decoupled from auth; a registered 401 handler triggers re-auth.
- **`auth/oidc.ts`** — the singleton `UserManager`.
- **`router/index.ts`** — routes + auth guard (see Authentication note
  above).
- **`views/`** — route-level pages (Circles, CircleCalendar, DayDetail,
  Join, Login, AuthCallback). **`components/`** — reusable
  dialogs/cells. **`composables/`** — shared state/logic (`auth`,
  `circles`, `appBar`).
- Vite proxies `/api` to the backend in dev; API base is
  `VITE_API_BASE_URL`, OIDC coords are `VITE_OIDC_AUTHORITY` /
  `VITE_OIDC_CLIENT_ID`.

---

## Testing

`backend/tests/` uses pytest with an **in-memory SQLite** engine (the
`client` fixture overrides `get_db`; the real Postgres is never
touched). `conftest.py` sets `MEEPLETIME_*` env defaults via
`os.environ.setdefault` **before** any app import (module-level
`get_settings()`/`create_engine()` run at import time), and auth in
tests uses HS256 dev tokens. Add tests for security-sensitive logic.

---

## Non-negotiable

- If `contract.md` is absent, alert the developer before proceeding with
  any feature work.
- Do not edit `contract.md` unless explicitly asked.
- Keep implementation aligned with `contract.md`.
- Do not implement features excluded by the contract.
- Never bypass authentication or authorisation checks.

---

## Agent behaviour

- Prefer minimal, focused changes.
- Update documentation when behaviour or architecture changes.
- Add tests for security-sensitive logic when implementation exists.
- Do not introduce project-specific assumptions not present in
  `contract.md`.
