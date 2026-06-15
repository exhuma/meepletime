# Host-native development for agents — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make running the stack directly on the host the documented,
first-class path for coding agents, removing the dev-container as a
prerequisite while keeping it intact for humans.

**Architecture:** App runtimes (Python via uv, Node via nvm) run
natively on the host with project-local packages. Stateful backing
services (PostgreSQL, optional Keycloak) run as disposable
`docker run` containers, extending the existing `dev:db` pattern.
Agents default to dev-auth mode (no Keycloak) and may freely override
service ports via env vars. Changes are limited to `Taskfile.yml`, a
new bootstrap script, `AGENTS.md`, a new developer doc, and a
`.devcontainer` annotation — no application code changes.

**Tech Stack:** Taskfile, bash, uv, nvm, Docker, FastAPI/Vite (run
targets only), Markdown.

**Spec:** `docs/superpowers/specs/2026-06-15-host-native-dev-for-agents-design.md`

---

## File structure

- Modify: `Taskfile.yml` — overridable ports on `dev:db`, `backend`,
  `frontend`; new `dev:keycloak`, `dev:keycloak-stop`, `setup:host`
  tasks.
- Create: `scripts/setup-host.bash` — host bootstrap (toolchains +
  host-flavored env seeding + dev-container `.env` warning).
- Modify: `AGENTS.md` — add a "Running on the host" section and list
  the new tasks under "Commands".
- Create: `docs/developer/host-run.md` — full host-run reference.
- Modify: `docs/developer/index.md` — link the new doc.
- Modify: `.devcontainer/devcontainer.json` — header note that the
  dev-container is optional/human-oriented.

**Line-length note:** the repo's 80-char rule is enforced by ruff
(Python) and prettier (frontend) only. Keep new lines ≤80 where
feasible, but unbreakable tokens — URLs, `.env` values, and absolute
Docker `-v` bind paths — may exceed it, consistent with the existing
`backend/.env.example` and `Taskfile.yml`.

---

### Task 1: Select instruction kits (project workflow)

`AGENTS.md` requires per-task kit selection via the
`instructions-exhuma` MCP for any task touching code, docs, or
tooling. This task touches tooling and docs.

- [ ] **Step 1: Discover + select kits**

Using the `instructions-exhuma` MCP tools: `list_available_traits`
and `list_kits`, then `select_kits` with traits `tooling`, `docs`,
`taskfile` (add `broaden=True` if `broadening_recommended` is set),
and `get_kit` to load the matched kits into context. If the MCP is
unavailable, note the gap and proceed.

- [ ] **Step 2: Confirm constraints**

Verify nothing in the loaded kits contradicts this plan (e.g. file
layout or doc conventions). If it does, adjust the affected task
before implementing it.

No commit (context-only task).

---

### Task 2: Overridable ports + Keycloak container tasks

**Files:**
- Modify: `Taskfile.yml`

- [ ] **Step 1: Make `dev:db` port overridable**

In `Taskfile.yml`, change the `dev:db` `docker run` port mapping and
the final echo to honor `MEEPLETIME_DB_PORT` (default `5432`):

```yaml
      - >-
        docker run -d --rm --name meepletime-dev-db
        -e POSTGRES_DB=meepletime -e POSTGRES_USER=meepletime
        -e POSTGRES_PASSWORD=changeme
        -p ${MEEPLETIME_DB_PORT:-5432}:5432 postgres:16-alpine
      - echo "Waiting for PostgreSQL to accept connections…"
      - >-
        until docker exec meepletime-dev-db
        pg_isready -U meepletime -q; do sleep 1; done
      - >-
        echo "Ready →
        postgresql://meepletime:changeme@localhost:${MEEPLETIME_DB_PORT:-5432}/meepletime"
```

- [ ] **Step 2: Make `backend` and `frontend` ports overridable**

Update the `backend` and `frontend` task commands:

```yaml
  backend:
    desc: Start the FastAPI dev server with hot-reload
    dir: backend
    deps: [migrate]
    cmd: >-
      uv run uvicorn app.main:app --reload --host 0.0.0.0
      --port ${MEEPLETIME_BACKEND_PORT:-8000}
      --log-config logging.dev.yaml

  frontend:
    desc: Start the Vite dev server
    dir: frontend
    cmd: >-
      npm run dev -- --host 0.0.0.0
      --port ${MEEPLETIME_FRONTEND_PORT:-5173}
```

