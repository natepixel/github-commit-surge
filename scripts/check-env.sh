#!/usr/bin/env bash
# scripts/check-env.sh — verify .env has all required keys from .env.example
#
# Usage: ./scripts/check-env.sh

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f ".env" ]]; then
  echo "ERROR: .env not found. Run: cp .env.example .env"
  exit 1
fi

REQUIRED=(GCP_PROJECT_ID GITHUB_TOKEN)
MISSING=()

for key in "${REQUIRED[@]}"; do
  val=$(grep -E "^${key}=" .env | cut -d= -f2- | tr -d '"' | tr -d "'")
  if [[ -z "$val" ]] || [[ "$val" == "your-"* ]] || [[ "$val" == "ghp_xxx"* ]]; then
    MISSING+=("$key")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: Missing or placeholder values in .env:"
  for key in "${MISSING[@]}"; do
    echo "  - $key"
  done
  echo ""
  echo "See .env.example for setup instructions."
  exit 1
fi

echo "✓ .env looks good (required keys present)"
echo "  GCP_PROJECT_ID: $(grep '^GCP_PROJECT_ID=' .env | cut -d= -f2-)"
echo "  GITHUB_TOKEN:   [set]"
