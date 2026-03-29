# GitHub Copilot instructions

Read `AGENTS.md` at the repository root before suggesting or
generating any code. All rules defined there and in the
instruction files it references are mandatory.

Key points:

- Load all MCP instruction kits listed in `AGENTS.md`.
- Never contradict `contract.md`.
- Authentication is OIDC via Keycloak (Option A). Do not suggest
  local password authentication patterns.
- 80-character line limit applies to all files.
- Follow the application-factory pattern for FastAPI.
- Vue components must use `<script setup lang="ts">`. No Options
  API, no `.js` files in `src/`.
