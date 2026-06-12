#!/bin/sh
# Generate the runtime config served at /config.js from MT_*
# environment variables. The official nginx image runs every
# executable in /docker-entrypoint.d/ before starting nginx, and
# bundles `envsubst` (gettext) for exactly this purpose.
set -eu

template=/etc/mt/config.template.js
output=/usr/share/nginx/html/config.js

# Only substitute the MT_* placeholders so any other $… in the file
# is left untouched.
envsubst '${MT_OIDC_AUTHORITY} ${MT_OIDC_CLIENT_ID} ${MT_API_BASE_URL}' \
  <"$template" >"$output"

echo "Generated $output from environment"
