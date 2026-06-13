import { createApp } from 'vue'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import './theme/skin.css'
import router from './router'
import App from './App.vue'
import {
  setAuthorizedHandler,
  setUnauthorizedHandler,
  setTokenProvider,
} from './api'
import { userManager } from './auth/oidc'
import { oidcAuthority, oidcClientId } from './config'
import {
  clearReauthGuard,
  markReauthAttempt,
  recentlyReauthed,
  setAuthError,
} from './auth/reauthGuard'
import { createMeepleTimeVuetify } from './theme'

setTokenProvider({
  getToken: () => {
    // oidc-client-ts (WebStorageStateStore) stores user state
    // under the deterministic key:
    //   oidc.user:<authority>:<client_id>
    // This is the documented key format used by the library's
    // own WebStorageStateStore implementation. The coordinates come
    // from `./config`, which resolves them identically for production
    // (runtime `window.__MEEPLETIME_CONFIG__`) and development
    // (`VITE_*` build-time fallback).
    const key = `oidc.user:${oidcAuthority}:${oidcClientId}`
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    try {
      const parsed = JSON.parse(raw) as {
        access_token?: string
      }
      return parsed.access_token ?? null
    } catch {
      return null
    }
  },
})

let _reauthInFlight = false

setUnauthorizedHandler(async () => {
  // A 401 means the API rejected the stored access token. This happens
  // when the token expired, or when Keycloak's signing keys rotated
  // after a restart so a still-clock-valid token no longer verifies.
  // The token will never be accepted again, so discard it and sign in
  // again — the Keycloak SSO session mints a fresh, valid token without
  // prompting. Coalesce simultaneous 401s so we redirect only once.
  if (_reauthInFlight) return
  _reauthInFlight = true
  try {
    await userManager.removeUser().catch(() => {})

    if (recentlyReauthed()) {
      // We re-authenticated moments ago and the *fresh* token was also
      // rejected. That is a real backend misconfiguration, not a stale
      // token — stop redirecting and let LoginView offer a manual retry
      // instead of looping forever.
      setAuthError()
      await router.replace('/login')
      return
    }

    markReauthAttempt()
    await userManager.signinRedirect({
      state: router.currentRoute.value.fullPath,
    })
  } finally {
    _reauthInFlight = false
  }
})

// A successful authenticated call proves the current token works, so
// reset the re-authentication loop breaker.
setAuthorizedHandler(() => clearReauthGuard())

const vuetify = createMeepleTimeVuetify()

const app = createApp(App)
app.use(router)
app.use(vuetify)
app.mount('#app')
