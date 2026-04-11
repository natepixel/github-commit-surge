# Skill: Run the Data Pipeline

## Purpose

Execute the 5-step pipeline to generate fresh viz data from GH Archive.

## When to use it

- First-time data collection
- Periodic refresh (the weekly GitHub Action handles this automatically)
- After changing cohort thresholds in `pipeline/config.py`

## Prerequisites

```bash
cp .env.example .env          # fill in GCP_PROJECT_ID and GITHUB_TOKEN
./scripts/check-env.sh        # verify credentials
pip install -r requirements.txt
gcloud auth application-default login   # for local BigQuery access
```

## Steps

### Step 01 — Sample candidate users (~10 GB BQ scan, run once)
```bash
# Dry-run first to check cost
python pipeline/01_sample_users.py --dry-run

# Execute
python pipeline/01_sample_users.py
# Output: data/raw/sampled_users.parquet  (~60k rows)
```

### Step 03 — Enrich via GitHub API (~10 hours first run, cached after)
```bash
python pipeline/03_enrich_github_api.py
# Output: data/raw/gh_profiles.parquet
#         data/raw/confirmed_users.csv   ← required for step 02
```

### Step 02 — Fetch yearly commits from BigQuery (**run ONCE, ~100 GB scan**)
```bash
# ALWAYS dry-run first
python pipeline/02_fetch_yearly_commits.py --dry-run

# Only execute if cost is acceptable and confirmed_users.csv exists
python pipeline/02_fetch_yearly_commits.py
# Output: data/raw/yearly_commits.parquet
#         BigQuery table: BQ_DATASET.yearly_commits (materialized, cheap to re-query)
```

> **Warning:** If `data/raw/yearly_commits.parquet` already exists, skip this step.
> Re-running it unnecessarily burns ~100 GB of your monthly quota.

### Step 04 — Classify cohorts (fast, safe to re-run)
```bash
python pipeline/04_classify_cohorts.py
# Output: data/processed/classified_users.parquet
# Prints: cohort distribution table
```

### Step 05 — Export viz data (fast, safe to re-run)
```bash
python pipeline/05_export_viz_data.py
# Output: data/viz/cohort_curves.json
#         data/viz/scatter_data.json
#         data/viz/timeline.json
#         data/viz/inflection_histogram.json
#         data/viz/summary.json
```

### Sync to viz
```bash
cp data/viz/*.json viz/data/
```

## Expected output

After step 05, `./scripts/status.sh` should show ✓ for all `data/viz/*.json` files.
Open `viz/index.html` in a browser (or run `./scripts/dev.sh`) to see real data.

## Caveats

- Step 02 is destructive to quota — never re-run without checking the parquet exists first
- Step 03 uses a disk cache at `data/raw/gh_profiles_cache.parquet` — safe to re-run
- Step 01 samples randomly — re-running produces a different user set
- The GH Archive PushEvent payload caps commits at 20 per push — bulk imports undercount
- Bot accounts are filtered by login pattern + GitHub API `type == 'User'` check
