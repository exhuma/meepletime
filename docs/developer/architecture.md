# Architecture

This repository is a monorepo with separate runtime services.

## Repository Structure

- `apps/frontend` contains the Vue + Vuetify UI.
- `apps/backend` contains the FastAPI API service.
- `apps/nginx` contains nginx static and reverse-proxy configuration.
- `deploy/compose` contains local stack scaffolding.
- `contract.md` is the product and behavior source of truth.

## Runtime Boundaries

- FastAPI and nginx run in separate containers.
- Each container runs exactly one long-running process.
- `/data` is a shared mounted volume used as the persistent source of truth.
- FastAPI must not serve large static documentation files directly.

## Backend Layering

### API Layer

- Owns HTTP input/output, status codes, and request validation.
- Performs authentication and authorization checks.
- Calls service-layer functions for business operations.
- Must not perform direct filesystem operations.

### Service Layer

- Owns business rules and mutation workflows.
- Calls storage abstraction methods for all filesystem operations.
- Implements atomic write behavior and immutability guarantees.
- Uses resolver functions for all version alias and locale resolution.

### Storage Layer

- Encapsulates filesystem access under `/data`.
- Implements namespace, project, version, and locale operations.
- Enforces atomic rename and concurrency-safe creation semantics.
- Exposes only the contract-defined storage interface.

## Frontend Boundaries

- UI must rely only on REST APIs.
- UI must not infer or depend on filesystem layout details.
- Docs are rendered by iframe against nginx static routes.
- Version/locale selection behavior must follow API resolution rules.

## nginx Authorization Gate

Static documentation requests must not bypass access control.
The flow is:

1. Browser requests `/{ns}/{project}/{version}/{locale}/...`.
2. nginx matches the static-docs location and invokes
   `auth_request /internal/auth`.
3. nginx proxies a subrequest to `GET /api/auth` on FastAPI.
   The subrequest inherits all incoming headers (including
   `Authorization` when present) and cookies (including the
   `session` cookie set by `POST /api/auth/session`) by default.
   nginx also sets `X-Original-URI` to the original request path.
4. FastAPI extracts the namespace from `X-Original-URI` and
   resolves credentials: `Authorization` header first, then the
   `session` cookie, then unauthenticated. The namespace ACL is
   evaluated and FastAPI returns 200, 401, or 403.
5. If 200, nginx serves the static file from `/data`.
   Otherwise nginx returns the error status to the browser.

The `session` cookie path is necessary because the SPA renders
docs inside a `<iframe :src="...">`. Browser iframe navigations
cannot carry custom `Authorization` headers; the cookie is
attached automatically instead. See the *Browser Token Storage —
Two-Store Design* section in `security.md` for full details.

The `/internal/auth` location is declared `internal` in nginx
and is unreachable by external clients.

## Prohibited Architectural Drift

- No direct filesystem writes in API handlers.
- No bypass of resolver for `latest` and locale fallbacks.
- No database, ORM, queue, or background-worker introduction in v1.
- No upstream/downstream split assumptions in repository design.
- No static documentation served by nginx without passing
  through the FastAPI `auth_request` gate.
