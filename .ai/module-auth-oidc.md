# Agent instructions: module-auth-oidc

This module documents the OIDC authentication implementation for
this project, which uses Keycloak (self-hosted) as the sole
identity provider (Option A).

**Prerequisite**: `stack-fastapi-vuetify/.ai/instructions.md` must
already be loaded and followed. All rules there remain in force.

---

## Architecture invariants

These are non-negotiable.

- **Vue = public OIDC client.** It initiates flows and holds
  tokens in the browser. There is no in-app login form.
- **FastAPI = stateless OAuth resource server.** It validates
  bearer tokens on every request via Keycloak's JWKS endpoint.
  It never participates in the OIDC flow.
- PKCE (`S256`) is mandatory on the authorization code flow.
- The `state` parameter is mandatory to prevent CSRF.
- `client_secret` must never appear in frontend code or be
  bundled into the built artefact.
- Never log raw token values anywhere.
- The architecture is stateless (no server-side session).
  If requirements emerge that would benefit from server-side
  sessions, **stop and ask the developer** before implementing.
- GitHub and Twitter login are out of scope. Social providers
  may be configured inside Keycloak at a later date without
  changes to application code.

---

## Keycloak client setup — two-client pattern

Keycloak is the sole identity provider. Two clients are
configured in the Keycloak realm:

### 1. `meepletime-frontend` (public OIDC client)

- **Type**: Public (no `client_secret`)
- **Protocol**: OpenID Connect
- **Flow**: Authorization code + PKCE (`S256`)
- **Redirect URIs**: `http://localhost:5173/*` (add production
  URL alongside in production deployments)
- **Web origins**: `http://localhost:5173`
- This is the client the Vue app uses to authenticate users.

### 2. `meepletime-backend` (bearer-only resource server)

- **Type**: Bearer-only (no login flow, no `client_secret`
  required for validation)
- **Protocol**: OpenID Connect
- This client exists solely so that Keycloak includes
  `meepletime-backend` in the `aud` claim of access tokens.

**Why two clients?**
Keycloak only adds a client to the access token's `aud` claim
when the authenticating user has at least one client-scoped role
assigned on that client. Creating a separate bearer-only client
(`meepletime-backend`) and assigning a `user` role to application
users is the correct OIDC-compliant way to achieve a distinct,
validatable audience in the token. The frontend client alone
cannot appear as audience in the way needed by the backend.

### `user` role and audience propagation

1. Define a `user` client role on `meepletime-backend`.
2. Assign that role to every application user (or via a default
   role group in Keycloak).
3. Keycloak then automatically includes `"meepletime-backend"` in
   the `aud` array of the issued access token.
4. The FastAPI backend validates `audience="meepletime-backend"`.

Do **not** add the `user` role to `meepletime-frontend`. The
frontend client remains a clean, role-free public client.

### Keycloak hostname configuration (v26+)

In Keycloak 26+, `KC_HOSTNAME` must be a full URL including
scheme and port, not just a hostname. Otherwise the `iss` claim
omits the port, which causes PyJWT's strict issuer check to fail:

```
# Correct (Keycloak 26+)
KC_HOSTNAME=http://keycloak.127.0.0.1.nip.io:8080

# Wrong — iss in token will omit :8080
KC_HOSTNAME=keycloak.127.0.0.1.nip.io
```

The realm configuration is in `deploy/dev/keycloak-realm.json`
and is imported automatically on first startup in dev.

---

## Frontend rules

### Package

```
npm install oidc-client-ts
```

`oidc-client-ts` is the only permitted OIDC library.

### Token storage

This project uses `sessionStorage` via `WebStorageStateStore`.

| Strategy | Pro | Con |
|---|---|---|
| Memory | Safest (no XSS persistence) | Lost on page reload |
| **sessionStorage** | Survives reload within tab | Lost on new tab |
| localStorage | Persistent | Accessible to XSS |

### UserManager configuration

