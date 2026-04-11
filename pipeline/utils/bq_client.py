"""Thin wrapper around google-cloud-bigquery with dry-run support."""
from __future__ import annotations

import sys
from typing import Optional

from google.cloud import bigquery

import pipeline.config as cfg


def get_client() -> bigquery.Client:
    return bigquery.Client(project=cfg.GCP_PROJECT_ID)


def dry_run_bytes(sql: str) -> int:
    """Return estimated bytes processed without executing the query."""
    client = get_client()
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=job_config)
    return job.total_bytes_processed


def run_query(sql: str, dry_run: bool = False) -> Optional[bigquery.table.RowIterator]:
    """Execute a query. If dry_run=True, print cost estimate and exit."""
    bytes_est = dry_run_bytes(sql)
    gb_est = bytes_est / 1e9
    print(f"[BQ] Estimated scan: {gb_est:.2f} GB", file=sys.stderr)

    if dry_run:
        print("[BQ] Dry run — not executing.", file=sys.stderr)
        return None

    if gb_est > 200:
        confirm = input(f"[BQ] This query will scan {gb_est:.1f} GB. Continue? [y/N] ")
        if confirm.strip().lower() != "y":
            print("[BQ] Aborted.", file=sys.stderr)
            sys.exit(1)

    client = get_client()
    job = client.query(sql)
    return job.result()


def ensure_dataset_exists() -> None:
    client = get_client()
    dataset_ref = bigquery.DatasetReference(cfg.GCP_PROJECT_ID, cfg.BQ_DATASET)
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        client.create_dataset(bigquery.Dataset(dataset_ref))
        print(f"[BQ] Created dataset {cfg.BQ_DATASET}", file=sys.stderr)


def upload_csv_as_table(csv_path, table_id: str, schema: list[bigquery.SchemaField]) -> None:
    """Upload a local CSV file to a BigQuery table (replaces existing)."""
    client = get_client()
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
    )
    with open(csv_path, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)
    job.result()
    print(f"[BQ] Uploaded {csv_path} → {table_id}", file=sys.stderr)
