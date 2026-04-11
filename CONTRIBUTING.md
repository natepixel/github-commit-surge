# CONTRIBUTING

## How to work in this repo

Read `AGENTS.md` first — it covers the pipeline ordering, quota rules, and
conventions for both AI assistants and humans.

## Key rules

- **Never commit `.env`** — add secrets to `.env` locally, document them in `.env.example`
- **BigQuery dry-run first** — always estimate scan cost before executing step 02
- **`data/raw/` and `data/processed/` are gitignored** — do not force-add them
- **`data/viz/*.json` is committed** — these are small, pre-aggregated, and needed by the viz
- **Scratch work belongs in `working/`** — not in `pipeline/`, `viz/`, or docs
- **Threshold changes belong in `pipeline/config.py`** — not scattered in individual scripts

## Stable entrypoints

```bash
./scripts/dev.sh          # serve the viz locally
./scripts/check-env.sh    # verify .env has required keys
./scripts/status.sh       # show current branch status
./scripts/export.sh       # bundle committed tree for external AI review
```

## Promoting work

- Experiments and debug notes → `working/`
- Recurring operational procedures → `skills/`
- Durable design decisions → `docs/decisions/`
- Pipeline configuration → `pipeline/config.py`

## Commit style

Use short, lowercase imperative commits:
```
feat: add location parser for geo analysis
fix: handle GH Archive missing commit arrays
chore: refresh pipeline data
docs: update STATUS with run results
```