```typescript
// src/auth/oidc.ts
import { UserManager, WebStorageStateStore } from 'oidc-client-ts'

export const userManager = new UserManager({
  authority: import.meta.env.VITE_OIDC_AUTHORITY as string,
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID as string,
  // Derived at runtime so the callback origin always matches
  // the origin where signinRedirect() was called, keeping
  // sessionStorage accessible throughout the PKCE flow.
  // Do NOT use a hardcoded env var or 127.0.0.1/localhost
  // mismatch will cause "No matching state found" errors.
  redirect_uri: `${window.location.origin}/auth/callback`,
  post_logout_redirect_uri: `${window.location.origin}/`,
  scope: 'openid email profile',
  response_type: 'code',
  automaticSilentRenew: true,
  userStore: new WebStorageStateStore({
    store: window.sessionStorage,
  }),
})
```

**Critical**: `redirect_uri` must be derived from
`window.location.origin` at runtime. Hard-coding a URL (even via
an environment variable) causes `sessionStorage` key mismatches
when the app is accessed under a different origin (e.g.
`localhost` vs `127.0.0.1`), resulting in
`"No matching state found in storage"` errors.

### Frontend environment variables

Only two variables are required in `.env.local`:

```
VITE_OIDC_AUTHORITY=http://keycloak.127.0.0.1.nip.io:8080/realms/meepletime
VITE_OIDC_CLIENT_ID=meepletime-frontend
```

Do **not** add `VITE_OIDC_REDIRECT_URI` or
`VITE_OIDC_POST_LOGOUT_URI` — these are derived at runtime.

### TokenProvider wiring

Read the access token directly from `sessionStorage` at the
well-known key that `oidc-client-ts` uses internally. This avoids
an async `getUser()` call on every API request:

```typescript
// src/main.ts
import { setTokenProvider } from './api'
import { userManager } from './auth/oidc'

const authority = import.meta.env.VITE_OIDC_AUTHORITY as string
const clientId = import.meta.env.VITE_OIDC_CLIENT_ID as string
// Key format: oidc.user:<authority>:<client_id>
const key = `oidc.user:${authority}:${clientId}`

setTokenProvider({
  getToken: () => {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    try {
      return (JSON.parse(raw) as { access_token?: string })
        .access_token ?? null
    } catch {
      return null
    }
  },
})
```

### `useAuth()` composable

The composable wraps `userManager` and exposes reactive state.
All components and views must use it rather than importing
`userManager` directly for auth state:

```typescript
// src/composables/auth.ts
export function useAuth() {
  return {
    /** Reactive OIDC User object (null when logged out). */
    oidcUser,           // Ref<OidcUser | null>

    /** Reactive OIDC subject (profile.sub). */
    userId,             // ComputedRef<string | undefined>

    /** True when a valid non-expired session exists. */
    isLoggedIn,         // ComputedRef<boolean>

    /** Initiate OIDC redirect, passing returnTo as state. */
    login,              // (returnTo?: string) => Promise<void>

    /** Call signoutRedirect and clear the session. */
    logout,             // () => Promise<void>

    /** Restore state from sessionStorage on app startup. */
    loadFromStorage,    // () => Promise<void>
  }
}
```

Call `loadFromStorage()` once from `App.vue` during `onMounted`
before rendering any auth-gated content.

### Routes

Three routes are always required:

| Path | Component | Purpose |
|---|---|---|
| `/login` | `LoginView.vue` | OIDC redirect interstitial |
| `/auth/callback` | `AuthCallbackView.vue` | Handle code exchange |
| *(inline)* | *(call `signoutRedirect`)* | Logout |

**`LoginView.vue`**:

1. Read `returnTo` from the route query.
2. If the user already has a valid session (from
   `userManager.getUser()`), skip OIDC and redirect to
   `returnTo` immediately. This prevents an unnecessary OIDC
   round trip when the user navigates to `/login` while
   already authenticated.
