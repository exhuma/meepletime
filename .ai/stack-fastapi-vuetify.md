# Agent instructions: stack-fastapi-vuetify

This file defines mandatory guard-rails for AI coding agents working
on any project built on the FastAPI + Vue 3 + Vuetify 4 stack.

Load this file at the start of every session that touches backend or
frontend code. Treat every rule here as non-negotiable unless the
project's `contract.md` explicitly overrides it.

---

## Start here: contract.md

Look for `contract.md` at the repository root before making any
change.

- If it exists: never contradict it. If a requested change conflicts
  with `contract.md`, say so and stop.
- If it is absent: alert the developer. Do not proceed with
  feature implementation until the file exists or the developer
  explicitly waives the requirement.

---

## Agent behaviour

- Make minimal, focused changes. Do not refactor code that is not
  in the scope of the current task.
- Security and correctness take priority over convenience.
- Never bypass authentication or authorisation checks.
- Ask one clarifying question rather than guessing at ambiguous
  requirements.
- When changing observable behaviour (API shape, UI flow, data
  model), update the relevant documentation in the same patch.

---

## Line-length limit

80 characters maximum for all files: Python, TypeScript, Markdown,
RST, YAML, TOML. This is enforced by linters; do not suppress
warnings.

---

## Tooling

### Backend

- `uv` is the only package manager. Never run `pip install`.
- Add dependencies with `uv add <package>`.
- Remove dependencies with `uv remove <package>`.
- `pyproject.toml` is the source of truth for dependencies and
  Python version. Do not edit `requirements.txt` directly.
- Virtual environment is always at `backend/.venv`.

### Frontend

- `npm` is the package manager.
- Never install packages with `yarn`, `pnpm`, or `bun`.
- `package.json` is the source of truth.

### Secrets

- Never commit `.env`. Always commit `.env.example` with
  placeholder values and a comment for every variable.
- `.env.local` is gitignored and holds developer-local overrides.

---

## Python / FastAPI rules

### Layering

Strict three-layer hierarchy — calls only go downward:

```
routers/      HTTP concerns: input validation, status codes,
              auth checks, calling service functions.
services/     Business logic: orchestration, rules, side effects.
              Calls storage or DB layer. No HTTP concepts.
storage/ or   Filesystem or database access only. No business
models/       logic. No HTTP concepts.
```

API handlers must not perform direct filesystem or database
operations. Business logic must not live in routers.

### Configuration

- All configuration comes from a `pydantic-settings` `Settings`
  class (typically `app/config.py`).
- Every environment variable must appear as a named field on
  `Settings`. Never read `os.environ` or `os.getenv` directly.
- All environment variables must be prefixed with the application
  name to avoid collisions in shared environments. Set this with
  `SettingsConfigDict(env_prefix="MYAPP_")`. For this project
  the prefix is `MEEPLETIME_`.
- `Settings` is instantiated once and injected via
  `Depends(get_settings)` or imported as a module-level singleton.

### Type hints

- Every function and method must have full type annotations,
  including return type.
- Use `from __future__ import annotations` for forward references.
- Avoid `Any` unless there is no safe alternative; add a comment
  explaining why.

### Docstrings

- Every Python source file: module-level docstring explaining
  what the file does.
- Every function: Sphinx style (`:param:`, `:returns:`,
  `:raises:`).
- **Format**: triple-double-quotes only. Opening `"""` must be
  on its own line with nothing else. Closing `"""` must be on
  its own line.

  ```python
  def create_token(subject: str) -> str:
      """
      Issue a short-lived access JWT.

      :param subject: User identifier (UUID as string).
      :returns: Signed JWT string.
      """
  ```

- Route handler docstrings have two sections separated by a bare
  `\r` character (carriage return, not `---`):
  - Before `\r`: user-facing API documentation in Markdown.
  - After `\r`: internal developer notes for the team.
- Every test function: docstring starting with "Ensure …" that
  describes the behaviour being verified.

### Error handling

