#!/usr/bin/env bash
# scripts/dev.repo.sh — repo-specific local dev hook for ./scripts/dev.sh
#
# Do NOT run this file directly. Use:
#   ./scripts/dev.sh
#
# This file is sourced by dev.sh after environment setup.
# Define repo_dev_start() to describe how this repo starts locally.

repo_dev_start() {
  # ── Sync viz data ──────────────────────────────────────────────────────────
  # Copy pre-computed pipeline JSON into viz/data/ if available
  if [[ -d "data/viz" ]] && compgen -G "data/viz/*.json" > /dev/null 2>&1; then
    mkdir -p viz/data
    cp data/viz/*.json viz/data/
    echo "  Synced data/viz/ → viz/data/"
  else
    echo "  No pipeline data found — viz will run in demo mode"
    echo "  (Run the pipeline steps to generate real data)"
  fi

  # ── Start local HTTP server ────────────────────────────────────────────────
  echo ""
  echo "  Starting viz server on port ${APP_PORT}..."
  echo "  Open: ${DEV_URL}"
  echo "  Press Ctrl+C to stop."
  echo ""

  # Kill any previous server on this port
  lsof -ti :"${APP_PORT}" | xargs kill -9 2>/dev/null || true

  # Serve viz/ directory
  cd viz && python3 -m http.server "${APP_PORT}" --bind 127.0.0.1
}
