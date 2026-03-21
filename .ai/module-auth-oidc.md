# Agent instructions: module-auth-oidc

This module adds OIDC/OAuth2 authentication to a project built on
the `stack-fastapi-vuetify` core template.

**Prerequisite**: `stack-fastapi-vuetify/.ai/instructions.md` must
already be loaded and followed. All rules there remain in force.

---

## Architecture invariants

These are non-negotiable regardless of provider or project size.

- **Vue = public OIDC client.** It initiates flows and holds tokens.
- **FastAPI = stateless OAuth resource server.** It validates bearer
  tokens on every request. It never participates in the auth flow
  except in Option B (see below).
- PKCE (`S256`) is mandatory on every authorization code flow.
- The `state` parameter is mandatory to prevent CSRF.
- `client_secret` must never appear in frontend code or be bundled
  into the built artefact.
- Never log raw token values anywhere.
- The default architecture is stateless (no server-side session).
  If requirements emerge that would benefit from server-side
  sessions (e.g. immediate token revocation, high-security
  compliance contexts), **stop and ask the developer** before
  implementing session state.

---

## Choose a provider strategy

**Before writing any auth code**, document the chosen option in
`contract.md` under a section named `## Authentication strategy`.

The choice is driven by the project's audience size and provider
requirements:

### Option A — True OIDC (small/internal or federated audience)

Use when all providers expose a standard OIDC discovery document
at `/.well-known/openid-configuration`. No backend token exchange
logic is required.

**Cloud providers** (managed):
- Google Identity
- Microsoft Entra ID

**Self-hosted federation layer**:
- Keycloak — configure upstream social/AD providers inside it;
  Vue and FastAPI code remains identical to the managed-provider
  case. Document the Keycloak configuration in
  `docs/developer/auth.md`.

GitHub and Twitter are explicitly **out of scope** for Option A
because they do not implement OIDC. Document this exclusion in
`contract.md` if applicable.

### Option B — OAuth2 userinfo normalization (large/public audience)

Use when GitHub, Twitter, or other non-OIDC providers must be
supported and the user base is large (broad attack surface).

- Vue still performs authorization code + PKCE.
- A dedicated `POST /auth/exchange` endpoint on FastAPI:
  1. Receives the authorization code.
  2. Exchanges it at the upstream provider (holds the
     `client_secret` server-side).
  3. Calls the provider's userinfo or `/user` endpoint.
  4. Normalizes claims to a standard shape:
     `sub`, `email`, `name`, `picture`.
  5. Issues a project-signed JWT (via `pyjwt`).
- One provider adapter per upstream (interface-based):

  ```python
  class ProviderAdapter(Protocol):
      async def exchange(
          self,
          code: str,
          code_verifier: str,
      ) -> NormalizedUser: ...
  ```

- FastAPI gains an internal "auth client" module that is separate
  from the resource-server validation logic.
- The PKCE `code_verifier` must be sent by the frontend and
  validated by the backend during the exchange.
- All project-issued JWTs are validated by the same
  `get_current_user` dependency as Option A.

---

## Frontend rules (all options)

### Package

```
npm install oidc-client-ts
```

`oidc-client-ts` is the only permitted OIDC library.

### UserManager configuration

```typescript
// src/auth/oidc.ts
import { UserManager, WebStorageStateStore } from 'oidc-client-ts'

// ADAPT: storage is project-specific — choose one:
//   WebStorageStateStore({ store: window.sessionStorage })
//   WebStorageStateStore({ store: window.localStorage })
//   In-memory (default, most secure, lost on reload)
export const userManager = new UserManager({
  authority: import.meta.env.VITE_OIDC_AUTHORITY,
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID,
  redirect_uri: import.meta.env.VITE_OIDC_REDIRECT_URI,
  post_logout_redirect_uri:
    import.meta.env.VITE_OIDC_POST_LOGOUT_URI,
  scope: 'openid email profile',
  response_type: 'code',
  automaticSilentRenew: true,
})
```

Token storage strategy is left unspecified. Document the choice
and its trade-offs in `contract.md`:

| Strategy | Pro | Con |
|---|---|---|
| Memory | Safest (no XSS persistence) | Lost on page reload |
| sessionStorage | Survives reload within tab | Lost on new tab |
| localStorage | Persistent | Accessible to XSS |

### TokenProvider wiring

Wire `oidc-client-ts` into the core `TokenProvider` seam at
bootstrap (in `main.ts`):

```typescript
import { setTokenProvider } from './api/token'
import { userManager } from './auth/oidc'

setTokenProvider({
  getToken: async () => {
    const user = await userManager.getUser()
    return user?.access_token ?? null
  },
})
```

### Routes

Three routes are always required:

| Path | Component | Purpose |
|---|---|---|
| `/login` | `LoginView.vue` | OIDC redirect interstitial |
| `/auth/callback` | `AuthCallbackView.vue` | Exchange code, store tokens |
| `/auth/logout` | *(inline redirect)* | Call `signoutRedirect` |

`LoginView.vue` must:

1. Read `returnTo` from the route query (passed by the guard).
2. Call `userManager.signinRedirect({ state: returnTo })`.
3. Show a loading spinner while the redirect is pending.

