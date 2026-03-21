# Developer Guide

Use this guide when working on this repository.

## Read in order

1. [Invariants](invariants.md)
2. [Architecture](architecture.md)
3. [Security](security.md)
4. [Code Style](code-style.md)

## Scope

These documents are aligned to `contract.md` and intentionally
avoid project-external conventions.

## Documentation Map

- **[User guide](../user/index.md)** — UI and API usage in
  production.
- **[Operator guide](../operator/index.md)** — installation,
  environment variables, OIDC, and ACL management.

## Testing Conventions

- Every test function must have a docstring starting with
  "Ensure…" that describes the behaviour under test.
- Test files should have a module-level docstring.
- Run tests with `task test:backend` (requires `uv` and deps).

## Coding Conventions

- All functions must have a docstring.
  - Route handlers: Markdown docstring for API consumers,
    separated from internal notes by a line containing `---`.
  - Internal Python code: Sphinx-style (`:param:`, `:returns:`,
    `:raises:`).
  - TypeScript: JSDoc style.
- Every source file must have a module-level docstring.
- Code must be fully type-annotated; avoid bare `dict`.
- Maximum line length: 80 characters.
- Environment variables use the `DOCROOT_` prefix and are
  declared in `app.settings.Settings`.

