/**
 * Design tokens — the single source of truth for the MeepleTime skin.
 *
 * Layer 3 of the architecture. Colours defined here flow into the
 * Vuetify theme (see `vuetify-theme.ts`) and become `--v-theme-*` CSS
 * variables; shape / motion / texture tokens live alongside in
 * `tokens.css` as `--mt-*` variables. Swapping the look means swapping
 * this file — nothing else references raw colour values.
 *
 * Aesthetic: a warm wooden game table. Parchment and walnut surfaces,
 * bright "meeple" accents (coral, leaf, sky, honey), chunky tactile
 * shapes.
 */

/** Raw, un-themed palette. Referenced only by the semantic maps. */
const palette = {
  // Warm neutrals (parchment by day, walnut by night)
  parchment: '#f3e7d3',
  cream: '#fdf7ec',
  wood300: '#c8a27a',
  wood500: '#9c7b53',
  wood700: '#5c4433',
  ink: '#3a2c1d',
  walnut900: '#1a1410',
  walnut800: '#221a14',
  // Meeple accents
  coral: '#d8492f',
  coralLight: '#ff8a73',
  leaf: '#4f9d5d',
  leafLight: '#8cd497',
  sky: '#3a7ca5',
  skyLight: '#8cc6e6',
  honey: '#e0a92e',
  honeyLight: '#f2c75b',
  clay: '#bb5a2e',
  clayLight: '#f0a86a',
  berry: '#ba1a1a',
  berryLight: '#ffb4ab',
} as const

/** Full colour map for one Vuetify theme. */
export type ThemeColors = Record<string, string>

/** Daylight tabletop: parchment board, ink text. */
const light: ThemeColors = {
  background: palette.parchment,
  'on-background': palette.ink,
  surface: palette.cream,
  'on-surface': palette.ink,
  'surface-variant': '#ead9c0',
  'on-surface-variant': '#7a6650',
  'surface-container-lowest': '#ffffff',
  'surface-container-low': '#fbf3e4',
  'surface-container': '#f6ebd8',
  'surface-container-high': '#efe1ca',
  'surface-container-highest': '#e7d6bb',
  'surface-dim': '#e9dac1',
  'surface-bright': palette.cream,
  'surface-tint': palette.coral,
  outline: '#b59a78',
  'outline-variant': '#e0cdb0',
  primary: palette.coral,
  'on-primary': '#ffffff',
  'primary-container': '#ffd9cf',
  'on-primary-container': '#5b1704',
  secondary: palette.wood500,
  'on-secondary': '#ffffff',
  'secondary-container': '#ecdcc4',
  'on-secondary-container': '#3a2a16',
  tertiary: palette.clay,
  'on-tertiary': '#ffffff',
  'tertiary-container': '#f7d8b8',
  'on-tertiary-container': '#4a2400',
  attend: palette.leaf,
  'on-attend': '#ffffff',
  'attend-container': '#cdeccb',
  'on-attend-container': '#123610',
  host: palette.sky,
  'on-host': '#ffffff',
  'host-container': '#cfe6f3',
  'on-host-container': '#062a40',
  viable: palette.honey,
  'on-viable': '#4a2f00',
  'viable-container': '#ffe6a8',
  'on-viable-container': '#4a2f00',
  error: palette.berry,
  'on-error': '#ffffff',
  'error-container': '#ffdad6',
  'on-error-container': '#410002',
  'inverse-surface': palette.ink,
  'inverse-on-surface': '#f7efea',
  'inverse-primary': palette.coralLight,
}

/** Game-night tabletop: dark walnut board, warm cream text. */
const dark: ThemeColors = {
  background: palette.walnut900,
  'on-background': '#efe2d4',
  surface: palette.walnut800,
  'on-surface': '#efe2d4',
  'surface-variant': '#3c2f25',
  'on-surface-variant': '#d3bda4',
  'surface-container-lowest': '#150f0b',
  'surface-container-low': palette.walnut800,
  'surface-container': '#2a201a',
  'surface-container-high': '#332720',
  'surface-container-highest': '#3e3128',
  'surface-dim': palette.walnut900,
  'surface-bright': '#473930',
  'surface-tint': palette.coralLight,
  outline: '#9b8369',
  'outline-variant': '#4f4034',
  primary: palette.coralLight,
  'on-primary': '#5b1704',
  'primary-container': '#7a2e16',
  'on-primary-container': '#ffd9cf',
  secondary: '#d8bd96',
  'on-secondary': '#3a2a16',
  'secondary-container': '#54422a',
  'on-secondary-container': '#f0ddc2',
  tertiary: palette.clayLight,
  'on-tertiary': '#4a2400',
  'tertiary-container': '#6a3a18',
  'on-tertiary-container': '#ffd8b8',
  attend: palette.leafLight,
  'on-attend': '#0c3a16',
  'attend-container': '#2c5a33',
  'on-attend-container': '#c9f0cd',
  host: palette.skyLight,
  'on-host': '#07344a',
  'host-container': '#2a5066',
  'on-host-container': '#cfe6f3',
  viable: palette.honeyLight,
  'on-viable': '#4a2f00',
  'viable-container': '#6a5012',
  'on-viable-container': '#ffe6a8',
  error: palette.berryLight,
  'on-error': '#690005',
  'error-container': '#93000a',
  'on-error-container': '#ffdad6',
  'inverse-surface': '#efe2d4',
  'inverse-on-surface': '#2e2927',
  'inverse-primary': '#8f3d21',
}

/** Type families (also declared to Vuetify as theme `variables`). */
export const fonts = {
  base: "'Nunito', sans-serif",
  display: "'Fredoka', 'Nunito', sans-serif",
} as const

/** The complete token set. A second skin = a second object like this. */
export const meepleTimeTokens = {
  defaultTheme: 'meepletimeDark',
  themes: {
    meepletimeLight: light,
    meepletimeDark: dark,
  },
  fonts,
} as const
