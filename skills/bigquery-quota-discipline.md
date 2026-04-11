# Skill: BigQuery Quota Discipline

## Purpose

Protect the 1 TB/month free quota on BigQuery when running pipeline queries.

## Rules

1. **Always dry-run before executing** any query against `bigquery-public-data.github_events`
2. **Never `SELECT *`** — project only the columns needed
3. **Always partition-prune** — include `_PARTITIONTIME BETWEEN ...` in every query
4. **Use `TABLESAMPLE`** for exploration (sampling, not full scans)
5. **Materialize step 02 results** to a table in your own project — re-queries are cheap
6. **Skip step 02** if `data/raw/yearly_commits.parquet` already exists

## How to dry-run

### From the pipeline scripts
```bash
python pipeline/01_sample_users.py --dry-run
python pipeline/02_fetch_yearly_commits.py --dry-run
```

### From Python
```python
from pipeline.utils.bq_client import dry_run_bytes
gb = dry_run_bytes(YOUR_SQL) / 1e9
print(f"Estimated scan: {gb:.1f} GB")
```

### From `bq` CLI
```bash
bq query --dry_run --nouse_legacy_sql 'SELECT ...'
```

## Estimated quota budget (first run)

| Step | Estimated scan | Notes |
|---|---|---|
| Step 01 (sampling) | ~10 GB | TABLESAMPLE 1% of 3 years |
| Step 02 (yearly commits) | ~100 GB | JOIN-filtered, run once |
| Exploration / dry runs | ~50 GB | Notebooks, re-runs |
| **Total** | **~160 GB** | Well under 1 TB free |

## After step 02 materializes

Subsequent runs of steps 04+05 never touch `bigquery-public-data` again.
They read from `YOUR_PROJECT.github_stats_work.yearly_commits` — cheap.

## Monthly refresh

The weekly GitHub Action re-runs only steps 03, 04, and 05 by default.
It skips steps 01 and 02 if the parquet files exist (committed as Actions cache).
Annual incremental refresh of step 02 costs ~15–20 GB (one new year of data).
