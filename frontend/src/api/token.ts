/**
 * Token provider abstraction — the OIDC integration seam.
 *
 * Authentication is handled exclusively via Keycloak (OIDC Option A).
 * The active provider is set at bootstrap in main.ts by calling
 * setTokenProvider() with an implementation that reads the access
 * token from sessionStorage using the oidc-client-ts key format:
 *
 *   oidc.user:<authority>:<client_id>
 *
 * The API server validates the bearer token as a stateless OAuth
 * resource server using Keycloak's JWKS endpoint.
 */

export interface TokenProvider {
  /**
   * Return the current bearer access token, or null when the
   * user is not authenticated.
   */
  getToken(): string | null
}

const _null: TokenProvider = {
  getToken: () => null,
}

let _provider: TokenProvider = _null

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
