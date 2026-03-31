# Keycloak Operator Runbook

This document describes how to configure Keycloak as the
identity provider for MeepleTime.

## Overview

MeepleTime uses Keycloak (self-hosted OIDC, Option A).

- The Vue frontend is a **public OIDC client**.  It performs the
  authorization-code + PKCE flow and holds tokens in the browser.
  There is no in-app login form.
- The FastAPI backend is a **stateless resource server**.  It
  validates bearer tokens on every request using Keycloak's JWKS
  endpoint.  It never participates in the OIDC flow.
- `client_secret` must never appear in frontend code or build
  artefacts.

---

## Prerequisites

- Docker or a running Keycloak ≥ 24.x instance.
- The `docker-compose.yml` in this repository starts Keycloak at
  `http://localhost:8080` in `start-dev` mode.

For production, use `start` instead of `start-dev` and configure
TLS termination in front of Keycloak.

### Theme source

The custom Keycloak theme is versioned in this repository at:

- `assets/keycloak/themes/meepletime`

For local dev-container testing, `.devcontainer/docker-compose.yml`
mounts this path into Keycloak as `/opt/keycloak/themes`.
The dev command also disables Keycloak theme caching so CSS and
template edits appear after a browser refresh.

The login flow uses standalone FreeMarker templates under
`login/`. The account console uses a custom `account/index.ftl`
shell on top of `keycloak.v3`, so branding and page framing can
be changed without forking the React application bundle.

For production, mount `assets/keycloak/themes` (or a copied image
layer containing it) to `/opt/keycloak/themes` in the Keycloak
container and set both the realm login theme and account theme to
`meepletime`.

---

## Initial setup

### 1. Start Keycloak

```bash
docker compose up keycloak -d
```

Wait until Keycloak is healthy:

```bash
docker compose ps keycloak
```

### 2. Create the realm

1. Open `http://localhost:8080/admin` and sign in with the
   credentials from `KC_ADMIN_PASSWORD` (default: `changeme`).
2. In the top-left dropdown, click **Create Realm**.
3. Set **Realm name** to `meepletime`.
4. Click **Create**.

### 3. Create the frontend client

1. In the `meepletime` realm, go to **Clients → Create client**.
2. Set:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `meepletime-frontend`
   - **Name**: `MeepleTime Frontend`
3. Click **Next**.
4. On the **Capability config** screen:
   - Disable **Client authentication** (this creates a public
     client — no `client_secret`).
   - Enable **Standard flow** (authorization code).
5. Click **Next**.
6. On the **Login settings** screen, set:
   - **Valid redirect URIs**:
     `http://localhost:5173/auth/callback`
     (add your production URL too, e.g.
     `https://meepletime.example.com/auth/callback`)
   - **Valid post logout redirect URIs**:
     `http://localhost:5173/`
   - **Web origins**: `http://localhost:5173`
7. Click **Save**.

### 4. Verify discovery document

The FastAPI backend resolves the JWKS URI from the OIDC
discovery document.  Verify it is accessible:

```bash
curl -s \
  http://localhost:8080/realms/meepletime/.well-known/openid-configuration \
  | python -m json.tool | head -20
```

You should see a JSON object containing `jwks_uri`.

---

## Environment variables

Set these in `.env` (or the deployment secret manager):

| Variable | Example value | Description |
|---|---|---|
| `OIDC_AUTHORITY` | `http://keycloak:8080/realms/meepletime` | Keycloak realm URL. Used by the backend. |
| `OIDC_AUDIENCE` | `meepletime-frontend` | Expected `aud` claim. Must match the Client ID. |
| `OIDC_ISSUER` | `http://keycloak:8080/realms/meepletime` | Expected `iss` claim. Usually same as authority. |
| `VITE_OIDC_AUTHORITY` | `http://localhost:8080/realms/meepletime` | Frontend authority (browser-reachable URL). |
| `VITE_OIDC_CLIENT_ID` | `meepletime-frontend` | Public client ID. |
| `VITE_OIDC_REDIRECT_URI` | `http://localhost:5173/auth/callback` | Callback URI registered in Keycloak. |
| `VITE_OIDC_POST_LOGOUT_URI` | `http://localhost:5173/` | Post-logout redirect URI. |

> **Note**: `OIDC_AUTHORITY` and `VITE_OIDC_AUTHORITY` may differ
> in a Docker environment where the backend uses the internal
> hostname (`keycloak`) and the browser uses `localhost`.  Both
> must resolve to the same Keycloak realm.

---

## Adding users

Users are managed in Keycloak.

1. In the `meepletime` realm, go to **Users → Add user**.
2. Fill in **Username** and **Email**, enable **Email verified**.
3. Click **Create**, then go to the **Credentials** tab and set
   a password.

For self-hosted circles, user registration can also be enabled
in **Realm settings → Login → User registration**.

---

## Token claims

The backend reads the following claims from the access token:

| Claim | Required | Use |
|---|---|---|
| `sub` | Yes | OIDC subject — unique identity key. |
| `email` | Yes | Used to find or create the local user. |
| `name` | No | Stored as `display_name` on the user. |

Ensure these claims are included in the access token.  By
default Keycloak includes `sub`.  To add `email` and `name`,
go to **Clients → meepletime-frontend → Client scopes** and
verify that `email` and `profile` scopes are assigned.

---

## Production checklist

- [ ] Replace `start-dev` with `start` in the Keycloak command.
- [ ] Configure TLS (Keycloak behind a reverse proxy or with
      built-in TLS).
- [ ] Set `KC_ADMIN_PASSWORD` to a strong random value.
- [ ] Register production redirect URIs in the Keycloak client.
- [ ] Set `OIDC_AUTHORITY` / `VITE_OIDC_AUTHORITY` to the
      production Keycloak URL.
- [ ] Back up the Keycloak database (or export the realm).
- [ ] Mount `/opt/keycloak/themes` with the `meepletime` theme.
- [ ] Verify **Realm settings → Themes → Login theme** is
  `meepletime`.
- [ ] Verify **Realm settings → Themes → Account theme** is
  `meepletime`.

---

## Realm export / import

Export the `meepletime` realm for backup or CI:

```bash
docker exec -it <keycloak_container> \
  /opt/keycloak/bin/kc.sh export \
  --realm meepletime \
  --file /tmp/meepletime-realm.json

docker cp <keycloak_container>:/tmp/meepletime-realm.json .
```

To import on a fresh instance, place the JSON file in a
volume and pass `--import-realm` to the Keycloak start command.
