#!/usr/bin/env bash
# scripts/export.sh — bundle committed tree for external AI review
#
# Creates a timestamped .zip of the committed git tree (no gitignored files)
# and writes it to working/export/. Useful for handing off to external AI tools.
#
# Usage: ./scripts/export.sh

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
SAFE_BRANCH="${BRANCH//\//__}"
OUTFILE="working/export/${SAFE_BRANCH}_${TIMESTAMP}.zip"

mkdir -p working/export

git archive HEAD --format=zip -o "$OUTFILE"

SIZE=$(du -sh "$OUTFILE" | cut -f1)
echo "Created: ${OUTFILE} (${SIZE})"
echo ""
echo "Use this with working/ask-ai/TEMPLATE.md for external AI handoffs."
