# Deployment

How to bring up MeepleTime for a real (alpha) deployment using the
prebuilt container images.

This setup assumes two services are provided **externally** and are
_not_ part of the application stack:

- **An OpenID Connect provider (IDP)** — reachable at a public URL,
  with a public client for the SPA and an audience for the backend
  already configured. MeepleTime is a plain OIDC resource server and
  does not ship or manage an IDP. If you do not already run one, the
  [Keycloak appendix](keycloak.md) walks through configuring Keycloak
  as a concrete example.
- **PostgreSQL** — a vanilla PostgreSQL 16 instance provided by the
  OPS team, with an empty database and a login role for the app.

The application itself is just two images:
`ghcr.io/<owner>/<repo>/backend` and `.../frontend`.

## 1. Images

MeepleTime is published as two container images on the GitHub
Container Registry (GHCR):

- `ghcr.io/<owner>/<repo>/backend`
- `ghcr.io/<owner>/<repo>/frontend`

Each release is published under an immutable version tag (e.g.
`0.1.0`) alongside the moving `latest` tag. **Pin a specific version
tag in production** rather than `latest` so redeploys are reproducible.

To pull manually (after `docker login ghcr.io`):

```bash
docker pull ghcr.io/<owner>/<repo>/backend:0.1.0
docker pull ghcr.io/<owner>/<repo>/frontend:0.1.0
```

## 2. Configuration

A ready-to-edit Compose file and environment template live in
`deploy/prod/`:

```bash
cp deploy/prod/.env.example deploy/prod/.env
$EDITOR deploy/prod/.env
```

### Backend environment

The backend reads its configuration from the following
**`MEEPLETIME_`**-prefixed environment variables:

| Variable                    | Required | Purpose                                                                                                                                                           |
| --------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MEEPLETIME_DATABASE_URL`   | yes      | DSN for the external PostgreSQL.                                                                                                                                  |
| `MEEPLETIME_OIDC_AUTHORITY` | yes      | IDP discovery base URL — the backend fetches `<authority>/.well-known/openid-configuration` from it to resolve the JWKS keys. For Keycloak this is the realm URL. |
| `MEEPLETIME_OIDC_AUDIENCE`  | yes      | Expected `aud` claim. Tokens must be issued for the backend, e.g. `meepletime-backend`.                                                                           |
| `MEEPLETIME_OIDC_ISSUER`    | no       | Expected `iss` claim. Defaults to `MEEPLETIME_OIDC_AUTHORITY`; only set it when it differs (see below).                                                           |
| `MEEPLETIME_CORS_ORIGINS`   | yes      | JSON array of allowed browser origins.                                                                                                                            |
| `MEEPLETIME_APP_BASE_URL`   | yes      | Public base URL of the frontend SPA. The backend embeds it in the links it emails (notification deep links and the email-address confirmation link).             |

`MEEPLETIME_CORS_ORIGINS` must be valid JSON and must include the
frontend's public origin, e.g. `["https://meeple.example.com"]`.
Requests from the browser are rejected by CORS otherwise.

`MEEPLETIME_APP_BASE_URL` is the public URL your users reach the app
at (e.g. `https://meeple.example.com`, no trailing slash) — **not** the
internal container address. The backend bakes it into the links it
sends by email, so if it is left unset those links fall back to
`http://localhost:5173` and will not resolve for recipients. This is a
backend setting, not a request-derived value: notification emails are
produced by a background scheduler with no incoming request, so proxy
headers (e.g. Traefik's `X-Forwarded-*`) cannot supply it.

#### Authority vs. issuer

These are two different things that _usually_ hold the same value:

- **Authority** is a **location** — where the backend goes to download
  the OIDC discovery document and signing keys (JWKS).
- **Issuer** is a **trust value** — the exact string the token's `iss`
  claim must equal for the backend to accept it.

For Keycloak and most OIDC providers the issuer equals the discovery
URL, so you set `MEEPLETIME_OIDC_AUTHORITY` alone and the backend uses
it for both. Override `MEEPLETIME_OIDC_ISSUER` only in split-network
deployments where the backend reaches the IDP over an internal
hostname (e.g. `http://keycloak:8080/realms/meepletime`) while tokens
carry a different public issuer (e.g.
`https://auth.example.com/realms/meepletime`).

> **Never** set `MEEPLETIME_DEV_SHARED_SECRET` in production — it
> enables self-minted HS256 tokens and is for local/headless use only.

### Frontend environment

The frontend reads its browser-facing configuration from these
`MEEPLETIME_*` variables (the same prefix as the backend):

| Variable                    | Purpose                                                |
| --------------------------- | ------------------------------------------------------ |
| `MEEPLETIME_OIDC_AUTHORITY` | IDP authority/discovery URL (shared with the backend). |
| `MEEPLETIME_OIDC_CLIENT_ID` | Public SPA client id, e.g. `meepletime-frontend`.      |
| `MEEPLETIME_API_BASE_URL`   | Public base URL of the backend API.                    |

`MEEPLETIME_OIDC_AUTHORITY` is shared with the backend — define it once
in `.env`. `MEEPLETIME_API_BASE_URL` is the URL the **browser** uses to
reach the backend, so it must be publicly resolvable and present in
`MEEPLETIME_CORS_ORIGINS`. `MEEPLETIME_OIDC_AUTHORITY` must likewise be
the exact **public** IDP URL the browser can reach.

## 3. Bring up the stack

```bash
docker compose -f deploy/prod/docker-compose.yml up -d
```

On startup the backend automatically applies any pending database
schema changes, so a fresh external database is brought up to schema
on first boot. **A deployment may therefore modify the database** (see
the Upgrades section). The frontend waits for the backend to be
healthy before it starts.

Verify:

```bash
# Backend liveness
curl -sf http://<backend-host>:8000/health
# Frontend is serving its runtime configuration
curl -s   http://<frontend-host>/config.js
```

The `/config.js` response should show your real IDP and API URLs.

## 4. Upgrades

1. Choose the new version tag to deploy.
2. Update the image tags in `deploy/prod/.env`.
3. `docker compose -f deploy/prod/docker-compose.yml pull`
4. `docker compose -f deploy/prod/docker-compose.yml up -d`

The backend applies database schema changes automatically on start, so
a deployment may modify the database. **Take a database backup before
upgrading** if the release contains schema changes.

## 5. Troubleshooting

- **Login redirects fail / token rejected** — the token's `iss` must
  match `MEEPLETIME_OIDC_ISSUER` (which defaults to
  `MEEPLETIME_OIDC_AUTHORITY`), the `aud` must match
  `MEEPLETIME_OIDC_AUDIENCE`, and the IDP client's redirect URIs must
  include the frontend origin. See the [Keycloak appendix](keycloak.md).
- **API calls blocked in the browser** — the frontend origin is
  missing from `MEEPLETIME_CORS_ORIGINS`, or `MEEPLETIME_API_BASE_URL`
  is
  wrong.
- **Backend exits on start** — usually a bad `MEEPLETIME_DATABASE_URL`
  or the database is unreachable; check `docker compose logs backend`.