- Define domain-specific exception classes for every error
  condition (e.g. `UserNotFoundError`, `CircleCapacityError`).
  Do not use Python built-ins (`ValueError`, `KeyError`,
  `TypeError`) as error signals that cross layer boundaries.
- Register `@app.exception_handler` only for domain exception
  classes, never for built-in exceptions.
- Never silently catch broad exceptions (`except Exception` with
  no re-raise or logging).
- HTTP error responses use explicit `HTTPException` with
  intentional status codes. Do not default to 500 for client
  errors.
- Log at `WARNING` or above for errors that cross service
  boundaries.

  ```python
  # domain exception
  class UserNotFoundError(Exception):
      def __init__(self, user_id: str) -> None:
          """
          :param user_id: The ID that was not found.
          """
          self.user_id = user_id

  # handler registered at app factory time
  @app.exception_handler(UserNotFoundError)
  async def user_not_found_handler(
      request: Request,
      exc: UserNotFoundError,
  ) -> JSONResponse:
      """
      Map UserNotFoundError to HTTP 404.
      """
      return JSONResponse(
          status_code=404,
          content={"detail": "User not found"},
      )
  ```

### Application factory

The FastAPI `app` object must be created inside a factory function,
not at module level. Exception handlers, middleware, and routers
are registered inside the factory.

```python
# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

def create_app() -> FastAPI:
    """
    Build and return the configured FastAPI application.

    Registers routers, exception handlers, and middleware.
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # startup work here
        yield
        # shutdown work here

    app = FastAPI(lifespan=lifespan)

    from app.routers import auth, items
    app.include_router(auth.router)
    app.include_router(items.router)

    from app.errors import register_handlers
    register_handlers(app)

    return app

app = create_app()
```

No router, middleware, or exception handler may be registered
outside the factory function.

### Prohibited patterns

- `global` keyword — use dependency injection or
  `functools.lru_cache` instead.
- `Base.metadata.create_all()` — schema is managed by Alembic
  (see `module-database-postgresql`).
- Raw DDL strings (`CREATE TABLE`, `ALTER TABLE`) in Python code.
- Hard-coded secrets, passwords, or connection strings.
- Import statements inside function bodies. All imports must be at
  module top level. If a circular import would result, restructure
  the modules; do not use in-function imports as a workaround.

### Testing (pytest)

- Tests live in `backend/tests/`.
- Use `pytest-asyncio` for async route tests.
- Every test function has a docstring starting with "Ensure …".
- Use fixtures for database sessions and HTTP client setup.
- Never test against a production database.

---

## TypeScript / Vue 3 / Vuetify 4 rules

### Component authoring

- Vue 3 Composition API with `<script setup lang="ts">` only.
  Options API is prohibited.
- All files under `src/` must be `.ts` or `.vue`. No `.js` files.
- Props and emits must be typed explicitly.

### Component design

- Prefer **pure components**: a component that communicates only
  via `props` (input) and `emits` (output) with no side effects.
  These are the easiest to test, document, and reuse.
- `provide`/`inject` and composables are allowed. Use them when
  prop-drilling would span more than two component levels.
  Add a brief comment explaining why when you choose these
  patterns over plain props.
- Be liberal creating components. A component used once is
  still worth creating if it makes the parent file shorter and
  more readable. Target files under ~150 lines.

### State management

- No Pinia, Vuex, or any global state library.
- Shared state lives in module-level singleton composables:
  a `ref` or `reactive` defined at module scope, returned from
  a `use*` function.

### HTTP client

- No axios. Use the vanilla `fetch` API.
- All API calls go through a central `api/index.ts` module that
  provides `api.get`, `api.post`, `api.put`, `api.delete`.
- That module exposes an `ApiError` class with `status: number`
  and `data: unknown` fields.
- It exposes `setUnauthorizedHandler(fn: () => void)` for
  global 401 handling (redirects to login).
- It exposes a `TokenProvider` interface and `setTokenProvider`
  function as the authentication seam:

  ```typescript
  export interface TokenProvider {
    getToken(): string | null
  }
  export function setTokenProvider(p: TokenProvider): void
  ```

  The default implementation reads from `localStorage`. When the
  OIDC module is active, bootstrap code calls `setTokenProvider`
  with a `oidc-client-ts`-backed implementation. This seam must
  be present even in projects that do not yet use OIDC.

