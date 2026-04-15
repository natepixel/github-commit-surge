"""
Step 02: Fetch per-user annual commit counts from GH Archive via BigQuery.

IMPORTANT: Run AFTER step 03 so we can JOIN against confirmed_users only.
This keeps the effective scan small (~50-150 GB) and the results targeted.

The confirmed_users.csv is uploaded to BigQuery as a temp table, then used
as a broadcast JOIN filter — BQ will prune rows for actors not in our list.

Output: data/raw/yearly_commits.parquet
  columns: login, year, push_events, commit_count
"""
import os
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline.config as cfg
from pipeline.utils.bq_client import (
    dry_run_bytes,
    ensure_dataset_exists,
    run_query,
    table_exists,
    upload_csv_as_table,
    get_client,
)
from google.cloud import bigquery

CONFIRMED_CSV = cfg.DATA_RAW / "confirmed_users.csv"
OUTPUT = cfg.DATA_RAW / "yearly_commits.parquet"

# We store the result in BQ so we never re-scan if we need to re-run downstream steps.
MATERIALIZED_TABLE = cfg.BQ_YEARLY_COMMITS_TABLE

QUERY_TEMPLATE = f"""
SELECT
  e.actor.login                      AS login,
  EXTRACT(YEAR FROM e.created_at)    AS year,
  COUNT(*)                           AS push_events,
  -- payload.commits is an array; ARRAY_LENGTH gives commits per push event.
  -- GH Archive caps this at 20 per event for large pushes, but it's the best
  -- approximation available without scanning commit-level tables separately.
  SUM(COALESCE(
    ARRAY_LENGTH(JSON_EXTRACT_ARRAY(e.payload, '$.commits')), 0
  ))                                 AS commit_count
FROM `{cfg.BQ_SOURCE_TABLE}` AS e
INNER JOIN `{cfg.BQ_CONFIRMED_USERS_TABLE}` AS u
  ON e.actor.login = u.login
WHERE e.type = 'PushEvent'
  AND _TABLE_SUFFIX BETWEEN
      '{cfg.ANALYSIS_START_YEAR}'
      AND '{cfg.ANALYSIS_END_YEAR}'
GROUP BY 1, 2
ORDER BY 1, 2
"""


def upload_confirmed_users():
    print("Uploading confirmed_users.csv to BigQuery …")
    ensure_dataset_exists()
    schema = [bigquery.SchemaField("login", "STRING")]
    upload_csv_as_table(CONFIRMED_CSV, cfg.BQ_CONFIRMED_USERS_TABLE, schema)


def materialize_to_bq():
    """Write results to a BQ table so we never re-scan the source."""
    client = get_client()
    ensure_dataset_exists()
    job_config = bigquery.QueryJobConfig(
        destination=MATERIALIZED_TABLE,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    print(f"Materializing results to {MATERIALIZED_TABLE} …")
    job = client.query(QUERY_TEMPLATE, job_config=job_config)
    job.result()
    print("Done.")


def download_to_parquet():
    """Download the materialized BQ table to local Parquet."""
    client = get_client()
    rows = client.list_rows(MATERIALIZED_TABLE)
    records = [(r.login, r.year, r.push_events, r.commit_count)
               for r in tqdm(rows, desc="Downloading")]
    df = pd.DataFrame(records, columns=["login", "year", "push_events", "commit_count"])
    df.to_parquet(OUTPUT, index=False)
    print(f"Saved {len(df):,} rows → {OUTPUT}")


def main():
    dry_run = "--dry-run" in sys.argv
    force_rescan = "--force-rescan" in sys.argv

    if not CONFIRMED_CSV.exists():
        print(f"ERROR: {CONFIRMED_CSV} not found. Run 03_enrich_github_api.py first.")
        sys.exit(1)

    n_users = sum(1 for _ in open(CONFIRMED_CSV)) - 1  # subtract header
    print(f"Confirmed users: {n_users:,}")

    # Skip the expensive BQ scan if the materialized table already exists.
    # Re-run with --force-rescan to overwrite.
    if not force_rescan and table_exists(MATERIALIZED_TABLE):
        print(f"[BQ] Materialized table {MATERIALIZED_TABLE} already exists — skipping scan.")
        print("[BQ] Pass --force-rescan to overwrite. Downloading existing table …")
        if not dry_run:
            download_to_parquet()
        return

    print("Estimating BigQuery scan cost …")
    gb = dry_run_bytes(QUERY_TEMPLATE) / 1e9
    print(f"  Estimated scan: {gb:.2f} GB  (free quota: 1000 GB/month)")

    if dry_run:
        print("Dry run complete. Pass no flags to execute.")
        return

    # Cost guard: require explicit opt-in for large scans in non-interactive mode.
    allow_large = os.getenv("BQ_ALLOW_LARGE_QUERY", "").strip().lower() in {"1", "true", "yes", "y"}
    if gb > 200 and not allow_large:
        if sys.stdin.isatty():
            confirm = input(f"[BQ] This query will scan {gb:.1f} GB. Continue? [y/N] ")
            if confirm.strip().lower() != "y":
                print("[BQ] Aborted.", file=sys.stderr)
                sys.exit(1)
        else:
            print(
                f"[BQ] Query exceeds 200 GB ({gb:.1f} GB) in non-interactive mode. "
                "Set BQ_ALLOW_LARGE_QUERY=1 to proceed.",
                file=sys.stderr,
            )
            sys.exit(1)

    upload_confirmed_users()
    materialize_to_bq()
    download_to_parquet()


if __name__ == "__main__":
    main()