- [ ] **Step 3: Add `dev:keycloak` and `dev:keycloak-stop`**

Add these tasks (place them next to `dev:db`). The `KC_HOSTNAME` and
the published port share `MEEPLETIME_KEYCLOAK_PORT` so the issuer
claim always matches the published port:

```yaml
  dev:keycloak:
    desc: >-
      Start a throwaway Keycloak 26.5 (realm pre-imported) on
      localhost:8080 for real-OIDC end-to-end runs OUTSIDE the
      dev-container. Ephemeral. Most agent work should use dev-auth
      instead (no Keycloak). Override the port with
      MEEPLETIME_KEYCLOAK_PORT (also update the OIDC authority env in
      backend/.env and frontend/.env.local to match). Stop with
      `task dev:keycloak-stop`.
    cmds:
      - >-
        docker run -d --rm --name meepletime-dev-keycloak
        -e KC_BOOTSTRAP_ADMIN_USERNAME=admin
        -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin
        -e KC_HOSTNAME=http://keycloak.127.0.0.1.nip.io:${MEEPLETIME_KEYCLOAK_PORT:-8080}
        -e KC_HEALTH_ENABLED=true
        -p ${MEEPLETIME_KEYCLOAK_PORT:-8080}:8080
        -v {{.ROOT_DIR}}/deploy/dev/keycloak-realm.json:/opt/keycloak/data/import/meepletime-realm.json:ro
        -v {{.ROOT_DIR}}/assets/keycloak/themes:/opt/keycloak/themes:ro
        quay.io/keycloak/keycloak:26.5
        start-dev --import-realm --spi-theme-static-max-age=-1
        --spi-theme-cache-themes=false
        --spi-theme-cache-templates=false
      - echo "Waiting for Keycloak realm to import…"
      - >-
        until curl -fsS
        http://localhost:${MEEPLETIME_KEYCLOAK_PORT:-8080}/realms/meepletime
        | grep -q '"realm":"meepletime"'; do sleep 2; done
      - >-
        echo "Ready →
        http://keycloak.127.0.0.1.nip.io:${MEEPLETIME_KEYCLOAK_PORT:-8080}
        (admin / admin)"

  dev:keycloak-stop:
    desc: Stop and remove the throwaway Keycloak from `task dev:keycloak`.
    cmd: docker rm -f meepletime-dev-keycloak
```

- [ ] **Step 4: Verify the Taskfile parses**

Run: `task --list`
Expected: the list includes `dev:keycloak`, `dev:keycloak-stop`, and
no YAML/parse error is printed.

- [ ] **Step 5: Smoke-test the DB port override**

Run:
```bash
MEEPLETIME_DB_PORT=55432 task dev:db
docker ps --format '{{.Names}} {{.Ports}}' | grep meepletime-dev-db
task dev:db-stop
```
Expected: the `docker ps` line shows `0.0.0.0:55432->5432/tcp`.

- [ ] **Step 6: Commit**

```bash
git add Taskfile.yml
git commit -m "feat(tooling): overridable ports + dev:keycloak task"
```

---

### Task 3: Host bootstrap script + `setup:host` task

**Files:**
- Create: `scripts/setup-host.bash`
- Modify: `Taskfile.yml`

- [ ] **Step 1: Create the bootstrap script**

Create `scripts/setup-host.bash` with exactly this content:

```bash
#!/usr/bin/env bash
# scripts/setup-host.bash
#
# One-shot host bootstrap for running MeepleTime directly on the
# host (no dev-container). Installs project-local toolchains and
# seeds host-flavoured env files. Idempotent: existing env files are
# never overwritten. See docs/developer/host-run.md for the full
# host-run reference.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

KEYCLOAK_HOST="keycloak.127.0.0.1.nip.io"
REALM_URL="http://${KEYCLOAK_HOST}:8080/realms/meepletime"

echo "==> Ensuring uv is installed ..."
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

echo "==> Installing backend dependencies (uv sync) ..."
# uv fetches the project's pinned Python interpreter automatically.
(cd "${REPO_ROOT}/backend" && uv sync)

echo "==> Installing frontend dependencies (npm) ..."
export NVM_DIR="${NVM_DIR:-${HOME}/.nvm}"
if [[ -s "${NVM_DIR}/nvm.sh" ]]; then
    # nvm is not fully compatible with `set -u`.
    # shellcheck disable=SC1090
    set +u
    . "${NVM_DIR}/nvm.sh"
    nvm install --lts
    nvm use --lts
    set -u
else
    echo "==> nvm not found; using preinstalled node/npm ..."
fi
(cd "${REPO_ROOT}/frontend" && npm install)

echo "==> Installing pre-commit hooks ..."
(cd "${REPO_ROOT}" \
    && "${REPO_ROOT}/backend/.venv/bin/pre-commit" install)

# --- Warn about a dev-container-flavoured backend/.env -----------
BACKEND_ENV="${REPO_ROOT}/backend/.env"
if [[ -f "${BACKEND_ENV}" ]] && grep -q '@db:5432' "${BACKEND_ENV}"; then
    echo "WARNING: ${BACKEND_ENV} points at container DB 'db:5432'." >&2
    echo "         On the host use 'localhost'. Edit it, or override" >&2
    echo "         with a shell export of MEEPLETIME_DATABASE_URL" >&2
    echo "         (shell env beats the .env file)." >&2
fi

# --- Seed host-flavoured backend/.env (only if absent) ----------
if [[ ! -f "${BACKEND_ENV}" ]]; then
    echo "==> Creating host backend/.env ..."
    cat > "${BACKEND_ENV}" <<EOF
MEEPLETIME_DATABASE_URL=postgresql://meepletime:changeme@localhost:5432/meepletime
MEEPLETIME_OIDC_AUTHORITY=${REALM_URL}
MEEPLETIME_OIDC_AUDIENCE=meepletime-backend
MEEPLETIME_OIDC_ISSUER=${REALM_URL}
MEEPLETIME_APP_BASE_URL=http://localhost:5173
# Development-only auth. NEVER set these in production.
MEEPLETIME_DEV_SHARED_SECRET=changeme
MEEPLETIME_DEV_AUTH_ENABLED=true
EOF
fi

# --- Seed host-flavoured frontend/.env.local (only if absent) ---
FRONTEND_ENV="${REPO_ROOT}/frontend/.env.local"
if [[ ! -f "${FRONTEND_ENV}" ]]; then
    echo "==> Creating host frontend/.env.local ..."
    cat > "${FRONTEND_ENV}" <<EOF
VITE_OIDC_AUTHORITY=${REALM_URL}
VITE_OIDC_CLIENT_ID=meepletime-frontend
VITE_API_BASE_URL=http://localhost:8000
# Development-only in-app login (no Keycloak). Dev server only.
VITE_DEV_AUTH=true
EOF
fi

echo ""
echo "==> Host setup complete."
echo "    Start PostgreSQL : task dev:db"
echo "    Run migrations   : task migrate"
echo "    Start backend    : task backend"
echo "    Start frontend   : task frontend"
echo "    (Optional OIDC)  : task dev:keycloak"
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x scripts/setup-host.bash`

- [ ] **Step 3: Add the `setup:host` task**

Add to `Taskfile.yml`:

```yaml
  setup:host:
    desc: >-
      One-shot host bootstrap for running OUTSIDE the dev-container:
      installs project-local toolchains (uv/npm), pre-commit hooks,
      and seeds host-flavoured backend/.env + frontend/.env.local
      (dev-auth, localhost DB) when absent. Idempotent.
    cmd: bash scripts/setup-host.bash
```

- [ ] **Step 4: Static-check the script**

Run: `bash -n scripts/setup-host.bash`
Expected: no output, exit code 0 (syntax OK).

Run (if available): `shellcheck scripts/setup-host.bash`
Expected: no errors (the SC1090 on the nvm source is suppressed).

- [ ] **Step 5: Verify env seeding in isolation**

Run a dry seeding check that exercises only the env-writing logic
without installing anything, in a temp dir:
```bash
bash -c '
set -euo pipefail
tmp=$(mktemp -d)
REALM_URL="http://keycloak.127.0.0.1.nip.io:8080/realms/meepletime"
BACKEND_ENV="$tmp/.env"
cat > "$BACKEND_ENV" <<EOF
MEEPLETIME_DATABASE_URL=postgresql://meepletime:changeme@localhost:5432/meepletime
MEEPLETIME_DEV_AUTH_ENABLED=true
EOF
grep -q "localhost:5432" "$BACKEND_ENV" && echo "OK: host DB URL"
grep -q "DEV_AUTH_ENABLED=true" "$BACKEND_ENV" && echo "OK: dev-auth"
rm -rf "$tmp"
'
```
Expected: prints `OK: host DB URL` and `OK: dev-auth`. This confirms
the seeded values are host-flavored (no `@db:5432`).

