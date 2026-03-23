/**
 * OIDC UserManager configuration for Keycloak Option A.
 *
 * Reads Keycloak coordinates from Vite environment variables.
 * VITE_OIDC_AUTHORITY and VITE_OIDC_CLIENT_ID must be set in
 * .env or .env.local.
 */
import { UserManager, WebStorageStateStore } from "oidc-client-ts";

/**
 * Singleton UserManager used across the entire application.
 *
 * Uses sessionStorage so that the session survives page reloads
 * within the same tab but is not shared across tabs.
 */
export const userManager = new UserManager({
  authority: import.meta.env.VITE_OIDC_AUTHORITY as string,
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID as string,
  // Derived at runtime so the callback origin always matches
  // the origin where signinRedirect() was called, keeping
  // sessionStorage accessible throughout the PKCE flow.
  redirect_uri: `${window.location.origin}/auth/callback`,
  post_logout_redirect_uri: `${window.location.origin}/`,
  scope: "openid email profile",
  response_type: "code",
  automaticSilentRenew: true,
  userStore: new WebStorageStateStore({
    store: window.sessionStorage,
  }),
});
