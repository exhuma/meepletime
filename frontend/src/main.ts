import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import router from './router'
import App from './App.vue'
import { setUnauthorizedHandler, setTokenProvider } from './api'
import { userManager } from './auth/oidc'
import { meepleTimeThemeOptions } from './generated/brand-theme'

setTokenProvider({
  getToken: () => {
    // oidc-client-ts (WebStorageStateStore) stores user state
    // under the deterministic key:
    //   oidc.user:<authority>:<client_id>
    // This is the documented key format used by the library's
    // own WebStorageStateStore implementation.
    const authority = import.meta.env.VITE_OIDC_AUTHORITY as string
    const clientId = import.meta.env.VITE_OIDC_CLIENT_ID as string
    const key = `oidc.user:${authority}:${clientId}`
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

setUnauthorizedHandler(async () => {
  // Only call signinRedirect when there is genuinely no active
  // local session. If the user already has a (possibly
  // misconfigured) token, fall back to /login instead of
  // immediately re-triggering Keycloak — which would SSO-login
  // them right back and cause an infinite redirect loop.
  const user = await userManager.getUser()
  if (user && !user.expired) {
    await router.replace('/')
  } else {
    await userManager.signinRedirect({
      state: router.currentRoute.value.fullPath,
    })
  }
})

const vuetify = createVuetify({
  components,
  directives,
  theme: meepleTimeThemeOptions,
  defaults: {
    VAppBar: {
      color: 'surface',
      elevation: 0,
      flat: true,
    },
    VAvatar: {
      rounded: 'lg',
    },
    VBtn: {
      color: 'primary',
      rounded: 'xl',
      variant: 'elevated',
    },
    VCard: {
      elevation: 0,
      rounded: 'xl',
    },
    VDialog: {
      maxWidth: 480,
    },
    VList: {
      bgColor: 'transparent',
    },
    VTextField: {
      color: 'primary',
      density: 'comfortable',
      hideDetails: 'auto',
      variant: 'outlined',
    },
  },
})

const app = createApp(App)
app.use(router)
app.use(vuetify)
app.mount('#app')
