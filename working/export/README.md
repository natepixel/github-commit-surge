# working/export/

Output directory for shareable code bundles produced by `./scripts/export.sh`.

## Usage

```bash
./scripts/export.sh
```

Creates a timestamped `.zip` of the committed git tree (no gitignored files —
no `data/raw/`, no `.env`, no `__pycache__`) and writes it here.

## What gets included

Only files committed in the current `HEAD`. Uncommitted work is excluded.

## What stays out

- `.env` and secrets
- `data/raw/` and `data/processed/` (large intermediate files, gitignored)
- `working/dev-state/`, `__pycache__/`, `.DS_Store`, etc.

## Typical workflow

1. `./scripts/export.sh` — generate the bundle
2. Attach the `.zip` to an external AI session
3. Use `working/ask-ai/TEMPLATE.md` to frame your question

Generated `.zip` files are gitignored — safe to delete anytime.
