# Keycloak theme assets

This folder contains Keycloak themes that can be mounted into
`/opt/keycloak/themes`.

Current theme:

- `themes/meepletime`

## Theme maintenance

Colours and fonts come from the shared design tokens in
`frontend/src/theme/tokens.ts` (the same source the app and email
templates use). They are baked into the theme's `brand-tokens.css`
(login and account) by a generator, so the Keycloak pages stay in
sync with the app skin.

- To change colours/fonts: edit `frontend/src/theme/tokens.ts`, then
  run `task build:keycloak` and commit the regenerated
  `brand-tokens.css` files. Do not hand-edit `brand-tokens.css` — it
  is generated.
- To change structure/styling: edit the login/account templates
  (`*.ftl`) and `login.css` / `account.css` directly under
  `themes/meepletime`. These reference the tokens via `--mt-*` CSS
  variables (e.g. `var(--mt-font-base)`).

## Local dev-container usage

The dev-container Keycloak service mounts this folder in
`.devcontainer/docker-compose.yml`:

- host: `../assets/keycloak/themes`
- container: `/opt/keycloak/themes`

The development command disables theme caching so template and CSS
changes are visible after refresh.

## Production usage

Mount `assets/keycloak/themes` (or copy its contents during image
build) into `/opt/keycloak/themes` on your production Keycloak
container.

Set the realm login theme to `meepletime` in either:

- realm import JSON (`"loginTheme": "meepletime"`), or
- Keycloak admin UI: Realm settings -> Themes -> Login theme.
