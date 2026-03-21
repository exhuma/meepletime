import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import router from './router'
import App from './App.vue'
import {
  setUnauthorizedHandler,
  setTokenProvider,
} from './api'
import { userManager } from './auth/oidc'

setTokenProvider({
  getToken: () => {
    // oidc-client-ts (WebStorageStateStore) stores user state
    // under the deterministic key:
    //   oidc.user:<authority>:<client_id>
    // This is the documented key format used by the library's
    // own WebStorageStateStore implementation.
    const authority =
      import.meta.env.VITE_OIDC_AUTHORITY as string
    const clientId =
      import.meta.env.VITE_OIDC_CLIENT_ID as string
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

setUnauthorizedHandler(() => {
  userManager.signinRedirect({
    state: router.currentRoute.value.fullPath,
  })
})

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      // Autumn Hearth — warm terracotta light theme
      light: {
        dark: false,
        variables: {
          'font-family-base': "'Manrope', sans-serif",
          'font-family-display': "'Manrope', sans-serif",
        },
        colors: {
          // Brand
          primary: '#ef6039',
          'on-primary': '#ffffff',
          'primary-container': '#ffdbd0',
          'on-primary-container': '#3a0a00',

          // Neutral warm secondary
          secondary: '#8c7f70',
          'on-secondary': '#ffffff',
          'secondary-container': '#f2e8e0',
          'on-secondary-container': '#2c1f17',

          // Amber tertiary accent
          tertiary: '#ae3100',
          'on-tertiary': '#ffffff',
          'tertiary-container': '#ffdbd0',
          'on-tertiary-container': '#3a0a00',

          // Surfaces — warm cream palette
          background: '#f7f3eb',
          'on-background': '#3e362e',
          surface: '#ffffff',
          'on-surface': '#3e362e',
          'surface-variant': '#f2e8e0',
          'on-surface-variant': '#8c7f70',
          'surface-container-lowest': '#ffffff',
          'surface-container-low': '#fff8f5',
          'surface-container': '#f7f3eb',
          'surface-container-high': '#f0e8e0',
          'surface-container-highest': '#eae0d8',
          'surface-dim': '#e8e0d8',
          'surface-bright': '#ffffff',
          'surface-tint': '#ef6039',

          // Outlines
          outline: '#8c7f70',
          'outline-variant': '#d6c9c0',

          // Inverse
          'inverse-surface': '#3e362e',
          'inverse-on-surface': '#f7f3eb',
          'inverse-primary': '#ffb59f',

          // Status
          error: '#ba1a1a',
          'on-error': '#ffffff',
          'error-container': '#ffdad6',
          'on-error-container': '#410002',
        },
      },

      // Warmer Midnight — charcoal-brown dark theme
      dark: {
        dark: true,
        variables: {
          'font-family-base':
            "'Plus Jakarta Sans', sans-serif",
          'font-family-display': "'Noto Serif', serif",
        },
        colors: {
          // Brand
          primary: '#ffb59f',
          'on-primary': '#5e1700',
          'primary-container': '#f75f2d',
          'on-primary-container': '#531300',

          // Sage secondary
          secondary: '#a9b88f',
          'on-secondary': '#1d2412',
          'secondary-container': '#7a8563',
          'on-secondary-container': '#1b2111',

          // Amber tertiary
          tertiary: '#ffb95f',
          'on-tertiary': '#472a00',
          'tertiary-container': '#ca8100',
          'on-tertiary-container': '#3e2400',

          // Surfaces — warm charcoal-brown
          background: '#1a1614',
          'on-background': '#eee7e3',
          surface: '#1a1614',
          'on-surface': '#eee7e3',
          'surface-variant': '#3d3430',
          'on-surface-variant': '#d7c1ba',
          'surface-container-lowest': '#14110f',
          'surface-container-low': '#26211e',
          'surface-container': '#2d2724',
          'surface-container-high': '#352d2a',
          'surface-container-highest': '#3d3430',
          'surface-dim': '#1a1614',
          'surface-bright': '#473c38',
          'surface-tint': '#ffb59f',

          // Outlines
          outline: '#a9948d',
          'outline-variant': '#5a4b45',

          // Inverse
          'inverse-surface': '#eee7e3',
          'inverse-on-surface': '#352d2a',
          'inverse-primary': '#ae3100',

          // Status
          error: '#ffb4ab',
          'on-error': '#690005',
          'error-container': '#93000a',
          'on-error-container': '#ffdad6',
        },
      },
    },
  },
})

const app = createApp(App)
app.use(router)
app.use(vuetify)
app.mount('#app')

