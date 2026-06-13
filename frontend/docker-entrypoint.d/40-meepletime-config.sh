#!/bin/sh
# Generate the runtime config served at /config.js from MEEPLETIME_*
# environment variables. The official nginx image runs every
# executable in /docker-entrypoint.d/ before starting nginx, and
# bundles `envsubst` (gettext) for exactly this purpose.
set -eu

template=/etc/meepletime/config.template.js
output=/usr/share/nginx/html/config.js

# Restrict substitution to these placeholders (whitespace-separated,
# so the newlines below are fine) and leave any other $… untouched.
vars='${MEEPLETIME_OIDC_AUTHORITY}
${MEEPLETIME_OIDC_CLIENT_ID}
${MEEPLETIME_API_BASE_URL}'

envsubst "$vars" <"$template" >"$output"

echo "Generated $output from environment"