```typescript
// src/views/LoginView.vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { userManager } from '../auth/oidc'

const route = useRoute()

onMounted(async () => {
  const returnTo = (route.query.returnTo as string) ?? '/'
  await userManager.signinRedirect({ state: returnTo })
})
```

`AuthCallbackView.vue` must:

1. Call `userManager.signinRedirectCallback()`.
2. Read `user.state` — this is the `returnTo` value that
   `LoginView` passed as the OIDC `state` parameter when
   calling `signinRedirect`. Redirect there; otherwise
   redirect to `/`.
3. Handle errors and display a user-visible message.

### Navigation guard

**Important**: do NOT call `signinRedirect()` directly from
the guard and then `return false`. This causes Vue Router 4
to call `history.go(-1)` (to restore the previous URL) which
races with the `window.location.href` assignment made by
`signinRedirect`, creating an infinite redirect loop.

Instead, redirect to the `/login` route and let that component
call `signinRedirect` from `onMounted`:

```typescript
// src/router/index.ts
router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    const user = await userManager.getUser()
    if (!user || user.expired) {
      return {
        path: '/login',
        query: { returnTo: to.fullPath },
      }
    }
  }
})
```

The full `returnTo` chain is:
1. Guard passes `to.fullPath` as `query.returnTo` to `/login`.
2. `LoginView` passes it as `state` to `signinRedirect`.
3. After Keycloak redirects back, `AuthCallbackView` reads
   `user.state` to restore the protected route.

- Mark protected routes with `meta: { requiresAuth: true }`.

### Logout

```typescript
await userManager.signoutRedirect()
// or for silent/popup logout:
await userManager.signoutSilent()
```

---

## Backend rules (Options A and C)

### Package

```
uv add pyjwt[crypto] httpx
```

`pyjwt` is the only permitted JWT library. Do not use
`python-jose`, `authlib` for validation, or any other JWT library.

### OIDC discovery and JWKS

```python
# app/auth/jwks.py
import httpx
import jwt
from functools import lru_cache

@lru_cache(maxsize=1)
def get_jwks_client(authority: str) -> jwt.PyJWKClient:
    """Return a cached JWKS client for the given authority.

    :param authority: OIDC issuer base URL.
    :returns: Configured PyJWKClient with auto key refresh.
    """
    discovery_url = f"{authority.rstrip('/')}
/.well-known/openid-configuration"
    with httpx.Client() as client:
        doc = client.get(discovery_url).raise_for_status().json()
    return jwt.PyJWKClient(doc["jwks_uri"])
```

- Cache the `PyJWKClient`. It handles unknown `kid` by
  re-fetching the JWKS automatically.
- Never hard-code JWKS URIs; always resolve from discovery.

### Token validation dependency

```python
# app/auth/dependencies.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.auth.jwks import get_jwks_client

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    settings = Depends(get_settings),
) -> dict:
    """Validate the bearer token and return decoded claims.

    :param credentials: Authorization header value.
    :param settings: Application configuration.
    :returns: Decoded JWT payload dict.
    :raises HTTPException: 401 if token is invalid or expired.
    ---
    Route handlers receive the decoded payload; they must not
    perform raw JWT operations themselves.
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
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return payload
```

- Validate `exp`, `nbf`, `aud`, and `iss` on every call.
- Inject `get_current_user` into every protected route via
  `Depends`.
- Never expose raw exception messages to the client.

### Required environment variables

Add to `Settings`:

```python
OIDC_AUTHORITY: str        # e.g. https://accounts.google.com
OIDC_AUDIENCE: str         # client_id or resource identifier
OIDC_ISSUER: str           # must match token iss claim
```

---

## Backend rules — Option B additions

In addition to the validation rules above:

### Exchange endpoint

```python
# app/routers/auth.py
@router.post("/auth/exchange")
async def exchange_code(
    body: ExchangeRequest,
    settings = Depends(get_settings),
) -> TokenResponse:
    """Exchange an authorization code for a project JWT.

    Accepts the code and PKCE verifier from the frontend,
    exchanges at the upstream provider, normalizes the user
    claims, and returns a signed project JWT.
    """
```

The `ExchangeRequest` schema includes:

- `code: str` — authorization code
- `code_verifier: str` — PKCE verifier
- `provider: str` — identifies which adapter to use

### Provider adapter interface

```python
from typing import Protocol

class ProviderAdapter(Protocol):
    async def exchange(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> NormalizedUser: ...

class NormalizedUser(BaseModel):
    sub: str
    email: str
    name: str | None = None
    picture: str | None = None
```

One adapter per provider, registered in a dict keyed by provider
name. New providers add one file, no other changes.

---

## Testing

### Backend

- Mock the JWKS endpoint with `respx` or `pytest-httpserver`.
- Test cases required: valid token, expired token, wrong audience,
  wrong issuer, tampered signature.
- Never make real HTTP calls to identity providers in tests.

### Frontend

- Mock `userManager` methods with `vi.fn()` in vitest.
- Test the navigation guard with mocked `getUser()` returning
  valid user, expired user, and `null`.
- Test `AuthCallbackView` with mocked
  `signinRedirectCallback()`.
