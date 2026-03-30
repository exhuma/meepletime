# AI Assistant Rules

Before generating or modifying files, load **every** instruction
kit listed below in order. All rules in those kits are
non-negotiable unless `contract.md` explicitly overrides them.
Correctness and security take priority over convenience.

---

## Instruction files

Load these files at the start of every session that touches
backend or frontend code:

1. `stack-fastapi-vuetify` — core stack rules (always)
2. `module-auth-oidc` — OIDC general rules (Keycloak, Option A)
3. `module-auth-oidc-python` — backend token validation
4. `module-auth-oidc-vue` — frontend OIDC flow (PKCE)
5. `module-database-postgresql` — PostgreSQL / Alembic
6. `module-code-style-python` — Python style and linting

Optional (recommended):

7. `module-dev-tooling-taskfile` — Taskfile conventions
8. `module-docs-sphinx` — Sphinx documentation

---

## Task-scoped applicability

The baseline list above remains mandatory whenever backend or
frontend code is touched. Use the following as an additional
selection rule so agents do not drift into loading only the most
recently edited part of the stack.

### Backend-only tasks

Still load the full mandatory baseline, then also consider:

- `module-fastapi` — backend architecture, dependency usage,
  error handling, and endpoint composition
- `module-api-design` — HTTP semantics, status codes, pagination,
  and response consistency
- `module-observability-healthz` — health probes and operational
  readiness checks when the task is ops-facing

### Frontend-only tasks

Still load the full mandatory baseline, then also consider:

- `module-vue-vuetify` — Vue 3 + Vuetify implementation rules
- `module-api-design` — request/response expectations shared with
  the backend
- `module-release-metadata` — only when exposing build/version
  metadata in the frontend

### Cross-cutting or ops tasks

Prefer adding these on top of the baseline when relevant:

- `module-dev-tooling-taskfile` — local developer workflow and
  task automation
- `module-observability-healthz` — live/readiness checks and
  operational probes
- `module-library-preferences` — when choosing or replacing
  dependencies

### Avoiding false narrowing

- Do not infer that frontend kits are no longer applicable merely
  because the most recent changes were backend-only.
- Do not infer that backend kits are optional merely because a task
  touches only docs or tooling; they may still constrain behavior.
- Use `contract.md` and this file as the primary source of truth
  when kit selection and recent edit history disagree.

---

## Authentication strategy

Option: **A — Keycloak (self-hosted OIDC)**
Providers configured inside Keycloak: TBD
GitHub login: out of scope
Local password login: removed — do not re-introduce

Two Keycloak clients are used: `meepletime-frontend` (public OIDC
client for PKCE flow) and `meepletime-backend` (bearer-only resource
server for audience claim propagation). See `module-auth-oidc`.

---

## Non-negotiable

- If `contract.md` is absent, alert the developer before
  proceeding with any feature work.
- Do not edit `contract.md` unless explicitly asked.
- Keep implementation aligned with `contract.md`.
- Do not implement features excluded by the contract.
- Never bypass authentication or authorisation checks.

---

## Agent behaviour

- Prefer minimal, focused changes.
- Update documentation when behaviour or architecture changes.
- Add tests for security-sensitive logic when implementation
  exists.
- Do not introduce project-specific assumptions not present in
  `contract.md`.

