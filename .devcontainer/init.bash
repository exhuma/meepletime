#!/usr/bin/env bash
# .devcontainer/init.bash
#
# Runs once after the devcontainer is created.
# Installs all backend and frontend dependencies, and seeds
# local env files from the checked-in example so the developer
# only needs to fill in secrets they actually want to change.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Installing backend dependencies (uv sync) ..."
pip install --quiet uv
cd "${REPO_ROOT}/backend"
uv sync

echo "==> Installing frontend dependencies (npm ci) ..."
cd "${REPO_ROOT}/frontend"
npm ci

# Seed backend/.env from .env.example if it does not exist yet.
# Developers can then override individual values in backend/.env
# without touching the shared example file.
if [[ ! -f "${REPO_ROOT}/backend/.env" ]]; then
    echo "==> Creating backend/.env from .env.example ..."
    # Keep only backend-relevant variables (no VITE_ prefix).
    grep -v '^VITE_' "${REPO_ROOT}/.env.example" \
        | grep -v '^#' \
        | grep -v '^[[:space:]]*$' \
        > "${REPO_ROOT}/backend/.env" || true
    echo "    Edit backend/.env to set real secrets before" \
         "starting the backend."
fi

# Seed frontend/.env.local from .env.example if it does not
# exist yet. Only VITE_-prefixed lines are relevant to Vite.
if [[ ! -f "${REPO_ROOT}/frontend/.env.local" ]]; then
    echo "==> Creating frontend/.env.local from .env.example ..."
    grep '^VITE_' "${REPO_ROOT}/.env.example" \
        > "${REPO_ROOT}/frontend/.env.local" || true
    echo "    Edit frontend/.env.local to adjust OIDC" \
         "coordinates if needed."
fi

echo ""
echo "==> Dev container ready."
echo "    Run services:"
echo "      Backend : cd backend && uv run uvicorn app.main:app" \
     "--reload"
echo "      Frontend: cd frontend && npm run dev"
echo "    Keycloak admin: http://localhost:8080 (admin / changeme)"
