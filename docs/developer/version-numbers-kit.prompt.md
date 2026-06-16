# Prompt: author a `module-version-numbers` instruction kit

This document is a **hand-off prompt for a coding agent**. Its goal is
to produce a new instruction kit (working name `module-version-numbers`)
in the external `instructions-exhuma` kit repository — *not* in this
application repo. It also records the versioning decisions MeepleTime
adopted, so the kit can be grounded in a concrete case.

Copy everything under "Prompt for the agent" into a fresh agent session
that has the `instructions-exhuma` MCP available.

---

## Background (the discussion to synthesize)

MeepleTime needed a coherent version-numbering scheme spanning a Python
backend, a TypeScript/Vite frontend, and Docker images on a private
registry. The reasoning that emerged:

- **Applications vs. libraries is the dividing line.**
  - *Applications* (deployed end-products: web apps, services, CLIs the
    user runs) gain little from semver. There is no downstream code
    importing them against a compatibility contract, so the
    major/minor/patch promise is noise. **Calendar versioning (calver,
    `YYYY.M.D`)** communicates the one thing that matters — *when* this
    build was cut.
  - *Libraries* — and, to a meaningful degree, *REST APIs* — are
    consumed by other code that relies on a compatibility contract.
    They should use **semver**, where the version number encodes
    backwards-compatibility intent (breaking / feature / fix).
- **Pre-releases follow semver semantics** regardless of scheme:
  `-alpha.N`, `-beta.N`, `-rc.N`, ordered
  `alpha < beta < rc < final`.
- **PEP440 ↔ semver common ground.** Python packaging requires PEP440;
  npm and OCI tooling require semver. There is no single string that is
  *canonical* in both, but the semver pre-release form is **accepted by
  PEP440**, which normalizes it:
  - semver `2026.6.15-alpha.1`  →  PEP440 canonical `2026.6.15a1`
  - semver `2026.6.15-beta.1`   →  PEP440 `2026.6.15b1`
  - semver `2026.6.15-rc.1`     →  PEP440 `2026.6.15rc1`
  - a final release `2026.6.15` is identical in both.
  No zero-padding of month/day (semver forbids leading zeros; PEP440
  strips them), matching the `YYYY.M.D` convention.
- **Store native, display uniform.** Keep each manifest in its
  ecosystem's canonical form (`package.json` semver, `pyproject.toml`
  PEP440), but pick one string — the semver form — to *report at
  runtime* across components, injected at build time, so the header,
  OpenAPI schema, and UI all show the identical value.
- **Container tags for a calver app.** Aliasing `{{major}}.{{minor}}`
  or `{{major}}` is meaningless under calver, and an unconditional
  `latest` hides the channel. Instead publish, per image:
  - an **immutable full-version tag** (e.g. `2026.6.15-alpha.1`), and
  - a **moving release-channel pointer**: `alpha` / `beta` / `rc` /
    `stable`, derived from the tag's pre-release identifier (no
    pre-release ⇒ `stable`).

### The MeepleTime discrepancy to call out

MeepleTime is an *application*, yet it currently applies calver to its
**entire** surface — including its REST API, where semver would
normally govern the compatibility contract with API clients. This is a
deliberate, known simplification to be revisited later. The kit must
make the **application-vs-library/API distinction explicit** and frame
all-calver-including-the-API as a conscious trade-off, not a default to
copy blindly.

### Relationship to existing kits

The kit **complements `module-release-metadata`** (which plumbs build
metadata — repo URL, commit, build time — into the frontend). That kit
has **no version field today**; the agent should file a gap (via the
MCP `check_existing_gap_issue` → `request_clarification_or_addition`
flow) to add a `VITE_APP_VERSION` field to `module-release-metadata`,
and the new kit should reference it rather than duplicate the plumbing.
It is also adjacent to `module-api-design` (REST) — cross-reference the
"REST APIs should use semver" point there.

---

## Prompt for the agent

> You are authoring a new instruction kit named `module-version-numbers`
> for the `instructions-exhuma` kit repository. Follow the repository's
> existing kit conventions (front-matter/manifest, trait declarations,
> changelog) — inspect a few existing kits first to match their shape.
>
> First, orient using the MCP: `list_available_traits` and `list_kits`
> to learn the vocabulary and avoid overlap; `get_kit` on
> `module-release-metadata` and `module-api-design` to align with and
> reference them. Do **not** hand-edit kit files outside the documented
> workflow.
>
> The kit must teach an agent to:
>
> 1. **Classify the artifact first.** Application (deployed product) ⇒
>    calver `YYYY.M.D`. Library or REST API (consumed against a
>    compatibility contract) ⇒ semver. State the rationale, not just the
>    rule.
> 2. **Apply pre-release identifiers** with semver semantics
>    (`-alpha.N` / `-beta.N` / `-rc.N`; ordering alpha < beta < rc <
>    final), for both schemes.
> 3. **Use the PEP440 ↔ semver common ground** when a project ships both
>    a Python package and a JS package: store each manifest in its
>    native canonical form (`pyproject.toml` PEP440 `…a1/b1/rc1`,
>    `package.json` semver `…-alpha.1`), keep them in lockstep, and
>    report one uniform semver-form string at runtime via build-time
>    injection. Include the normalization table and the no-zero-padding
>    rule.
> 4. **Tag containers for calver apps**: one immutable full-version tag
>    plus a moving channel pointer (`alpha`/`beta`/`rc`/`stable`) derived
>    from the tag; drop `{{major}}.{{minor}}`, `{{major}}`, and an
>    unconditional `latest`. Give a `docker/metadata-action` snippet
>    (`flavor: latest=false`, `type=semver,pattern={{version}}`, a
>    `type=raw` channel tag) and a shell channel-derivation step.
> 5. **Guard against drift** in CI: assert the release git tag matches
>    the version in every package manifest (accounting for the PEP440 ↔
>    semver normalization) and fail the build on mismatch.
> 6. **Expose the version at runtime**: a response header
>    (e.g. `X-<App>-Version`) and the OpenAPI `info.version` on the
>    backend; a non-intrusive, low-emphasis UI element on the frontend
>    (cross-reference `module-github-link` /
>    `module-release-metadata`).
>
> Include a short worked example using `2026.6.15` /
> `2026.6.15-alpha.1`. Explicitly cover the application-vs-library/API
> distinction and name the "calver applied to a REST API" case as a
> conscious trade-off (cite MeepleTime). Reference
> `module-release-metadata` and `module-api-design`, and **file a gap**
> to add a `VITE_APP_VERSION` field to `module-release-metadata` so the
> version rides the same frontend plumbing as commit/build-time.
>
> Declare sensible applicability traits (capabilities like
> `release-metadata` / `versioning`; contexts `tooling`, `backend`,
> `frontend`; no hard language requirement, since the rules are
> stack-agnostic). Add a changelog entry for the initial `v1`.
