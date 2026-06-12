/**
 * Build the Vuetify instance from the design tokens.
 *
 * This is the only place that translates MeepleTime tokens into
 * Vuetify's theme + component defaults. It replaces the old
 * `brand-theme.ts` + the inline `defaults` block from `main.ts`.
 */
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { meepleTimeTokens, fonts } from './tokens'

/** Per-theme Vuetify config derived from the token colour maps. */
function buildThemes() {
  const variables = {
    'font-family-base': fonts.base,
    'font-family-display': fonts.display,
  }
  return {
    meepletimeLight: {
      dark: false,
      variables,
      colors: meepleTimeTokens.themes.meepletimeLight,
    },
    meepletimeDark: {
      dark: true,
      variables,
      colors: meepleTimeTokens.themes.meepletimeDark,
    },
  }
}

/** Create the configured Vuetify plugin for the app. */
export function createMeepleTimeVuetify() {
  return createVuetify({
    components,
    directives,
    theme: {
      defaultTheme: meepleTimeTokens.defaultTheme,
      themes: buildThemes(),
    },
    defaults: {
      // No Material ink ripple — the skin uses a tactile press
      // (translate + shadow) instead, set in skin.css / Mt* styles.
      VBtn: {
        color: 'primary',
        rounded: 'xl',
        variant: 'elevated',
        ripple: false,
      },
      VListItem: { ripple: false },
      VAppBar: { color: 'surface', elevation: 0, flat: true },
      VAvatar: { rounded: 'lg' },
      VCard: { elevation: 0, rounded: 'xl' },
      VDialog: { maxWidth: 480 },
      VList: { bgColor: 'transparent' },
      VTextField: {
        color: 'primary',
        density: 'comfortable',
        hideDetails: 'auto',
        variant: 'outlined',
      },
    },
  })
}
