// Template for the runtime config served at /config.js.
//
// The Docker entrypoint runs `envsubst` over this file at container
// start, replacing the ${MEEPLETIME_*} placeholders with the matching
// environment variables. Unset variables become empty strings, in
// which case the app falls back to its build-time defaults.
window.__MEEPLETIME_CONFIG__ = {
  oidcAuthority: '${MEEPLETIME_OIDC_AUTHORITY}',
  oidcClientId: '${MEEPLETIME_OIDC_CLIENT_ID}',
  apiBaseUrl: '${MEEPLETIME_API_BASE_URL}',
}
