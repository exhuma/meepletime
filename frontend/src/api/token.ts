/**
 * Token provider abstraction — the OIDC integration seam.
 *
 * Today: reads from localStorage after a local password grant.
 *
 * When integrating oidc-client-ts, construct a UserManager and
 * call setTokenProvider() before mounting the app:
 *
 *   import { UserManager } from 'oidc-client-ts'
 *   const mgr = new UserManager({
 *     authority: 'https://accounts.google.com', // or Microsoft,
 *     client_id: '...',                          // GitHub, etc.
 *     redirect_uri: `${window.location.origin}/auth/callback`,
 *     scope: 'openid profile email',
 *   })
 *   setTokenProvider({
 *     getToken: async () =>
 *       (await mgr.getUser())?.access_token ?? null,
 *   })
 *
 * The API server validates the bearer token as a plain OAuth
 * resource server — no OIDC awareness needed on the backend.
 */

export interface TokenProvider {
  /**
   * Return the current bearer access token, or null when the
   * user is not authenticated.
   */
  getToken(): string | null
}

const _local: TokenProvider = {
  getToken: () => localStorage.getItem('meepletime_token'),
}

let _provider: TokenProvider = _local

/**
 * Replace the active token provider.
 * Call during app bootstrap, before any API request is made.
 */
export function setTokenProvider(provider: TokenProvider): void {
  _provider = provider
}

/** Return the bearer access token from the active provider. */
export function getToken(): string | null {
  return _provider.getToken()
}