3. Otherwise call `userManager.signinRedirect({ state: returnTo })`.
4. Show a loading spinner while the redirect is pending.

**`AuthCallbackView.vue`**:

1. Call `userManager.signinRedirectCallback()`.
2. Read `user.state` as `returnTo`. Reject unsafe values:
   `/login`, paths starting with `/auth/callback`, and empty
   strings — fall back to `/circles` in those cases.
3. Handle `"No matching state found in storage"` errors by
   redirecting to `/login` (clean recovery from stale/cross-
   origin state), rather than showing a raw error.
4. Handle other errors by displaying a user-visible message.

### Navigation guard

**Do NOT call `signinRedirect()` directly from the guard.**
Calling `signinRedirect` (which sets `window.location.href`)
and then returning `false` causes Vue Router 4 to call
`history.go(-1)` to restore the previous URL. This races with
the browser navigation initiated by `signinRedirect` and
produces an infinite redirect loop.

Instead, redirect to the `/login` route and let
`LoginView.vue` call `signinRedirect` from `onMounted`:

```typescript
// src/router/index.ts
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const user = await userManager.getUser()
  if (!user || user.expired) {
    return { path: '/login', query: { returnTo: to.fullPath } }
  }
  return true
})
```

The full `returnTo` chain is:
1. Guard passes `to.fullPath` as `query.returnTo` to `/login`.
2. `LoginView` passes it as `state` to `signinRedirect`.
3. Keycloak redirects to `/auth/callback`.
4. `AuthCallbackView` reads `user.state` to restore the route.

Mark protected routes with `meta: { requiresAuth: true }`.

### Unauthorized handler

The global 401 handler (wired in `main.ts`) must check for an
existing session before calling `signinRedirect`. Triggering
`signinRedirect` when the user already has a valid token (e.g.
after a transient 401 from a misconfigured backend) would cause
Keycloak to SSO-login them immediately and create a loop:

```typescript
setUnauthorizedHandler(async () => {
  const user = await userManager.getUser()
  if (user && !user.expired) {
    // Token exists but backend rejected it — go home rather
    // than re-triggering the OIDC flow.
    await router.replace('/')
  } else {
    await userManager.signinRedirect({
      state: router.currentRoute.value.fullPath,
    })
  }
})
```

---

## Backend rules

### Packages

```
uv add pyjwt[crypto] httpx
```

`pyjwt` is the only permitted JWT library. Do not use
`python-jose`, `authlib` for validation, or any other JWT library.

### OIDC discovery and JWKS

```python
# app/auth/jwks.py
from functools import lru_cache
import httpx
import jwt

@lru_cache(maxsize=8)
def get_jwks_client(authority: str) -> jwt.PyJWKClient:
    """Return a cached JWKS client for the given authority.

    :param authority: OIDC issuer base URL.
    :returns: Configured PyJWKClient with auto key refresh.
    """
    discovery_url = (
        f"{authority.rstrip('/')}/.well-known/openid-configuration"
    )
    with httpx.Client() as client:
        doc = client.get(discovery_url).raise_for_status().json()
    return jwt.PyJWKClient(doc["jwks_uri"])
```

- Cache the `PyJWKClient` per authority. It handles unknown
  `kid` by re-fetching the JWKS automatically.
- Never hard-code JWKS URIs; always resolve from discovery.

### Token validation dependency

The `get_current_user` dependency validates the bearer token
**and** provisions a local user account on first login. It
links the OIDC identity (`sub` + issuer) to a local `User` row
via an `AuthIdentity` join, so the rest of the application
works with typed ORM objects rather than raw JWT payloads:

