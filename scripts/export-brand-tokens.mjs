import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const sourcePath = path.join(rootDir, 'design', 'meepletime-brand.json')

const source = JSON.parse(await readFile(sourcePath, 'utf8'))

const frontendThemePath = path.join(
  rootDir,
  'frontend',
  'src',
  'generated',
  'brand-theme.ts',
)
const frontendCssPath = path.join(
  rootDir,
  'frontend',
  'src',
  'generated',
  'brand-tokens.css',
)
const keycloakCssPath = path.join(
  rootDir,
  'assets',
  'keycloak',
  'themes',
  'meepletime',
  'login',
  'resources',
  'css',
  'brand-tokens.css',
)

const fontImports = source.fonts.imports
  .map((url) => `@import url('${url}');`)
  .join('\n')

const frontendTheme = `${header('TypeScript')}
export const meepleTimeThemeOptions = {
  defaultTheme: ${quote(source.vuetify.defaultTheme)},
  themes: ${serializeThemes(source)},
} as const
`

const frontendCss = `${header('CSS')}
${fontImports}

:root {
  --mt-card-radius: ${source.shape.cardRadius};
  --mt-field-radius: ${source.shape.fieldRadius};
  --mt-button-radius: ${source.shape.buttonRadius};
  --mt-shell-width: ${source.shape.shellWidth};
  --mt-glass-blur: ${source.effects.glassBlur};
}
`

const keycloakCss = `${header('CSS')}
${fontImports}

:root {
  --mt-surface: ${source.keycloak.colors.surface};
  --mt-surface-high: ${source.keycloak.colors.surfaceHigh};
  --mt-surface-highest: ${source.keycloak.colors.surfaceHighest};
  --mt-text: ${source.keycloak.colors.text};
  --mt-text-muted: ${source.keycloak.colors.textMuted};
  --mt-outline: ${source.keycloak.colors.outline};
  --mt-primary: ${source.keycloak.colors.primary};
  --mt-primary-deep: ${source.keycloak.colors.primaryDeep};
  --mt-on-primary: ${source.keycloak.colors.onPrimary};
  --mt-shadow: ${source.keycloak.colors.shadow};
  --mt-error: ${source.keycloak.colors.error};
  --mt-error-bg: ${source.keycloak.colors.errorBg};
  --mt-card-radius: ${source.shape.cardRadius};
  --mt-field-radius: ${source.shape.fieldRadius};
  --mt-button-radius: ${source.shape.buttonRadius};
  --mt-glass-blur: ${source.effects.glassBlur};
}
`

await Promise.all([
  writeOutput(frontendThemePath, frontendTheme),
  writeOutput(frontendCssPath, frontendCss),
  writeOutput(keycloakCssPath, keycloakCss),
])

function header(kind) {
  return [
    `/* Auto-generated ${kind} file. */`,
    '/* Source: design/meepletime-brand.json */',
    '/* Run: npm run brand:sync */',
  ].join('\n')
}

function quote(value) {
  return JSON.stringify(value)
}

function serializeThemes(brandSource) {
  const themes = Object.entries(brandSource.vuetify.themes)
    .map(([name, theme]) => {
      const variables = {
        'font-family-base': brandSource.fonts.base,
        'font-family-display': brandSource.fonts.display,
      }
      return [
        `${quote(name)}: {`,
        `  dark: ${theme.dark},`,
        `  variables: ${serializeObject(variables, 2)},`,
        `  colors: ${serializeObject(theme.colors, 2)},`,
        '}',
      ].join('\n')
    })
    .join(',\n')

  return `{
${indent(themes, 2)}
}`
}

function serializeObject(value, spaces) {
  const entries = Object.entries(value)
    .map(([key, item]) => `${quote(key)}: ${quote(item)}`)
    .join(',\n')

  return `{
${indent(entries, spaces + 2)}
${' '.repeat(spaces)}}`
}

function indent(value, spaces) {
  return value
    .split('\n')
    .map((line) => `${' '.repeat(spaces)}${line}`)
    .join('\n')
}

async function writeOutput(filePath, content) {
  await mkdir(path.dirname(filePath), { recursive: true })
  await writeFile(filePath, `${content.trim()}\n`, 'utf8')
}
