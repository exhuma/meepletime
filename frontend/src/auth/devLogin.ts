/**
 * Development-only login helper (no Keycloak).
 *
 * Mints a real HS256 dev token at the backend `/auth/dev/login`
 * endpoint for a given identity, then stores it as an oidc-client-ts
 * session. Because the token lands in the same sessionStorage shape a
 * Keycloak login would produce, the existing TokenProvider, router
 * guard, and auth composable treat it like any other session — no
 * branching needed in those hot paths.
 *
 * Every caller is guarded by `devAuth`, so a production build folds
 * `devAuth` to `false` and tree-shakes this module away entirely.
 *
 * The list of dev identities ("presets") is a developer convenience
 * defined by the dev-only picker (see DevLoginPanel.vue) and the dev
 * manual — never fetched from or enumerated by the API.
 */
import { User } from 'oidc-client-ts'
import { userManager } from './oidc'
import api from '../api'

/** Identity claims to mint a dev token for. */
export interface DevIdentity {
  sub: string
  email: string
  name: string
}

interface DevLoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

/** Claims minted into the dev token (see app.auth.dev_token). */
interface DevClaims {
  iss: string
  sub: string
  aud: string
  exp: number
  iat: number
  email?: string
  name?: string
}

/** Decode a JWT payload segment without verifying the signature. */
function decodeClaims(token: string): DevClaims {
  const segment = token.split('.')[1]
  const json = atob(segment.replace(/-/g, '+').replace(/_/g, '/'))
  return JSON.parse(json) as DevClaims
}

/**
 * Log in as the given dev identity and persist the session.
 *
 * @param identity - The sub/email/name to embed in the dev token.
 */
export async function devLogin(identity: DevIdentity): Promise<void> {
  const res = await api.post<DevLoginResponse>('/auth/dev/login', identity)
  const claims = decodeClaims(res.access_token)
  const user = new User({
    access_token: res.access_token,
    token_type: res.token_type || 'Bearer',
    scope: 'openid email profile',
    expires_at: claims.exp,
    session_state: null,
    profile: {
      iss: claims.iss,
      sub: claims.sub,
      aud: claims.aud,
      exp: claims.exp,
      iat: claims.iat,
      email: claims.email,
      name: claims.name,
    },
  })
  await userManager.storeUser(user)
}
