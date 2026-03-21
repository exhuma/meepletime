/**
 * Authentication composable backed by oidc-client-ts.
 *
 * Replaces the previous local password authentication.
 * State is derived directly from the UserManager so there
 * is no separate token ref to keep in sync.
 */
import { computed, ref } from 'vue'
import type { User as OidcUser } from 'oidc-client-ts'
import { userManager } from '../auth/oidc'
import type { ComputedRef } from 'vue'

const _oidcUser = ref<OidcUser | null>(null)

/** Refresh the cached OIDC user from the UserManager. */
async function _syncUser(): Promise<void> {
  _oidcUser.value = await userManager.getUser()
}

// Keep cached user in sync when tokens renew silently.
userManager.events.addUserLoaded((u) => {
  _oidcUser.value = u
})
userManager.events.addUserUnloaded(() => {
  _oidcUser.value = null
})

/**
 * Return reactive auth state and OIDC actions.
 */
export function useAuth() {
  /** True when a valid, non-expired OIDC session exists. */
  const isLoggedIn: ComputedRef<boolean> = computed(
    () =>
      _oidcUser.value !== null &&
      !_oidcUser.value.expired,
  )

  /**
   * Initiate the OIDC authorization-code + PKCE redirect.
   *
   * @param returnTo - Path to redirect to after login.
   */
  async function login(returnTo = '/'): Promise<void> {
    await userManager.signinRedirect({ state: returnTo })
  }

  /** Sign the user out and redirect to the post-logout URI. */
  async function logout(): Promise<void> {
    await userManager.signoutRedirect()
  }

  /**
   * Restore auth state from session storage on app startup.
   * Call once from App.vue before mounting.
   */
  async function loadFromStorage(): Promise<void> {
    await _syncUser()
  }

  return {
    oidcUser: _oidcUser,
    isLoggedIn,
    login,
    logout,
    loadFromStorage,
  }
}
