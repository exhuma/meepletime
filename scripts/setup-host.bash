#!/usr/bin/env bash
# scripts/setup-host.bash
#
# One-shot host bootstrap for running MeepleTime directly on the
# host (no dev-container). Installs project-local toolchains and
# seeds host-flavoured env files. Idempotent: existing env files are
# never overwritten. See docs/developer/host-run.md for the full
# host-run reference.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

KEYCLOAK_HOST="keycloak.127.0.0.1.nip.io"
REALM_URL="http://${KEYCLOAK_HOST}:8080/realms/meepletime"

echo "==> Ensuring uv is installed ..."
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

echo "==> Installing backend dependencies (uv sync) ..."
# uv fetches the project's pinned Python interpreter automatically.
(cd "${REPO_ROOT}/backend" && uv sync)

echo "==> Installing frontend dependencies (npm) ..."
export NVM_DIR="${NVM_DIR:-${HOME}/.nvm}"
if [[ -s "${NVM_DIR}/nvm.sh" ]]; then
    # nvm is not fully compatible with `set -u`.
    # shellcheck disable=SC1090
    set +u
    . "${NVM_DIR}/nvm.sh"
    nvm install --lts
    nvm use --lts
    set -u
else
    echo "==> nvm not found; using preinstalled node/npm ..."
fi
(cd "${REPO_ROOT}/frontend" && npm install)

echo "==> Installing pre-commit hooks ..."
(cd "${REPO_ROOT}" \
    && "${REPO_ROOT}/backend/.venv/bin/pre-commit" install)

# --- Warn about a dev-container-flavoured backend/.env -----------
BACKEND_ENV="${REPO_ROOT}/backend/.env"
if [[ -f "${BACKEND_ENV}" ]] && grep -q '@db:5432' "${BACKEND_ENV}"; then
    echo "WARNING: ${BACKEND_ENV} points at container DB 'db:5432'." >&2
    echo "         On the host use 'localhost'. Edit it, or override" >&2
    echo "         with a shell export of MEEPLETIME_DATABASE_URL" >&2
    echo "         (shell env beats the .env file)." >&2
fi

# --- Seed host-flavoured backend/.env (only if absent) ----------
if [[ ! -f "${BACKEND_ENV}" ]]; then
    echo "==> Creating host backend/.env ..."
    cat > "${BACKEND_ENV}" <<EOF
MEEPLETIME_DATABASE_URL=postgresql://meepletime:changeme@localhost:5432/meepletime
MEEPLETIME_OIDC_AUTHORITY=${REALM_URL}
MEEPLETIME_OIDC_AUDIENCE=meepletime-backend
MEEPLETIME_OIDC_ISSUER=${REALM_URL}
MEEPLETIME_APP_BASE_URL=http://localhost:5173
# Development-only auth. NEVER set these in production.
MEEPLETIME_DEV_SHARED_SECRET=changeme
MEEPLETIME_DEV_AUTH_ENABLED=true
EOF
fi

# --- Seed host-flavoured frontend/.env.local (only if absent) ---
FRONTEND_ENV="${REPO_ROOT}/frontend/.env.local"
if [[ ! -f "${FRONTEND_ENV}" ]]; then
    echo "==> Creating host frontend/.env.local ..."
    cat > "${FRONTEND_ENV}" <<EOF
VITE_OIDC_AUTHORITY=${REALM_URL}
VITE_OIDC_CLIENT_ID=meepletime-frontend
VITE_API_BASE_URL=http://localhost:8000
# Development-only in-app login (no Keycloak). Dev server only.
VITE_DEV_AUTH=true
EOF
fi

echo ""
echo "==> Host setup complete."
echo "    Start PostgreSQL : task dev:db"
echo "    Run migrations   : task migrate"
echo "    Start backend    : task backend"
echo "    Start frontend   : task frontend"
echo "    (Optional OIDC)  : task dev:keycloak"
