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
  primary: '#d8492f',
  'on-primary': '#ffffff',
  'primary-container': '#ffd9cf',
  'on-primary-container': '#5b1704',
  'primary-accent': '#d8492f',
  secondary: palette.wood500,
  'on-secondary': '#ffffff',
  'secondary-container': '#ecdcc4',
  'on-secondary-container': '#3a2a16',
  tertiary: palette.clay,
  'on-tertiary': '#ffffff',
  'tertiary-container': '#f7d8b8',
  'on-tertiary-container': '#4a2400',
  attend: '#6f8f5f',
  'on-attend': '#ffffff',
  'attend-container': '#dbe7c8',
  'on-attend-container': '#243218',
  host: '#c4502c',
  'on-host': '#ffffff',
  'host-container': '#ffd9cf',
  'on-host-container': '#5b1704',
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

/** Game-night tabletop: Stitch Warmer Dark. */
const dark: ThemeColors = {
  background: '#1a1614',
  'on-background': '#ede0dc',
  surface: '#1a1614',
  'on-surface': '#ede0dc',
  'surface-variant': '#433a35',
  'on-surface-variant': '#d0c4c1',
  'surface-container-lowest': '#120e0c',
  'surface-container-low': '#26211e',
  'surface-container': '#2e2824',
  'surface-container-high': '#39312c',
  'surface-container-highest': '#433a35',
  'surface-dim': '#1a1614',
  'surface-bright': '#4d423d',
  'surface-tint': '#f75f2d',
  outline: '#9c8e8b',
  'outline-variant': '#5a4139',
  primary: '#f75f2d',
  'on-primary': '#3a0a00',
  'primary-container': '#7a2e16',
  'on-primary-container': '#ffdbd0',
  'primary-accent': '#ffb59f',
  secondary: '#a3b18a',
  'on-secondary': '#1d2418',
  'secondary-container': '#3a4a2c',
  'on-secondary-container': '#d6e4c0',
  tertiary: '#ffb95f',
  'on-tertiary': '#472a00',
  'tertiary-container': '#653e00',
  'on-tertiary-container': '#ffddb8',
  attend: '#a3b18a',
  'on-attend': '#1d2418',
  'attend-container': '#3a4a2c',
  'on-attend-container': '#d6e4c0',
  host: '#ffb59f',
  'on-host': '#5e1700',
  'host-container': '#7a2e16',
  'on-host-container': '#ffdbd0',
  viable: '#ffb95f',
  'on-viable': '#472a00',
  'viable-container': '#5a3d12',
  'on-viable-container': '#ffddb8',
  error: '#ffb4ab',
  'on-error': '#690005',
  'error-container': '#93000a',
  'on-error-container': '#ffdad6',
  'inverse-surface': '#ede0dc',
  'inverse-on-surface': '#2e2927',
  'inverse-primary': '#ae3100',
}

/** Type families (also declared to Vuetify as theme `variables`). */
export const fonts = {
  base: "'Plus Jakarta Sans', sans-serif",
  display: "'Noto Serif', Georgia, serif",
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
