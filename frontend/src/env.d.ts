/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Full URL of the GitHub repository. When unset, the footer's
  // "Source code" link is hidden. See module-github-link kit.
  readonly VITE_GITHUB_REPO_URL?: string
  // Release version injected at build time (see vite.config.ts).
  readonly VITE_APP_VERSION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Build-time constant: the resolved app version. Defined in
// vite.config.ts (VITE_APP_VERSION env, falling back to package.json).
declare const __APP_VERSION__: string
