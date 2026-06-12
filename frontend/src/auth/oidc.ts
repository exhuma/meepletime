/**
 * OIDC UserManager configuration for Keycloak Option A.
 *
 * Keycloak coordinates come from `../config`, which resolves them at
 * runtime (`window.__MT_CONFIG__`) with a Vite `VITE_*` build-time
 * fallback for local development.
 */
import { UserManager, WebStorageStateStore } from 'oidc-client-ts'
import { oidcAuthority, oidcClientId } from '../config'

/**
 * Singleton UserManager used across the entire application.
 *
 * Uses sessionStorage so that the session survives page reloads
 * within the same tab but is not shared across tabs.
 */
export const userManager = new UserManager({
  authority: oidcAuthority,
  client_id: oidcClientId,
  // Derived at runtime so the callback origin always matches
  // the origin where signinRedirect() was called, keeping
  // sessionStorage accessible throughout the PKCE flow.
  redirect_uri: `${window.location.origin}/auth/callback`,
  post_logout_redirect_uri: `${window.location.origin}/`,
  scope: 'openid email profile',
  response_type: 'code',
  automaticSilentRenew: true,
  userStore: new WebStorageStateStore({
    store: window.sessionStorage,
  }),
})
