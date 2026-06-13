# Deployment

How to bring up MeepleTime for a real (alpha) deployment using the
prebuilt container images.

This setup assumes two services are provided **externally** and are
*not* part of the application stack:

- **Keycloak** — reachable at a public URL, with the `meepletime`
  realm and the two clients already configured. See
  [Keycloak setup](keycloak.md).
- **PostgreSQL** — a vanilla PostgreSQL 16 instance provided by the
  OPS team, with an empty database and a login role for the app.

The application itself is just two images:
`ghcr.io/<owner>/<repo>/backend` and `.../frontend`.

## 1. Images

The images are built and pushed to the GitHub Container Registry
(GHCR) by the `Build and publish images` workflow
(`.github/workflows/build-images.yml`) whenever a `v*` tag is pushed:

```bash
git tag v0.1.0
git push origin v0.1.0
```

This publishes, for each component, the tags `0.1.0`, `0.1`, and
`latest`. Pin a specific version tag in production rather than
`latest` so redeploys are reproducible.

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

The backend reads its settings with the **`MEEPLETIME_`** env prefix
(see `backend/src/app/config.py`). These prefixed names are the ones
the application actually reads — set them, not the bare names.

| Variable                    | Purpose                               |
| --------------------------- | ------------------------------------- |
| `MEEPLETIME_DATABASE_URL`   | DSN for the external PostgreSQL.      |
| `MEEPLETIME_OIDC_AUTHORITY` | Keycloak realm URL (issuer).          |
| `MEEPLETIME_OIDC_ISSUER`    | Expected `iss` claim (same realm URL).|
| `MEEPLETIME_OIDC_AUDIENCE`  | Expected token audience.              |
| `MEEPLETIME_CORS_ORIGINS`   | JSON array of allowed browser origins.|

`MEEPLETIME_CORS_ORIGINS` must be valid JSON and must include the
frontend's public origin, e.g. `["https://meeple.example.com"]`.
Requests from the browser are rejected by CORS otherwise.

> **Never** set `MEEPLETIME_DEV_SHARED_SECRET` in production — it
> enables self-minted HS256 tokens and is for local/headless use only.

### Frontend environment

The frontend is a static build, but it also reads its browser-facing
configuration from `MEEPLETIME_*` variables (the same prefix as the
backend). They are injected at container start into `/config.js` (the
entrypoint renders `config.template.js` with `envsubst`):

| Variable                     | Purpose                            |
| ---------------------------- | ---------------------------------- |
| `MEEPLETIME_OIDC_AUTHORITY`  | Keycloak realm URL (shared).       |
| `MEEPLETIME_OIDC_CLIENT_ID`  | Public client id, `meepletime-frontend`. |
| `MEEPLETIME_API_BASE_URL`    | Public base URL of the backend API.|

`MEEPLETIME_OIDC_AUTHORITY` is shared with the backend — define it once
in `.env`. `MEEPLETIME_API_BASE_URL` is the URL the **browser** uses to
reach the backend, so it must be publicly resolvable and present in
`MEEPLETIME_CORS_ORIGINS`. Because the OIDC authority is baked into the
browser session, it must be the exact public Keycloak URL — a single
image can serve any deployment because these values are applied at
runtime, not at build time.

## 3. Bring up the stack

```bash
docker compose -f deploy/prod/docker-compose.yml up -d
```

The backend image runs database migrations (`alembic upgrade head`)
automatically on every start, so a fresh external database is brought
up to schema on first boot. The frontend waits for the backend to be
healthy before it starts.

Verify:

```bash
# Backend liveness
curl -sf http://<backend-host>:8000/health
# Frontend config was injected
curl -s   http://<frontend-host>/config.js
```

The `/config.js` response should show your real Keycloak and API URLs.

## 4. Upgrades

1. Push a new `v*` tag (or wait for CI to publish one).
2. Update the image tags in `deploy/prod/.env`.
3. `docker compose -f deploy/prod/docker-compose.yml pull`
4. `docker compose -f deploy/prod/docker-compose.yml up -d`

Migrations run automatically on backend start. Take a database backup
before upgrading if the release contains schema changes.

## 5. Troubleshooting

- **Login redirects fail / token rejected** —
  `MEEPLETIME_OIDC_AUTHORITY` and `MEEPLETIME_OIDC_ISSUER` must be the
  *same* realm URL, and the Keycloak client redirect URIs must include
  the frontend origin. See [Keycloak setup](keycloak.md).
- **API calls blocked in the browser** — the frontend origin is
  missing from `MEEPLETIME_CORS_ORIGINS`, or `MEEPLETIME_API_BASE_URL`
  is
  wrong.
- **Backend exits on start** — usually a bad `MEEPLETIME_DATABASE_URL`
  or the database is unreachable; check `docker compose logs backend`.
