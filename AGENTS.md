# AI Assistant Rules

Before generating or modifying files, load **every** instruction
file listed below in order. All rules in those files are
non-negotiable unless `contract.md` explicitly overrides them.
Correctness and security take priority over convenience.

---

## Instruction files

Load these files at the start of every session that touches
backend or frontend code:

1. `.ai/stack-fastapi-vuetify.md` — core stack rules (always)
2. `.ai/module-auth-oidc.md` — OIDC authentication (Keycloak,
   Option A)
3. `.ai/module-database-postgresql.md` — PostgreSQL / Alembic
4. `.ai/module-docs-sphinx.md` — Sphinx documentation

---

## Authentication strategy

Option: **A — Keycloak (self-hosted OIDC)**
Providers configured inside Keycloak: TBD
GitHub login: out of scope
Local password login: removed — do not re-introduce

Two Keycloak clients are used: `meepletime-frontend` (public OIDC
client for PKCE flow) and `meepletime-backend` (bearer-only resource
server for audience claim propagation). See `module-auth-oidc.md`.

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

