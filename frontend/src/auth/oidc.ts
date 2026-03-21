/**
 * OIDC UserManager configuration for Keycloak Option A.
 *
 * Reads Keycloak coordinates from Vite environment variables.
 * All VITE_OIDC_* variables must be set in .env or .env.local.
 */
import {
  UserManager,
  WebStorageStateStore,
} from 'oidc-client-ts'

/**
 * Singleton UserManager used across the entire application.
 *
 * Uses sessionStorage so that the session survives page reloads
 * within the same tab but is not shared across tabs.
 */
export const userManager = new UserManager({
  authority: import.meta.env.VITE_OIDC_AUTHORITY as string,
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID as string,
  redirect_uri:
    import.meta.env.VITE_OIDC_REDIRECT_URI as string,
  post_logout_redirect_uri:
    import.meta.env.VITE_OIDC_POST_LOGOUT_URI as string,
  scope: 'openid email profile',
  response_type: 'code',
  automaticSilentRenew: true,
  userStore: new WebStorageStateStore({
    store: window.sessionStorage,
  }),
})
