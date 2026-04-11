#!/usr/bin/env bash
# scripts/dev.sh — primary local development entrypoint
#
# Usage: ./scripts/dev.sh
#
# Humans and AI agents should always use this script to start local development.
# Repo-specific startup logic lives in scripts/dev.repo.sh.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ── Load .env ────────────────────────────────────────────────────────────────
if [[ -f ".env" ]]; then
  set -o allexport
  # shellcheck source=/dev/null
  source .env
  set +o allexport
fi

# ── Branch state ─────────────────────────────────────────────────────────────
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
SAFE_BRANCH="${BRANCH//\//__}"
SAFE_BRANCH="${SAFE_BRANCH//:/__}"
STATE_DIR="working/dev-state"
STATE_FILE="${STATE_DIR}/${SAFE_BRANCH}.env"
mkdir -p "$STATE_DIR"

# Load previous state for this branch
if [[ -f "$STATE_FILE" ]]; then
  set -o allexport
  # shellcheck source=/dev/null
  source "$STATE_FILE"
  set +o allexport
fi

# ── Port assignment ───────────────────────────────────────────────────────────
if [[ -z "${APP_PORT:-}" ]]; then
  APP_PORT=$(python3 -c "
import socket
s = socket.socket()
s.bind(('', 0))
port = s.getsockname()[1]
s.close()
print(port)
" 2>/dev/null || echo "8080")
fi
export APP_PORT

DEV_URL="http://127.0.0.1:${APP_PORT}"
export DEV_URL

# ── Repo-specific hook ────────────────────────────────────────────────────────
if [[ -f "scripts/dev.repo.sh" ]]; then
  # shellcheck source=scripts/dev.repo.sh
  source "scripts/dev.repo.sh"
  repo_dev_start
fi

# ── Persist state ─────────────────────────────────────────────────────────────
{
  echo "# dev state for branch: ${BRANCH}"
  echo "# written: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "APP_PORT=${APP_PORT}"
  echo "DEV_URL=${DEV_URL}"
  echo "BRANCH=${BRANCH}"
} > "$STATE_FILE"

echo ""
echo "──────────────────────────────────────────"
echo "  Branch: ${BRANCH}"
echo "  Dev URL: ${DEV_URL}"
echo "  State:   ${STATE_FILE}"
echo "──────────────────────────────────────────"