- [ ] **Step 6: Verify `setup:host` is listed**

Run: `task --list`
Expected: output includes `setup:host`.

- [ ] **Step 7: Commit**

```bash
git add scripts/setup-host.bash Taskfile.yml
git commit -m "feat(tooling): add setup:host bootstrap for host runs"
```

---

### Task 4: AGENTS.md — "Running on the host" section

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add the new tasks to the Commands list**

In `AGENTS.md`, inside the ```bash command block under "## Commands"
(currently ending at `task db-shell`), add these lines after the
existing `dev:db-stop` line:

```bash
task setup:host       # one-shot host bootstrap (toolchains + env)
task dev:keycloak     # throwaway Keycloak for real-OIDC e2e on host
task dev:keycloak-stop # stop/remove the throwaway Keycloak
```

- [ ] **Step 2: Add the "Running on the host" section**

In `AGENTS.md`, immediately after the closing of the "## Commands"
section (before "## Authentication"), insert:

```markdown
---

## Running on the host (agents)

Coding agents should run the stack **directly on the host**, not
inside the dev-container (`.devcontainer/` is kept for human use).
See `docs/developer/host-run.md` for the full reference.

- **Bootstrap once:** `task setup:host` (installs uv/npm deps +
  pre-commit, seeds host-flavoured `backend/.env` and
  `frontend/.env.local` when absent).
- **Toolchains:** Python 3.14 via `uv` (project venv in
  `backend/.venv`), Node via `nvm`. Keep dependencies project-local;
  do not install runtimes via the host package manager. A wider
  scope is allowed only when a truly local install would explode
  complexity or hits a real technical constraint.
- **Backing services:** PostgreSQL via `task dev:db` (throwaway
  container). Keycloak is **not** needed for most work — default to
  dev-auth mode (`MEEPLETIME_DEV_AUTH_ENABLED=true` +
  `VITE_DEV_AUTH=true`, seeded by `setup:host`). Start Keycloak via
  `task dev:keycloak` only for explicit real-OIDC end-to-end tests.
- **Ports:** the defaults (backend `8000`, frontend `5173`, DB
  `5432`, Keycloak `8080`) are conventional. If one is taken, pick a
  free port via `MEEPLETIME_BACKEND_PORT`, `MEEPLETIME_FRONTEND_PORT`,
  `MEEPLETIME_DB_PORT`, or `MEEPLETIME_KEYCLOAK_PORT`, and update the
  dependent config (e.g. `VITE_API_BASE_URL`) to match.
- **Gotcha:** a dev-container-seeded `backend/.env` points the DB at
  `db:5432`, which is unreachable on the host. Use `localhost` (or a
  shell `export MEEPLETIME_DATABASE_URL=...`, which overrides the
  `.env` file). `setup:host` warns when it detects this.
```

- [ ] **Step 3: Verify the edits**

Run: `grep -n "Running on the host" AGENTS.md`
Expected: one match.

Run: `grep -n "setup:host" AGENTS.md`
Expected: at least two matches (Commands list + the new section).

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "docs(agents): document host-native run path in AGENTS.md"
```

---

### Task 5: Developer doc — host-run.md

**Files:**
- Create: `docs/developer/host-run.md`
- Modify: `docs/developer/index.md`

- [ ] **Step 1: Create the host-run reference**

Create `docs/developer/host-run.md` with this content:

```markdown
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

`task setup:host` prints a warning when it detects a container-flavoured
`backend/.env`.

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

| Service   | Default | Override env var              | Also update            |
|-----------|---------|-------------------------------|------------------------|
| Backend   | 8000    | `MEEPLETIME_BACKEND_PORT`     | `VITE_API_BASE_URL`    |
| Frontend  | 5173    | `MEEPLETIME_FRONTEND_PORT`    | `MEEPLETIME_APP_BASE_URL` |
| PostgreSQL| 5432    | `MEEPLETIME_DB_PORT`          | `MEEPLETIME_DATABASE_URL` |
| Keycloak  | 8080    | `MEEPLETIME_KEYCLOAK_PORT`    | OIDC authority in both env files |

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
```

- [ ] **Step 2: Link the doc from the developer index**

Read `docs/developer/index.md` to match its existing list/link style,
then add a link to `host-run.md` (Running on the host) alongside the
other developer-doc entries, using the same formatting as the
neighboring links.

- [ ] **Step 3: Verify**

