/**
 * Authentication composable backed by oidc-client-ts.
 *
 * Replaces the previous local password authentication.
 * State is derived directly from the UserManager so there
 * is no separate token ref to keep in sync.
 *
 * The OIDC `sub` claim is an identity-provider detail that is
 * intentionally not exposed to the rest of the application.
 * Components should use `userId` which resolves to the
 * backend-internal UUID via GET /auth/me.
 */
import { computed, ref } from 'vue'
import type { User as OidcUser } from 'oidc-client-ts'
import { userManager } from '../auth/oidc'
import { devAuth } from '../config'
import api from '../api'
import type { User } from '../types'
import type { ComputedRef } from 'vue'

const _oidcUser = ref<OidcUser | null>(null)
const _backendUser = ref<User | null>(null)

/** Refresh the cached OIDC user from the UserManager. */
async function _syncUser(): Promise<void> {
  _oidcUser.value = await userManager.getUser()
}

/**
 * Resolve the OIDC session to a backend User record via
 * GET /auth/me and cache the result.
 *
 * Clears the cached record when no OIDC session is active.
 * Errors (network failure, unexpected 401) are logged and
 * treated as "not resolved" rather than crashing the app.
 */
async function _syncBackendUser(): Promise<void> {
  if (!_oidcUser.value || _oidcUser.value.expired) {
    _backendUser.value = null
    return
  }
  try {
    _backendUser.value = await api.get<User>('/auth/me')
  } catch (err) {
    console.error('[auth] Failed to resolve backend user:', err)
    _backendUser.value = null
  }
}

// Keep cached state in sync when tokens renew silently.
userManager.events.addUserLoaded((u) => {
  _oidcUser.value = u
  _syncBackendUser()
})
userManager.events.addUserUnloaded(() => {
  _oidcUser.value = null
  _backendUser.value = null
})

/**
 * Return reactive auth state and OIDC actions.
 */
export function useAuth() {
  /** True when a valid, non-expired OIDC session exists. */
  const isLoggedIn: ComputedRef<boolean> = computed(
    () => _oidcUser.value !== null && !_oidcUser.value.expired,
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
    if (devAuth) {
      // No Keycloak end-session endpoint exists in dev: just drop the
      // local session and return to the dev-login picker.
      await userManager.removeUser()
      _oidcUser.value = null
      _backendUser.value = null
      return
    }
    await userManager.signoutRedirect()
  }

  /**
   * Restore auth state from session storage on app startup.
   * Call once from App.vue before mounting.
   */
  async function loadFromStorage(): Promise<void> {
    await _syncUser()
    await _syncBackendUser()
  }

  /**
   * Upload (or replace) the user's profile picture and refresh the
   * cached backend user with the new resolved avatar.
   *
   * @param file - The image file to upload.
   */
  async function uploadAvatar(file: File): Promise<void> {
    const form = new FormData()
    form.append('file', file)
    _backendUser.value = await api.post<User>('/users/me/image', form)
  }

  /**
   * Remove the user's uploaded profile picture; the cached user then
   * falls back through the avatar chain (IDP picture / gravatar).
   */
  async function removeAvatar(): Promise<void> {
    _backendUser.value = await api.delete<User>('/users/me/image')
  }

  return {
    oidcUser: _oidcUser,
    /**
     * The backend-internal UUID for the authenticated user.
     * Undefined until loadFromStorage() has completed.
     */
    userId: computed(() => _backendUser.value?.id ?? undefined) as ComputedRef<
      string | undefined
    >,
    /** Display name sourced from the OIDC name claim. */
    displayName: computed(
      () => _backendUser.value?.display_name ?? null,
    ) as ComputedRef<string | null>,
    /**
     * The account email from the backend user record. This is the
     * exact address notifications fall back to when no custom
     * notification email is set, so the UI can surface it verbatim.
     */
    accountEmail: computed(
      () => _backendUser.value?.email ?? null,
    ) as ComputedRef<string | null>,
    /**
     * Resolved avatar reference for the authenticated user, or null
     * when the client should render the initials avatar.
     */
    avatarRef: computed(
      () => _backendUser.value?.avatar_ref ?? null,
    ) as ComputedRef<string | null>,
    isLoggedIn,
    login,
    logout,
    loadFromStorage,
    uploadAvatar,
    removeAvatar,
  }
}
