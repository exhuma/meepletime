# Appendix: The MeepleTime Keycloak theme

> **Optional, nice-to-have.** MeepleTime works with any compliant OIDC
> provider and does not require this theme. It is offered purely as a
> convenience for operators who run [Keycloak](https://www.keycloak.org/)
> and want the login and account pages to match the MeepleTime look
> (the warm "Warmer Dark" charcoal-and-terracotta skin). Nothing in the
> app or the backend depends on it.

## What the artifact is

A standard Keycloak theme directory, versioned in this repository at:

- `assets/keycloak/themes/meepletime`

It provides two theme types:

- **login** — standalone FreeMarker templates (`login/*.ftl`) and
  `login/resources/css/`.
- **account** — a custom `account/index.ftl` shell on top of
  `keycloak.v3`, so branding and page framing change without forking
  the React account-console bundle.

The directory is the deliverable. It is committed in its final,
ready-to-use form — there is **no build step required to consume it**.
Drop it into a Keycloak instance and activate it (below).

## How it stays in sync with the app

Colours and fonts come from the app's single source of truth,
`frontend/src/theme/tokens.ts` (the same tokens that drive the Vue SPA
and the email templates). A small generator bakes those tokens into the
theme's `brand-tokens.css` (one copy for `login`, one for `account`):

```sh
task build:keycloak   # regenerates both brand-tokens.css files
```

The generated `brand-tokens.css` files are committed alongside the
theme, so operators never need a Node toolchain — the build step only
matters to contributors changing the MeepleTime palette. Templates,
layout CSS, and the favicon/logo are hand-authored and reference the
generated tokens through `--mt-*` CSS variables.

> Do not hand-edit `brand-tokens.css`; it is generated. To change
> colours or fonts, edit `tokens.ts` and re-run `task build:keycloak`.

## Adding the theme to Keycloak

Pick whichever fits how you run Keycloak. In all cases the theme must
end up under the container's `/opt/keycloak/themes/meepletime`.

### Option A — mount the directory (simplest)

Bind-mount the theme into the standard themes directory. Docker
Compose:

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:26.5
    volumes:
      - ./assets/keycloak/themes:/opt/keycloak/themes:ro
```

Kubernetes: ship the directory as a `ConfigMap` / mounted volume at the
same path. This is also how the dev-container and `task dev:keycloak`
wire it up locally.

### Option B — bake it into a custom image

Copy the theme during your image build so no runtime mount is needed:

```dockerfile
FROM quay.io/keycloak/keycloak:26.5
COPY assets/keycloak/themes /opt/keycloak/themes
```

### Option C — package as a provider JAR

For distribution independent of this repo, package the theme as a
Keycloak theme JAR and drop it in `/opt/keycloak/providers/`:

```
meepletime-theme.jar
├── META-INF/keycloak-themes.json
└── theme/meepletime/
    ├── login/...
    └── account/...
```

`META-INF/keycloak-themes.json`:

```json
{ "themes": [ { "name": "meepletime", "types": ["login", "account"] } ] }
```

Build it from the repo root, then rebuild the Keycloak provider cache:

```sh
( cd assets/keycloak && jar -cf /tmp/meepletime-theme.jar \
    -C . META-INF themes/meepletime )   # see note below
# place the JAR in /opt/keycloak/providers/ and run:
/opt/keycloak/bin/kc.sh build
```

> The JAR's internal layout must be `theme/<name>/...`, so when packaging
> you typically stage `assets/keycloak/themes/meepletime` as
> `theme/meepletime` plus a `META-INF/keycloak-themes.json`. The mount
> options above avoid this repackaging entirely and are recommended
> unless you specifically need a self-contained JAR.

## Activating the theme

Once the files are in place, set the realm's themes to `meepletime`:

- **Realm import JSON** — `"loginTheme": "meepletime"` and
  `"accountTheme": "meepletime"` (this repo's
  `deploy/dev/keycloak-realm.json` already does this for the
  `meepletime` realm), **or**
- **Admin UI** — Realm settings → Themes → *Login theme* and
  *Account theme* → `meepletime`.

## Notes

- **Caching.** Keycloak caches themes by default, which is what you want
  in production. For local theme work, disable it with
  `--spi-theme-cache-themes=false --spi-theme-cache-templates=false`
  (the dev tooling already does).
- **Account console secure context.** The Keycloak account console is a
  React app that calls the account REST API and uses the Storage Access
  API; browsers only permit that in a **secure context**. Serve Keycloak
  over HTTPS (or via `http://localhost` / `http://127.0.0.1`) — over
  plain HTTP on a non-localhost hostname the account console renders the
  themed shell but its data panel fails to load.
- See the [Keycloak appendix](keycloak.md) for the full realm/client
  walkthrough and the production checklist.
