/**
 * Application configuration, resolved at runtime with a build-time
 * fallback.
 *
 * In production the Docker entrypoint writes `window.__MEEPLETIME_CONFIG__`
 * from container environment variables (see `config.template.js`), so a
 * single static image can target any Keycloak realm or backend without
 * a rebuild. In local development that global is absent and the Vite
 * `import.meta.env.VITE_*` values are used instead.
 */

/** Shape of the config injected as `window.__MEEPLETIME_CONFIG__`. */
interface RuntimeConfig {
  oidcAuthority?: string
  oidcClientId?: string
  apiBaseUrl?: string
}

declare global {
  interface Window {
    __MEEPLETIME_CONFIG__?: RuntimeConfig
  }
}

const runtime: RuntimeConfig = window.__MEEPLETIME_CONFIG__ ?? {}

/** Keycloak OIDC authority (issuer) URL. */
export const oidcAuthority: string =
  runtime.oidcAuthority || (import.meta.env.VITE_OIDC_AUTHORITY as string)

/** Public OIDC client id used for the PKCE flow. */
export const oidcClientId: string =
  runtime.oidcClientId || (import.meta.env.VITE_OIDC_CLIENT_ID as string)

/** Base URL of the backend API. */
export const apiBaseUrl: string =
  runtime.apiBaseUrl ||
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  'http://localhost:8000'

/**
 * Whether the dev-only in-app login (no Keycloak) is enabled.
 *
 * Two independent gates, both required:
 *
 * - `import.meta.env.DEV` is `true` only under the Vite dev server
 *   and is replaced with a literal `false` in *any* production
 *   build. Because it folds to `false` statically, Rollup
 *   dead-code-eliminates the dev-login UI and helper, so they
 *   never ship in a built artefact (verify: `grep -r auth/dev
 *   dist/` is empty).
 * - `VITE_DEV_AUTH=true` is the explicit opt-in a developer must
 *   set, so dev login is off by default even locally.
 *
 * Deliberately **not** part of `RuntimeConfig`: it is never read
 * from `window.__MEEPLETIME_CONFIG__`, so the production runtime
 * config mechanism cannot turn it on either.
 */
export const devAuth: boolean =
  import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH === 'true'
