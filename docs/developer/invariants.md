# Invariants

These rules are mandatory and derive from `contract.md`.

## Scope Invariants

- Do not implement features explicitly excluded by the contract.
- Keep the service split: FastAPI API service and nginx static/reverse-proxy
  service in separate containers.
- Keep one long-running process per container.
- Keep `/data` as the only authoritative persistent data source.
- Do not add a database, ORM, or background workers.

## Layering Invariants

- API handlers own HTTP concerns only.
- Business logic and filesystem writes belong in backend services.
- API handlers must not perform direct filesystem operations.
- All filesystem operations must go through the storage abstraction.
- Version resolution must always go through `resolve_version(...)`.

## Data and Immutability Invariants

- Storage path model must follow the locale-aware contract layout.
- Version+locale artifacts are immutable once created.
- Writes must be atomic; no partial version visibility.
- `metadata.toml` is system-generated and not trusted from uploaded archives.
- `latest` is a symlink alias and must be updated atomically.

## Locale Invariants

- Locale is mandatory for uploads and resolution.
- Locale format is two lowercase letters.
- Fallback order is fixed: requested locale, then `en`, then any available
  locale, then `404`.

## Security Invariants

- Authentication is stateless JWT validation via JWKS.
- Write operations require valid JWT and namespace ACL write permission.
- Public read behavior is controlled only by namespace ACL.
- Upload ZIP validation must reject traversal and symlink entries.
- Upload validation must enforce extracted size and file-count limits.
- Uploaded documentation must contain top-level `index.html`.

## Concurrency Invariants

- Concurrent uploads to different projects must be supported.
- Concurrent uploads to same project for different versions/locales
  must be supported.
- Two uploads must never create the same version+locale artifact.

## Code Quality Invariants

- Every test function must have a docstring starting with "Ensure…".
- Every source file must have a module-level docstring.
- Every function must have a docstring.
- All environment variables must use the `DOCROOT_` prefix and be
  declared in `app.settings.Settings`.
- The `global` keyword must not be used; use dependency injection
  or `functools.lru_cache` instead.
