#!/usr/bin/env bash
# scripts/status.sh — show current branch status
#
# Usage: ./scripts/status.sh

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
SAFE_BRANCH="${BRANCH//\//__}"
SAFE_BRANCH="${SAFE_BRANCH//:/__}"

echo "══════════════════════════════════════════"
echo "  Branch:  ${BRANCH}"
echo "  Commit:  $(git log -1 --format='%h %s' 2>/dev/null || echo 'none')"
echo "══════════════════════════════════════════"

# Branch status note
STATUS_FILE="working/status/${SAFE_BRANCH}.md"
if [[ -f "$STATUS_FILE" ]]; then
  echo ""
  echo "── Status note (${STATUS_FILE}) ──"
  cat "$STATUS_FILE"
else
  echo ""
  echo "  No status note found at ${STATUS_FILE}"
  echo "  Create one to track branch progress."
fi

# Dev state
STATE_FILE="working/dev-state/${SAFE_BRANCH}.env"
if [[ -f "$STATE_FILE" ]]; then
  echo ""
  echo "── Dev state ──"
  cat "$STATE_FILE"
fi

# Data status
echo ""
echo "── Data status ──"
for f in data/raw/sampled_users.parquet data/raw/gh_profiles.parquet \
          data/raw/yearly_commits.parquet data/processed/classified_users.parquet; do
  if [[ -f "$f" ]]; then
    size=$(du -sh "$f" 2>/dev/null | cut -f1)
    echo "  ✓ ${f} (${size})"
  else
    echo "  ✗ ${f} (not yet generated)"
  fi
done

echo ""
echo "── Viz data ──"
for f in data/viz/cohort_curves.json data/viz/scatter_data.json \
          data/viz/timeline.json data/viz/summary.json; do
  if [[ -f "$f" ]]; then
    echo "  ✓ ${f}"
  else
    echo "  ✗ ${f}"
  fi
done
