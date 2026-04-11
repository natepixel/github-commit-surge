# AGENTS.md

How AI assistants and humans should work in this repo.

## Repo purpose

Analyze GitHub commit history data to identify and visualize "dormant developer
reactivation" — experienced developers who went quiet and then surged post-2022
alongside AI coding tools. The output is a static data visualization website.

## Read these files first

1. `README.md` — project overview, structure, getting started
2. `STATUS.md` — what's done, what's next, open questions
3. `DEPLOY.md` — how the viz deploys (GitHub Pages) and pipeline runs (Cloud Run / local)
4. `pipeline/config.py` — all tunable parameters in one place
5. `working/README.md` — scratch space conventions

## Architecture in one paragraph

The pipeline is five sequential Python scripts (`pipeline/01` through `pipeline/05`).
Steps 01 and 03 can be skipped on re-runs if their output Parquet files exist.
Step 02 is the expensive BigQuery scan — run it once and it materializes to a BQ table.
Steps 04 and 05 are fast, pure-Python, and safe to re-run anytime.
The output is four JSON files in `data/viz/` that the static site (`viz/`) reads directly.

## Core rules

- `./scripts/dev.sh` is the only local startup entrypoint — serve the viz site locally.
- Never hardcode GCP project IDs or tokens in source files. Use `.env` / `pipeline/config.py`.
- All BigQuery queries **must** be dry-run first (`--dry-run` flag or `dry_run_bytes()`).
- Never re-run step 02 (`02_fetch_yearly_commits.py`) against the full BQ dataset if
  `data/raw/yearly_commits.parquet` already exists — it wastes quota.
- `data/raw/` and `data/processed/` are gitignored (large files). `data/viz/` is committed.
- Put scratch work, debug notes, and one-off experiments in `working/`.
- Keep `pipeline/config.py` as the single source of truth for thresholds and paths.

## Pipeline steps

| Script | What it does | Expensive? | Safe to re-run? |
|---|---|---|---|
| `01_sample_users.py` | BQ: sample 60k pre-2019 logins | ~10 GB scan | Yes (skips if file exists) |
| `03_enrich_github_api.py` | REST API: filter to real human accounts | ~10 API-hrs | Yes (disk cache) |
| `02_fetch_yearly_commits.py` | BQ: per-user annual commit counts 2011–2025 | ~100 GB scan | **Once only** |
| `04_classify_cohorts.py` | Pure Python: cohort classification | Fast | Yes |
| `05_export_viz_data.py` | Pure Python: generate JSON for viz | Fast | Yes |

Note: steps 01 and 03 must complete before step 02 (the confirmed_users list drives the JOIN).

## Cohort definitions (in `pipeline/config.py`)

| Cohort | Definition |
|---|---|
| `dormant_reactivated` | pre-mean ≤ 10 commits/yr AND post-mean ≥ 30 AND surge_ratio ≥ 5× |
| `consistently_active` | pre-mean ≥ 50 AND post-mean ≥ 50 |
| `new_surger` | pre-mean < 5 AND post-mean ≥ 30 |
| `always_sparse` | everything else |

The "pre" era is 2011–2018. The "post" era is 2022–2025.
Thresholds are tunable — see `notebooks/01_classification_tuning.ipynb`.

## Visualization

The viz (`viz/`) is a pure static site — no build step, no framework.
It uses Observable Plot loaded from CDN.
It works without real data (falls back to built-in demo data automatically).
Real data: copy `data/viz/*.json` into `viz/data/` after running the pipeline.

## Working folders

### `working/`
Scratch space. Gitignored except for the committed structural files.
Use it for debug notes, one-off queries, BigQuery exploration, API experiments.

### `working/status/`
Branch-specific status notes. Filename = safe branch name + `.md`
(replace `/` and `:` with `__`).

## What good AI help looks like here

- Prefer dry-running BQ queries before executing
- Respect the pipeline ordering (01→03→02→04→05)
- Keep `pipeline/config.py` as the tuning surface, not inline constants
- When classifying cohorts, explain threshold choices
- Suggest `notebooks/` for exploratory analysis before hardcoding
- Don't commit `data/raw/` or `data/processed/` — they're gitignored for size
- The viz should work in demo mode even without real data

## Secrets policy

- `.env` is local only — never committed
- `.env.example` documents all required variables
- GCP credentials: use `gcloud auth application-default login` locally, or a
  service account key stored as a GitHub Actions secret
- GitHub token needs no scopes (public data only)
