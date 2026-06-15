# Host-native development for agents — design

**Date:** 2026-06-15
**Status:** Approved (pending spec review)

## Goal

Make running the stack **directly on the host** the documented,
first-class path for coding agents, removing the dev-container as a
prerequisite for agentic work. The dev-container stays intact and
fully supported for humans.

## Guiding principle

Dependencies are installed as project-local as possible to keep the
host clean. Wider-scope installs are allowed only when a truly local
install would explode complexity or hits a real technical constraint.
Stateful backing services (PostgreSQL, Keycloak) run as **disposable
containers** — isolation without polluting the host with long-lived
daemons. Agents are free to choose alternate TCP ports when a default
is taken.

## Decisions (locked)

- **Backing services:** app runtimes run natively on the host;
  PostgreSQL (and Keycloak only when real OIDC is needed) run as
  throwaway `docker run` containers, extending the existing `dev:db`
  pattern.
- **Toolchains:** `uv` manages the Python 3.14 interpreter
  (uv-scoped cache + project venv in `backend/.venv`); Node via `nvm`
  (user-scoped `~/.nvm`, pinned per project). Packages stay
  project-local; no system-wide package-manager installs. This mirrors
  what `.devcontainer/init.bash` already does.
- **Auth default:** agents default to **dev-auth mode** (no Keycloak).
  Keycloak runs in a container only for explicit real-OIDC end-to-end
  tests.
- **Ports:** keep conventional defaults; document that agents may pick
  any free port, and make the service ports overridable via env vars.

## Components

### 1. `AGENTS.md` — "Running on the host" section

A concise rule block instructing agents to:

- Run services natively, not inside the dev-container.
- Use `uv` (Python 3.14) and `nvm` (Node); keep packages
  project-local.
- Get PostgreSQL via `task dev:db`.
- Default to dev-auth mode (no Keycloak); start Keycloak only for
  real-OIDC e2e.
- Treat default ports as conventional but freely overridable.

It points to `docs/developer/host-run.md` as the detailed reference
(AGENTS.md keeps the rules terse; the doc holds the how-to).

### 2. `docs/developer/host-run.md` — full reference

Covers, for both humans and agents working outside the dev-container:

- **Bootstrap:** install `uv` and `nvm`; run `task setup:host`.
- **Env config (host-flavored):** `localhost` DB URL and dev-auth
  variables — explicitly different from the dev-container's
  `db:5432` / nip.io seeding.
- **Start sequence:** `task dev:db` → `task migrate` → `task backend`
  → `task frontend`.
- **Dev-auth login path:** the no-Keycloak default flow.
- **Optional Keycloak path:** `task dev:keycloak` for real-OIDC e2e.
- **Port overrides:** a table of the env vars and their defaults.
- **Playwright / debugging:** notes on why this is now trivial
  (every service is a local process, directly attachable).
- **Teardown:** `task dev:db-stop` / `task dev:keycloak-stop`.

Linked from `docs/developer/index.md`.

### 3. Taskfile ergonomics

- **`dev:keycloak` + `dev:keycloak-stop`** — a throwaway Keycloak
  container mirroring `dev:db`: publishes `:8080`, imports
  `deploy/dev/keycloak-realm.json` and the `assets/keycloak/themes`,
  uses the `keycloak.127.0.0.1.nip.io` hostname so issuer claims match
  the env defaults. Needed only for real-OIDC e2e.
- **`setup:host`** — host twin of `init.bash`: `uv sync`, nvm/npm
  install, `pre-commit install`, and seed **host-flavored**
  `backend/.env` + `frontend/.env.local` (localhost URLs + dev-auth
  enabled) only when absent.
- **Overridable ports** — backend, frontend, and dev DB ports become
  env-var overridable (e.g. `MEEPLETIME_BACKEND_PORT`,
  `MEEPLETIME_FRONTEND_PORT`, `MEEPLETIME_DB_PORT`) with current
  defaults preserved.

### 4. `.devcontainer/` — keep, annotate

No functional change. Add a header note clarifying the dev-container
is optional and human-oriented, not required for agents.

## Key gotcha to address

`.devcontainer/init.bash` seeds `backend/.env` with the **container**
DB hostname (`db:5432`) and nip.io OIDC URLs. On the host the DB URL
must be `localhost:5432` (or the chosen port). Notes:

- The nip.io OIDC URLs already resolve correctly on the host (nip.io
  is real public DNS that maps to `127.0.0.1`; `extra_hosts` was only
  needed *inside* the container), so Keycloak-container runs work
  unchanged from the host.
- `setup:host` and the doc must use **host-flavored** env values, must
  **warn** when a devcontainer-seeded `.env` is present (it points at
  `db:` and will not work on the host), and must recommend shell
  `export` overrides as the conflict-free way to switch a DB URL or
  port. `pydantic-settings` reads `.env` from the working directory
  and shell env vars override file values.

## Default auth flow for agents

Set `MEEPLETIME_DEV_SHARED_SECRET` + `MEEPLETIME_DEV_AUTH_ENABLED=true`
(backend) and `VITE_DEV_AUTH=true` (frontend) → the full SPA works
with no Keycloak. Use `task dev:token` / `task dev:login` for headless
API calls. Both dev flags are development-only and must never be set
in production.

## Out of scope (YAGNI)

- Auto-port-selection or per-agent deterministic port offsets
  (documented freedom was chosen instead).
- Removing or rewriting the dev-container.
- CI changes.

## Verification

- `task setup:host` on a host without an existing `.env` produces a
  working backend + frontend reachable in a browser with dev-auth
  login, against a `task dev:db` PostgreSQL — no dev-container, no
  Keycloak.
- `task dev:keycloak` brings up a realm-imported Keycloak and the SPA
  can complete a real OIDC login against it.
- Overriding a port env var moves the corresponding service and the
  dependent config follows (frontend reaches the relocated backend).
- A devcontainer-seeded `backend/.env` (with `db:5432`) triggers the
  documented warning rather than a silent connection failure.
