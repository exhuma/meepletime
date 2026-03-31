# Keycloak theme assets

This folder contains Keycloak themes that can be mounted into
`/opt/keycloak/themes`.

Current theme:

- `themes/meepletime`

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
