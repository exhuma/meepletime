# Appendix: Keycloak as an OIDC Provider

> **This is an appendix, not a requirement.** MeepleTime treats the
> identity provider (IDP) as an **external** service and works with any
> compliant OpenID Connect provider. This walkthrough is provided as a
> convenience for operators who do not already run an IDP and want a
> concrete, working example using [Keycloak](https://www.keycloak.org/).
> If you already operate an OIDC provider, you only need the values in
> the [deployment guide](deployment.md); skip the rest.

> **Local development without Keycloak.** Contributors who just want to
> run the app locally can skip standing up an IDP entirely by using the
> dev-only login path — see
> [Development login (no Keycloak)](../developer/auth.md). Those switches
> are development-only and can never activate in a production build or
> image; production authentication is always Keycloak (or another OIDC
> provider) as described below.

## What MeepleTime needs from any IDP

Whatever provider you use, MeepleTime requires:

- A **public client** for the Vue SPA — authorization-code + PKCE, no
  client secret. The frontend holds tokens in the browser; there is no
  in-app login form.
- Access tokens whose **`aud`** claim names the backend (the value you
  set in `MEEPLETIME_OIDC_AUDIENCE`, e.g. `meepletime-backend`). The
  FastAPI backend is a stateless resource server that validates bearer
  tokens on every request against the IDP's JWKS endpoint and never
  participates in the OIDC flow.
- The standard **discovery document** at
  `<authority>/.well-known/openid-configuration` (used to resolve the
  JWKS keys) and the `sub`, `email`, and `name` claims (see
  the "Token claims" section below).
- `client_secret` must never appear in frontend code or build
  artefacts.

The rest of this appendix shows how to satisfy those requirements in
Keycloak specifically.

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

Colours and fonts are generated from the app's shared design tokens
(`frontend/src/theme/tokens.ts`) via `task build:keycloak`; the output
is committed, so the theme is ready to use without a build step.

For production, mount `assets/keycloak/themes` (or a copied image
layer containing it) to `/opt/keycloak/themes` in the Keycloak
container and set both the realm login theme and account theme to
`meepletime`. See [The MeepleTime Keycloak theme](keycloak-theme.md)
for the full artifact reference and packaging options (directory mount,
custom image, or provider JAR).

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

### 4. Make tokens target the backend audience

The backend rejects tokens whose `aud` claim does not match
`MEEPLETIME_OIDC_AUDIENCE`. By default Keycloak sets `aud` to
`account`, so add an audience mapper that names the backend:

1. Create a second client `meepletime-backend` (OpenID Connect). It is
   only a resource-server identity, so leave **Standard flow** and
   **Direct access grants** disabled — it never logs anyone in.
2. Go to **Clients → meepletime-frontend → Client scopes →
   meepletime-frontend-dedicated → Add mapper → By configuration →
   Audience**.
3. Set **Included Client Audience** to `meepletime-backend`, enable
   **Add to access token**, and save.

`meepletime-backend` is then the value you put in
`MEEPLETIME_OIDC_AUDIENCE`. Confirm a token actually carries it via the
**Client scopes → Evaluate** tab before deploying.

### 5. Verify discovery document

The FastAPI backend resolves the JWKS URI from the OIDC
discovery document. Verify it is accessible:

```bash
curl -s \
  http://localhost:8080/realms/meepletime/.well-known/openid-configuration \
  | python -m json.tool | head -20
```

You should see a JSON object containing `jwks_uri`.

---

## Mapping Keycloak to MeepleTime settings

The canonical, prefixed environment variables (and which service reads
them) are documented in the
[deployment guide](deployment.md). This table only shows
which Keycloak value goes into each one:

| Variable                     | Keycloak value                                  |
| ---------------------------- | ----------------------------------------------- |
| `MEEPLETIME_OIDC_AUTHORITY`  | The realm URL, e.g. `https://keycloak.example.com/realms/meepletime`. |
| `MEEPLETIME_OIDC_AUDIENCE`   | The backend client id `meepletime-backend` (the audience added in step 4). |
| `MEEPLETIME_OIDC_CLIENT_ID`  | The public SPA client id `meepletime-frontend`. |
| `MEEPLETIME_OIDC_ISSUER`     | Optional. Leave unset — Keycloak's `iss` equals the realm URL, which is already the authority. Set it only if the backend reaches Keycloak over a different host than the public issuer in tokens. |

> **Internal vs. public host.** In a Docker network the backend may
> reach Keycloak at an internal name (`http://keycloak:8080/...`) while
> browsers use the public URL (`https://keycloak.example.com/...`).
> Because the OIDC authority is baked into the browser session, set
> `MEEPLETIME_OIDC_AUTHORITY` to the **public** realm URL. If you want
> the backend to fetch JWKS over the internal name instead, that is
> exactly the case where you also set `MEEPLETIME_OIDC_ISSUER` to the
> public realm URL so token validation still matches the `iss` claim.

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

| Claim   | Required | Use                                    |
| ------- | -------- | -------------------------------------- |
| `sub`   | Yes      | OIDC subject — unique identity key.    |
| `email` | Yes      | Used to find or create the local user. |
| `name`  | No       | Stored as `display_name` on the user.  |

Ensure these claims are included in the access token. By
default Keycloak includes `sub`. To add `email` and `name`,
go to **Clients → meepletime-frontend → Client scopes** and
verify that `email` and `profile` scopes are assigned.

---

## Production checklist

- [ ] Replace `start-dev` with `start` in the Keycloak command.
- [ ] Configure TLS (Keycloak behind a reverse proxy or with
      built-in TLS).
- [ ] Set `KC_ADMIN_PASSWORD` to a strong random value.
- [ ] Register production redirect URIs in the Keycloak client.
- [ ] Set `MEEPLETIME_OIDC_AUTHORITY` to the public production
      Keycloak realm URL.
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
