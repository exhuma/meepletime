#!/usr/bin/env bash
# .devcontainer/init.bash
#
# Runs once after the devcontainer is created.
# Installs all backend and frontend dependencies, and seeds
# local env files so the developer only needs to override
# secrets they actually want to change.
#
# OIDC URLs use the nip.io hostname keycloak.127.0.0.1.nip.io
# so that the Keycloak issuer claim is identical whether the
# request originates inside the container (backend) or from the
# browser on the host machine (frontend). The backend service
# resolves this hostname via the extra_hosts entry in the
# devcontainer docker-compose.yml; the browser resolves it via
# standard DNS (nip.io encodes 127.0.0.1 in the name).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

KEYCLOAK_HOST="keycloak.127.0.0.1.nip.io"
KEYCLOAK_URL="http://${KEYCLOAK_HOST}:8080"
REALM="meepletime"
REALM_URL="${KEYCLOAK_URL}/realms/${REALM}"

echo "==> Installing Task (taskfile.dev) ..."
# Install into ~/.local/bin and ensure it is on the PATH for
# subsequent steps in this script and for the dev shell.
export PATH="${HOME}/.local/bin:${PATH}"
mkdir -p "${HOME}/.local/bin"
[ ! -f ${HOME}/.local/bin/task ] && sh -c "$(curl --location https://taskfile.dev/install.sh)" \
    -- -d -b "${HOME}/.local/bin"

echo "==> Installing backend dependencies (uv sync) ..."
command -v uv > /dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
cd "${REPO_ROOT}/backend"
uv sync

echo "==> Installing frontend dependencies (npm ci) ..."
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
cd "${REPO_ROOT}/frontend"
npm install

echo "==> Installing pre-commit hooks ..."
# pre-commit is installed into the backend venv by uv (dev dep).
# Register the hooks so they run automatically on every commit.
cd "${REPO_ROOT}"
"${REPO_ROOT}/backend/.venv/bin/pre-commit" install

# Seed backend/.env with nip.io-based OIDC URLs so the resource
# server's iss validation matches the tokens issued by Keycloak.
if [[ ! -f "${REPO_ROOT}/backend/.env" ]]; then
    echo "==> Creating backend/.env ..."
    cat > "${REPO_ROOT}/backend/.env" <<EOF
MEEPLETIME_DATABASE_URL=postgresql://meepletime:changeme@db:5432/meepletime
MEEPLETIME_OIDC_AUTHORITY=${REALM_URL}
MEEPLETIME_OIDC_AUDIENCE=meepletime-backend
MEEPLETIME_OIDC_ISSUER=${REALM_URL}
MEEPLETIME_FRONTEND_URL=http://localhost:5173
EOF
    echo "    Edit backend/.env to set real secrets."
fi

# Seed frontend/.env.local with nip.io-based authority so
# oidc-client-ts discovers Keycloak via the same hostname the
# backend validates against.
if [[ ! -f "${REPO_ROOT}/frontend/.env.local" ]]; then
    echo "==> Creating frontend/.env.local ..."
    cat > "${REPO_ROOT}/frontend/.env.local" <<EOF
VITE_OIDC_AUTHORITY=${REALM_URL}
VITE_OIDC_CLIENT_ID=meepletime-frontend
VITE_API_BASE_URL=http://localhost:8000
EOF
    echo "    Edit frontend/.env.local to override if needed."
fi

echo ""
echo "==> Dev container ready."
echo "    Run services:"
echo "      Backend : (cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0)"
echo "      Frontend: (cd frontend && npm run dev -- --host 0.0.0.0)"
echo "    Keycloak admin: ${KEYCLOAK_URL} (admin / admin)"
echo "    Dev login:  devuser / devpass"
