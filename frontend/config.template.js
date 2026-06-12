// Template for the runtime config served at /config.js.
//
// The Docker entrypoint runs `envsubst` over this file at container
// start, replacing the ${MT_*} placeholders with the matching
// environment variables. Unset variables become empty strings, in
// which case the app falls back to its build-time defaults.
window.__MT_CONFIG__ = {
  oidcAuthority: '${MT_OIDC_AUTHORITY}',
  oidcClientId: '${MT_OIDC_CLIENT_ID}',
  apiBaseUrl: '${MT_API_BASE_URL}',
}