```python
# app/dependencies.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.auth.jwks import get_jwks_client
from app.config import Settings, get_settings
from app.database import get_db

bearer = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    """Validate the OIDC bearer token and return the local User.

    Finds or creates the User and AuthIdentity rows on first
    login (auto-provisioning). Subsequent calls hit the DB
    but perform no writes.

    :param credentials: Authorization header bearer token.
    :param settings: Application configuration.
    :param db: Database session.
    :returns: Local User record for the authenticated identity.
    :raises HTTPException: 401 when the token is missing,
        expired, has the wrong audience/issuer, or has a
        tampered signature.
    """
    token = credentials.credentials
    client = get_jwks_client(settings.OIDC_AUTHORITY)
    try:
        key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=settings.OIDC_AUDIENCE,
            issuer=settings.OIDC_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    # Auto-provision: find-or-create User + AuthIdentity.
    ...
    return user
```

- Validate `exp`, `nbf`, `aud`, and `iss` on every call.
- Inject into every protected route via `Depends`.
- Never expose raw exception messages to the client.

### User auto-provisioning

On the first successful token validation for a new identity,
the backend creates:

1. A `User` row (`email`, `display_name` from JWT claims).
2. An `AuthIdentity` row linking `User.id` to the OIDC
   `provider` (the issuer URL) and `subject` (`sub` claim).

Subsequent calls look up the existing `AuthIdentity` row and
return the linked `User` directly. No manual registration flow
is needed.

### Required environment variables

```python
OIDC_AUTHORITY: str  # Keycloak realm URL
                     # http://keycloak:8080/realms/meepletime
OIDC_AUDIENCE: str   # meepletime-backend
OIDC_ISSUER: str     # same as OIDC_AUTHORITY (Keycloak realm URL)
```

`OIDC_AUDIENCE` must be `meepletime-backend` (the bearer-only
resource server client ID), not the frontend client ID.

---

## Dev-token: headless-agent authentication

Coding agents (e.g. GitHub Copilot in the cloud) cannot spin up
Keycloak, and running a full OIDC flow requires a browser.  To
support automated / headless development, the backend accepts
**self-minted HS256 JWTs** when `DEV_SHARED_SECRET` is set.

### How it works

1. `DEV_SHARED_SECRET` is an optional env var in `backend/.env`.
   When absent (production), only JWKS/RS256 tokens are accepted.
   When present, the backend validates tokens as HS256 JWTs
   signed with that secret (bypassing Keycloak JWKS validation
   entirely).  OIDC/RS256 validation is not performed.

2. The token is generated with `task dev:token`:

   ```
   task dev:token
   task dev:token -- --sub myagent --email agent@dev.local
   task dev:token -- --ttl 3600
   ```

   The token includes `iss`, `aud`, `sub`, `email`, `name`, `iat`,
   and `exp`.  `iss` and `aud` are read from `.env` and must match
   `OIDC_ISSUER` / `OIDC_AUDIENCE`.  Default lifespan is 1 year.

3. Pass the token as a bearer header to API calls:

   ```
   TOKEN=$(task dev:token -s)
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/...
   ```

### Implementation rules

- `DEV_SHARED_SECRET: str | None = None` in `Settings`.
- In `get_current_user`, branch on `settings.DEV_SHARED_SECRET`:
  - Set → `jwt.decode(..., algorithms=["HS256"])`.
  - Not set → existing JWKS path with `algorithms=["RS256"]`.
- The token generator lives in `backend/scripts/dev_token.py`.
  It is **outside `src/app/`** and is therefore not included in
  the production wheel.
- **NEVER** set `DEV_SHARED_SECRET` in production config.
- Add `DEV_SHARED_SECRET` to the `.env.example` as a commented-out
  line with a clear "dev-only" warning.

---

## Testing

### Backend

- Mock the JWKS endpoint with `respx` or `pytest-httpserver`.
- Required test cases: valid token, expired token, wrong
  audience, wrong issuer, tampered signature.
- Never make real HTTP calls to identity providers in tests.

### Frontend

- Mock `userManager` methods with `vi.fn()` in vitest.
- Test the navigation guard with mocked `getUser()` returning
  a valid user, an expired user, and `null`.
- Test `AuthCallbackView` with mocked
  `signinRedirectCallback()` for success, state-not-found
  error, and other errors.