### Dependencies

- Every new npm dependency requires justification. Prefer web
  platform APIs over libraries where the implementation is
  straightforward (< ~50 lines).
- Do not introduce CSS utility frameworks (Tailwind, UnoCSS, etc.).
  Use vanilla CSS or Vuetify's built-in spacing/typography helpers.

### Vuetify theming

- All colours come from the Vuetify theme. Never use hex literals,
  `rgb()`, `rgba()`, or named CSS colours in templates or
  component `<style>` blocks.
- Use `color="semantic-name"` on Vuetify components.
- Use `rgb(var(--v-theme-semantic-name))` in scoped CSS.
- Named Vuetify utility classes like `text-medium-emphasis`
  are acceptable; `text-grey`, `text-white`, `text-black` are not.
- Font families are declared in the theme's `variables` block in
  `main.ts`. Never set `font-family` in CSS or inline styles.
- Theme tokens for `light` and `dark` must both be populated.

### Testing (vitest)

- Tests live in `frontend/tests/`. Mirror the `src/` directory
  structure inside `tests/` (e.g. `tests/composables/auth.test.ts`
  for `src/composables/auth.ts`).
- Test composables and utility logic with vitest.
- Mock API calls with `vi.fn()` or `vi.spyOn`; never make real
  HTTP calls in tests.

---

## Deployment

### Docker Compose

- `docker-compose.yml` at the repository root is the canonical
  local and production stack definition.
- Each service runs exactly one long-running process.
- Services must have a `healthcheck` stanza.
- Secrets are passed via environment variables, never baked into
  images.

### Dockerfiles

Every Dockerfile must be multi-stage:

```
Stage 1 (build): install all dependencies, compile/build.
Stage 2 (runtime): copy only the built artefacts and runtime
                   dependencies into a slim base image.
```

Always use the current latest stable runtime image tag available
at the time of scaffolding. Do not copy pinned version tags from
these example patterns; resolve the actual latest tag first.

Backend pattern:

```dockerfile
# Stage 1 — build
FROM python:slim AS build
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .

# Stage 2 — runtime
FROM python:slim
WORKDIR /app
COPY --from=build /app/.venv .venv
COPY --from=build /app/app ./app
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Frontend pattern:

```dockerfile
# Stage 1 — build
FROM node:slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2 — runtime
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

- Do not mount `node_modules` or `.venv` from the host into
  runtime containers.
- Port convention (internal): backend `8000`, frontend `80`.
- The backend must expose a `GET /health` endpoint that returns
  `{"status": "ok"}`.

---

## Dev container

Every project must include `.devcontainer/devcontainer.json` and
`.devcontainer/docker-compose.yml`.
Agents must create or update both files when scaffolding a project
that uses a database or identity provider.

### Structure

Use the `dockerComposeFile` pattern — not `image` + `runServices`.
The docker-compose file defines all sidecar services (db, keycloak)
and a `devcontainer` service that VS Code attaches to.

```
.devcontainer/
  devcontainer.json       — VS Code attachment config
  docker-compose.yml      — full sidecar stack
  init.bash               — post-create dependency installer
deploy/
  dev/
    keycloak-realm.json   — importable Keycloak realm
```

### devcontainer.json reference

```jsonc
{
  "name": "<project-name>",
  "dockerComposeFile": "docker-compose.yml",
  "service": "devcontainer",
  "workspaceFolder": "/workspace",
  "postCreateCommand": "bash .devcontainer/init.bash",
  "forwardPorts": [8000, 5173, 5432, 8080],
  "portsAttributes": {
    "8000": { "label": "Backend API" },
    "5173": { "label": "Frontend (Vite)" },
    "5432": { "label": "PostgreSQL" },
    "8080": { "label": "Keycloak" }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "Vue.volar",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        "python.defaultInterpreterPath":
          "${workspaceFolder}/backend/.venv/bin/python",
        "typescript.tsdk":
          "frontend/node_modules/typescript/lib",
        "editor.formatOnSave": true
      }
    }
  }
}
```