Run: `test -f docs/developer/host-run.md && grep -n "host-run" docs/developer/index.md`
Expected: the file exists and the index references `host-run`.

- [ ] **Step 4: Commit**

```bash
git add docs/developer/host-run.md docs/developer/index.md
git commit -m "docs(developer): add host-run reference"
```

---

### Task 6: Annotate the dev-container as optional

**Files:**
- Modify: `.devcontainer/devcontainer.json`

- [ ] **Step 1: Add the note**

`devcontainer.json` is JSONC (it already contains `//` comments). Add
a comment immediately after the opening `{` and before the `"name"`
key:

```jsonc
{
  // NOTE: The dev-container is OPTIONAL and human-oriented. Coding
  // agents should run on the host instead — see
  // docs/developer/host-run.md and the "Running on the host" section
  // in AGENTS.md.
  // MeepleTime — FastAPI + Vue 3 + PostgreSQL + Keycloak
  "name": "meepletime",
```

- [ ] **Step 2: Verify the comment is present**

Run: `grep -n "OPTIONAL and human-oriented" .devcontainer/devcontainer.json`
Expected: one match.

- [ ] **Step 3: Commit**

```bash
git add .devcontainer/devcontainer.json
git commit -m "docs(devcontainer): note dev-container is optional for agents"
```

---

### Task 7: End-to-end verification (no dev-container)

This task confirms the whole path works on a clean host. It runs real
services, so it is a manual checkpoint rather than an automated test.

**Files:** none (verification only)

- [ ] **Step 1: Bootstrap**

Run: `task setup:host`
Expected: completes; `backend/.env` and `frontend/.env.local` exist
(or a warning is printed if a container-flavoured `.env` was present).

- [ ] **Step 2: Bring up DB + backend + frontend**

Run, each in its own shell:
```bash
task dev:db
task migrate
task backend
task frontend
```
Expected: migrations apply cleanly; backend serves on `:8000`;
frontend serves on `:5173`.

- [ ] **Step 3: Verify dev-auth login in a browser**

Open `http://localhost:5173`, use the dev-login picker to sign in.
Expected: login succeeds and the app loads circle data — with **no**
Keycloak running.

- [ ] **Step 4: Verify a port override**

Run:
```bash
MEEPLETIME_BACKEND_PORT=8001 task backend
```
Set `VITE_API_BASE_URL=http://localhost:8001` in
`frontend/.env.local`, restart `task frontend`, and confirm the SPA
reaches the relocated backend.
Expected: the app works against the backend on `:8001`.

- [ ] **Step 5: Tear down**

Run: `task dev:db-stop` (and `task dev:keycloak-stop` if used).
Expected: containers removed.

- [ ] **Step 6: Final review commit (if any fixes were needed)**

If steps surfaced fixes, commit them:
```bash
git add -A
git commit -m "fix(tooling): host-run e2e adjustments"
```

---

## Self-review

**Spec coverage:**
- AGENTS.md "Running on the host" section → Task 4. ✓
- `docs/developer/host-run.md` + index link → Task 5. ✓
- `dev:keycloak` / `dev:keycloak-stop` tasks → Task 2. ✓
- `setup:host` bootstrap (host-flavoured env, when absent) → Task 3. ✓
- Overridable ports (backend/frontend/db/keycloak) → Tasks 2 + doc
  table in Task 5. ✓
- `.devcontainer` annotation → Task 6. ✓
- Gotcha: dev-container `db:5432` env + warning + shell-override
  guidance → Task 3 (script warning) + Task 5 (doc). ✓
- Default dev-auth flow → Tasks 3, 4, 5. ✓
- Verification scenarios from the spec → Task 7. ✓

**Placeholder scan:** no TBD/TODO; every code/script/doc step shows
full content. ✓

**Type/name consistency:** task names (`setup:host`, `dev:keycloak`,
`dev:keycloak-stop`, `dev:db`, `dev:db-stop`), env vars
(`MEEPLETIME_BACKEND_PORT`, `MEEPLETIME_FRONTEND_PORT`,
`MEEPLETIME_DB_PORT`, `MEEPLETIME_KEYCLOAK_PORT`,
`MEEPLETIME_DATABASE_URL`, `MEEPLETIME_DEV_AUTH_ENABLED`,
`VITE_DEV_AUTH`, `VITE_API_BASE_URL`, `MEEPLETIME_APP_BASE_URL`), and
the container name `meepletime-dev-keycloak` are used consistently
across tasks. ✓
