# Style Invariants

- Maximum line length is 80 characters.
- Markdown and RST files must respect the 80-character line-length
  limit.
- Keep changes minimal and focused on the requested scope.
- Preserve existing naming and structure unless change is required.
- Do not introduce unrelated refactors in the same patch.
- Keep API and UI terminology aligned with `contract.md`.
- Prefer explicit, descriptive names over abbreviations.
- Do not add inline comments unless needed for non-obvious logic.

## Docstring Rules

- Every source file must have a module-level docstring explaining
  what the file does.
- Every Python function must have a docstring.
  - Route handlers: audience is the API user; use Markdown.
    Separate internal developer notes with a line containing `---`.
  - All other Python: Sphinx style (`:param:`, `:returns:`,
    `:raises:`).
  - TypeScript: JSDoc style.
- Every test function must have a docstring starting with
  "Ensure…" that describes the behaviour being verified.

## Environment Variables

All environment variables must use the `DOCROOT_` prefix and be
declared as fields in `app.settings.Settings`. Never read
environment variables directly via `os.environ` or `os.getenv`.