### docker-compose.yml reference

```yaml
version: "3.9"

services:

  devcontainer:
    image: mcr.microsoft.com/devcontainers/python:3.12
    volumes:
      - ..:/workspace:cached
    command: sleep infinity
    extra_hosts:
      - "keycloak.127.0.0.1.nip.io:host-gateway"
    depends_on:
      db:
        condition: service_healthy
      keycloak:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: <project>
      POSTGRES_USER: <project>
      POSTGRES_PASSWORD: changeme
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U <project>"]
      interval: 5s
      timeout: 5s
      retries: 10

  keycloak:
    image: quay.io/keycloak/keycloak:26.5
    command: start-dev --import-realm
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD: admin
      KC_HOSTNAME: keycloak.127.0.0.1.nip.io
      KC_HTTP_PORT: "8080"
      KC_HEALTH_ENABLED: "true"
    volumes:
      - ../deploy/dev/keycloak-realm.json:/opt/keycloak/data/import/<project>-realm.json:ro
    ports:
      - "8080:8080"
    healthcheck:
      test:
        - CMD
        - bash
        - -c
        - >-
          exec 3<>/dev/tcp/localhost/8080 &&
          printf 'GET /realms/<realm> HTTP/1.0\r\nHost: localhost\r\n\r\n' >&3 &&
          grep -q '"realm":"<realm>"' <&3
      interval: 10s
      timeout: 5s
      retries: 20
      start_period: 30s

volumes:
  postgres_data:
```

### Keycloak nip.io hostname strategy

With a 2-tier OIDC setup (public client + resource server), the
`iss` claim in access tokens must resolve identically from:

- The **browser** (Vue frontend, running on the developer's host)
- The **backend container** (FastAPI, validating tokens inside
  the devcontainer network)

Use `keycloak.<project-ip>.nip.io` as the Keycloak hostname.
`nip.io` is a free wildcard DNS service: any name of the form
`<label>.<A>.<B>.<C>.<D>.nip.io` resolves to the IPv4 address
`A.B.C.D`. The canonical dev address is `127.0.0.1`, so:

```
keycloak.127.0.0.1.nip.io  →  127.0.0.1  (localhost)
```

The frontend reaches Keycloak on port 8080 via localhost (port
forwarded by the devcontainer). The backend container resolves
the same hostname to the Docker host via the `extra_hosts` entry
`keycloak.127.0.0.1.nip.io:host-gateway` in the devcontainer
service. Both paths arrive at the same Keycloak, so the `iss`
claim is consistent and JWKS validation succeeds.

Set `KC_HOSTNAME` to the nip.io address and set the backend's
`OIDC_AUTHORITY` / `OIDC_ISSUER` and the frontend's
`VITE_OIDC_AUTHORITY` to `http://keycloak.127.0.0.1.nip.io:8080/realms/<realm>`.

### Keycloak healthcheck

The slim Keycloak image does not include `curl`. Use a raw TCP
socket check instead:

```yaml
healthcheck:
  test:
    - CMD
    - bash
    - -c
    - >-
      exec 3<>/dev/tcp/localhost/8080 &&
      printf 'GET /realms/<realm> HTTP/1.0\r\nHost: localhost\r\n\r\n' >&3 &&
      grep -q '"realm":"<realm>"' <&3
  interval: 10s
  timeout: 5s
  retries: 20
  start_period: 30s
```

This opens a raw TCP connection to port 8080, sends a minimal
HTTP/1.0 request, and checks that the realm name appears in the
JSON response.

### init.bash rules

- `postCreateCommand` must always point to
  `.devcontainer/init.bash`.
- Run `uv sync` in `backend/` and `npm ci` in `frontend/`.
- Seed `backend/.env` and `frontend/.env.local` with nip.io
  OIDC URLs on first run (idempotent — skip if files exist).
- Never commit `.env` or `.env.local`. Use `.env.example` as the
  canonical variable reference only.
- Forward port `5432` only when the database module is active.

