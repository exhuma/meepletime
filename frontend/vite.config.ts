/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
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
