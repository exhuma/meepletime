/**
 * Application configuration, resolved at runtime with a build-time
 * fallback.
 *
 * In production the Docker entrypoint writes `window.__MT_CONFIG__`
 * from container environment variables (see `config.template.js`), so a
 * single static image can target any Keycloak realm or backend without
 * a rebuild. In local development that global is absent and the Vite
 * `import.meta.env.VITE_*` values are used instead.
 */

/** Shape of the runtime config injected as `window.__MT_CONFIG__`. */
interface RuntimeConfig {
  oidcAuthority?: string
  oidcClientId?: string
  apiBaseUrl?: string
}

declare global {
  interface Window {
    __MT_CONFIG__?: RuntimeConfig
  }
}

const runtime: RuntimeConfig = window.__MT_CONFIG__ ?? {}

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
