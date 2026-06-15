# Running on the host (without the dev-container)

The `.devcontainer/` setup is optional and human-oriented. This page
documents running MeepleTime's stack **directly on the host** — the
first-class path for coding agents and anyone who prefers native
tooling. App runtimes run natively; only the stateful backing
services run as disposable Docker containers.

## Prerequisites

- **Docker** — for the throwaway PostgreSQL (and optional Keycloak).
- **uv** — manages the Python 3.14 interpreter and the backend venv.
  `task setup:host` installs it if missing.
- **nvm** — provides Node for the frontend. If absent, a
  system-installed Node/npm is used instead.

Dependencies stay project-local: the Python venv lives in
`backend/.venv`, Node modules in `frontend/node_modules`. No runtimes
are installed via the host package manager.

## One-shot bootstrap

```bash
task setup:host
```

This installs backend deps (`uv sync`, which also fetches the pinned
Python), frontend deps (`npm install` under nvm's LTS Node), registers
pre-commit hooks, and seeds host-flavoured env files **only if they do
not already exist**:

- `backend/.env` — `localhost` DB URL, OIDC URLs, and dev-auth
  enabled.
- `frontend/.env.local` — OIDC authority, API base URL, and
  `VITE_DEV_AUTH=true`.

### Env gotcha: `db:5432` vs `localhost`

`.devcontainer/init.bash` seeds `backend/.env` with the **container**
DB hostname `db:5432`, which is unreachable from a host process. If
you previously opened the dev-container, your `backend/.env` is
container-flavoured. Either change the host to `localhost`, or set a
shell override (shell env beats the `.env` file):

```bash
export MEEPLETIME_DATABASE_URL=postgresql://meepletime:changeme@localhost:5432/meepletime
```

`task setup:host` prints a warning when it detects a
container-flavoured `backend/.env`.

## Start the stack

```bash
task dev:db      # throwaway PostgreSQL 16 on localhost:5432
task migrate     # alembic upgrade head
task backend     # FastAPI on :8000 (reload)
task frontend    # Vite dev server on :5173
```

Open http://localhost:5173.

## Auth: dev-auth by default (no Keycloak)

With the seeded env (`MEEPLETIME_DEV_AUTH_ENABLED=true` +
`VITE_DEV_AUTH=true`), the SPA shows a dev-login picker and the
backend mints real HS256 tokens through the standard validator — no
Keycloak required. For headless API calls:

```bash
task dev:token            # mint an HS256 dev JWT
task dev:login            # POST /auth/dev/login on the running backend
```

These dev flags are development-only and must never be set in
production. See `docs/developer/auth.md`.

## Optional: real OIDC with Keycloak

Only needed to exercise the real OIDC flow end-to-end:

```bash
task dev:keycloak         # realm-imported Keycloak on :8080
# ... run your OIDC e2e ...
task dev:keycloak-stop
```

The OIDC URLs use the `keycloak.127.0.0.1.nip.io` hostname, which
resolves to `127.0.0.1` via public DNS — so the issuer claim matches
identically on the host with no `/etc/hosts` edits. The seeded env
already points at this authority.

## Choosing different ports

The defaults are conventional, not mandatory. If a port is taken,
override it and update any dependent config:

| Service    | Default | Override env var           | Also update                      |
|------------|---------|----------------------------|----------------------------------|
| Backend    | 8000    | `MEEPLETIME_BACKEND_PORT`  | `VITE_API_BASE_URL`              |
| Frontend   | 5173    | `MEEPLETIME_FRONTEND_PORT` | `MEEPLETIME_APP_BASE_URL`        |
| PostgreSQL | 5432    | `MEEPLETIME_DB_PORT`       | `MEEPLETIME_DATABASE_URL`        |
| Keycloak   | 8080    | `MEEPLETIME_KEYCLOAK_PORT` | OIDC authority in both env files |

Example:

```bash
MEEPLETIME_BACKEND_PORT=8001 task backend
# then set VITE_API_BASE_URL=http://localhost:8001 in
# frontend/.env.local before starting the frontend.
```

## Playwright and debuggers

Because every service is a plain local process, browser automation
and debuggers attach directly — no container indirection. Point
Playwright at `http://localhost:5173` (or your chosen frontend port),
and attach a Python debugger to the `uv run uvicorn` process as usual.

## Teardown

```bash
task dev:db-stop          # stop + drop the throwaway PostgreSQL
task dev:keycloak-stop    # stop the throwaway Keycloak (if started)
```

Both DB and Keycloak containers are ephemeral (`--rm`); their data is
dropped on stop.
