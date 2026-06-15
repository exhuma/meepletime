/// <reference types="vitest/config" />
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

// Resolve the app version once at config time: the CI-injected
// VITE_APP_VERSION (baked from the release git tag) wins; otherwise
// fall back to package.json so local builds still show a real value.
const pkg = JSON.parse(
  readFileSync(
    fileURLToPath(new URL('./package.json', import.meta.url)),
    'utf-8',
  ),
) as { version: string }
const appVersion = process.env.VITE_APP_VERSION || pkg.version

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  plugins: [vue(), vuetify({ autoImport: true })],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    // Pure lib/ logic runs in node; component tests opt into
    // jsdom via a per-file `// @vitest-environment jsdom` pragma.
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    globals: true,
  },
})
