# Development login without Keycloak

Production authentication is **exclusively** Keycloak OIDC (see
[`contract.md`](../../contract.md) and the
[operator Keycloak guide](../operator/keycloak.md)). Running Keycloak
locally is heavyweight and impossible to complete for a headless coding
agent, so the project ships a **development-only** login path that lets
you drive the whole stack — SPA included — without an identity provider.

> **Never enable any of this in production.** Every switch defaults off
> and is layered so it cannot activate in a production build or image
> (see [Why it cannot leak](#why-it-cannot-leak-to-production)).

## What you get

- A single backend endpoint `POST /auth/dev/login`, mounted **only**
  when `MEEPLETIME_DEV_AUTH_ENABLED=true`. It takes an identity
  (`sub`/`email`/`name`, all optional) and mints a token for it.
- A dev-user picker on the SPA `/login` screen (instead of the
  Keycloak redirect) when the dev server runs with `VITE_DEV_AUTH=true`.

The endpoint mints a real HS256 dev token — the same kind
`task dev:token` produces — which flows through the **standard** token
validator and user-provisioning code in `app/dependencies.py`. This is
not a parallel auth bypass; it just removes the need for Keycloak to
*issue* the token.

The endpoint deliberately knows nothing about named "presets". It is a
generic "mint a token for this identity" call, so a deployed instance
has no canned dev credentials baked into it and nothing to enumerate.

### Dev identities ("presets")

For convenience the SPA picker offers a few stable identities. These are
documented **here** (the source of truth) and implemented only in the
dev-only frontend picker — they are never sent by or fetched from the
API:

| Picker label | `sub`        | `email`                     |
| ------------ | ------------ | --------------------------- |
| Dev Owner    | `dev-owner`  | `dev-owner@meepletime.local`  |
| Dev Admin    | `dev-admin`  | `dev-admin@meepletime.local`  |
| Dev Member   | `dev-member` | `dev-member@meepletime.local` |

The labels are only identity hints — **not** global roles. MeepleTime
roles (`MemberRole.owner/admin/member`) are per-circle. To exercise
RBAC, log in as one identity to create/own a circle, then as another to
join it; an owner/admin can promote members from there. Use any other
`sub`/`email`/`name` you like — these three are just a starting set.

## Enabling it

Backend (`backend/.env`):

```dotenv
MEEPLETIME_DEV_SHARED_SECRET=change-me-dev-only-secret-32-chars
MEEPLETIME_DEV_AUTH_ENABLED=true
```

The backend **refuses to start** if `DEV_AUTH_ENABLED` is true without a
`DEV_SHARED_SECRET` (the secret signs *and* verifies the token, so both
must be the same value).

Frontend (`frontend/.env.local`):

```dotenv
VITE_DEV_AUTH=true
```

Then run the stack without Keycloak:

```bash
task backend     # logs "DEV AUTH ENABLED: /auth/dev/* mounted"
task frontend    # vite dev server
```

Open the app, land on `/login`, and pick an identity. Logout returns you
to the picker (there is no Keycloak session to end).

## Running the full stack outside the dev-container

The committed `docker-compose.yml` and `backend/.env` assume the
dev-container network (the database host is `db`). To run the backend
directly on your host — for example so a coding agent can drive the SPA
with Playwright — you need a database reachable on `localhost`. Spin up
a disposable one:

```bash
task dev:db        # postgres:16-alpine on localhost:5432 (ephemeral)
# ... work ...
task dev:db-stop   # tear it down (drops all data)
```

Point the backend at it with a **shell** override (an exported variable
beats `backend/.env`, so you never edit the committed file):

```bash
export MEEPLETIME_DATABASE_URL=postgresql://meepletime:changeme@localhost:5432/meepletime
export MEEPLETIME_DEV_SHARED_SECRET=dev-only-secret-at-least-thirty-two-chars
export MEEPLETIME_DEV_AUTH_ENABLED=true

task migrate       # alembic upgrade head against the throwaway DB
task backend       # uvicorn on :8000 (also runs migrate)
```

In a second shell, with `VITE_DEV_AUTH=true` in `frontend/.env.local`:

```bash
task frontend      # vite dev server on :5173
```

Now the app at `http://localhost:5173` is fully usable without Keycloak,
and Playwright can drive it (see below). When finished,
`Ctrl-C` the servers and `task dev:db-stop`.

> The throwaway DB publishes port **5432** on the host. The
> dev-container's own database is not published to the host, so there is
> no conflict; if you do hit a port clash, stop whatever owns 5432
> first.

## Headless / agent usage

### API only

```bash
# Bare body → the default dev-agent identity:
curl -sX POST localhost:8000/auth/dev/login \
  -H 'Content-Type: application/json' -d '{}' | jq -r .access_token
# Or supply an identity (e.g. the Dev Owner from the table above):
curl -sX POST localhost:8000/auth/dev/login \
  -H 'Content-Type: application/json' \
  -d '{"sub":"dev-owner","email":"dev-owner@meepletime.local","name":"Dev Owner"}' \
  | jq -r .access_token
# → use as: Authorization: Bearer <token>
```

This is the HTTP equivalent of `task dev:token` and needs no browser.

### Full SPA via Playwright

The simplest path exercises the real flow — navigate and click:

```js
await page.goto('http://localhost:5173/login')
await page.getByRole('button', { name: 'Dev Owner' }).click()
// the app stores the session and routes to the destination
```

If you need to skip the click (setup-heavy tests), call the endpoint and
inject the session before navigating — store the token in the
oidc-client-ts shape under `oidc.user:<authority>:<client_id>` (see
`src/auth/devLogin.ts` for the exact `User` object it builds).

## Why it cannot leak to production

Defense-in-depth — each layer is independently sufficient:

1. **Backend flag default off.** `DEV_AUTH_ENABLED` defaults to `false`;
   the `/auth/dev/*` router is never imported or mounted, so the
   endpoints are a plain `404` in production.
2. **Startup guard.** Enabling the flag without `DEV_SHARED_SECRET`
   raises at startup, and a `WARNING` is logged whenever the dev router
   mounts.
3. **No production token even if reached.** HS256 tokens are rejected
   unless `DEV_SHARED_SECRET` is set — which must never happen in
   production.
4. **Frontend excluded from builds.** The dev UI is gated on
   `import.meta.env.DEV`, which Vite replaces with a literal `false` in
   any `vite build`. Rollup then drops the lazily-imported
   `DevLoginPanel` chunk and `devLogin` helper entirely — verify with
   `grep -r auth/dev frontend/dist` (empty). `VITE_DEV_AUTH` is honoured
   only under the dev server.
5. **Not runtime-configurable.** The `devAuth` flag is deliberately
   absent from `window.__MEEPLETIME_CONFIG__`, so the production
   runtime-config mechanism cannot switch it on.
