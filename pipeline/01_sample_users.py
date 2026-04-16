"""
Step 01: Sample candidate GitHub usernames from GH Archive via BigQuery.

Strategy: balanced sampling across older and newer activity windows so we can
compare surge prevalence by account-age cohort.

- older activity window: 2015-2018
- newer activity window: 2022-2025

Output: data/raw/sampled_users.parquet  (columns: login)
"""
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Allow running as a script from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline.config as cfg
from pipeline.utils.bq_client import dry_run_bytes, run_query

OLDER_LIMIT = max(1, cfg.SAMPLE_SIZE // 2)
NEWER_LIMIT = max(1, cfg.SAMPLE_SIZE - OLDER_LIMIT)

OLDER_QUERY = f"""
SELECT DISTINCT actor.login AS login
FROM `{cfg.BQ_SOURCE_TABLE}`
TABLESAMPLE SYSTEM (1 PERCENT)
WHERE type = 'PushEvent'
  AND _TABLE_SUFFIX BETWEEN '2015' AND '2018'
  AND actor.login IS NOT NULL
  AND actor.login NOT LIKE '%[bot]%'
  AND actor.login NOT LIKE '%bot%'
  AND actor.login NOT LIKE '%-bot'
  AND actor.login NOT LIKE '%Bot%'
LIMIT {OLDER_LIMIT}
"""

NEWER_QUERY = f"""
SELECT DISTINCT actor.login AS login
FROM `{cfg.BQ_SOURCE_TABLE}`
TABLESAMPLE SYSTEM (1 PERCENT)
WHERE type = 'PushEvent'
  AND _TABLE_SUFFIX BETWEEN '2022' AND '2025'
  AND actor.login IS NOT NULL
  AND actor.login NOT LIKE '%[bot]%'
  AND actor.login NOT LIKE '%bot%'
  AND actor.login NOT LIKE '%-bot'
  AND actor.login NOT LIKE '%Bot%'
LIMIT {NEWER_LIMIT}
"""

OUTPUT = cfg.DATA_RAW / "sampled_users.parquet"


def collect_logins(sql: str, label: str) -> list[str]:
    rows = run_query(sql)
    return [row.login for row in tqdm(rows, desc=f"Collecting {label} logins")]


def main():
    dry_run = "--dry-run" in sys.argv

    print(
        "Sampling target: "
        f"{cfg.SAMPLE_SIZE:,} users "
        f"(~{OLDER_LIMIT:,} older-window + ~{NEWER_LIMIT:,} newer-window)"
    )

    print("Estimating BigQuery scan cost …")
    older_gb = dry_run_bytes(OLDER_QUERY) / 1e9
    newer_gb = dry_run_bytes(NEWER_QUERY) / 1e9
    print(f"  older-window estimate: {older_gb:.2f} GB")
    print(f"  newer-window estimate: {newer_gb:.2f} GB")
    print(f"  total estimate: {(older_gb + newer_gb):.2f} GB")

    if dry_run:
        print("Dry run complete. Pass no flags to execute.")
        return

    print("Running older-window query …")
    older_logins = collect_logins(OLDER_QUERY, "older-window")

    print("Running newer-window query …")
    newer_logins = collect_logins(NEWER_QUERY, "newer-window")

    df = pd.DataFrame({"login": older_logins + newer_logins}).drop_duplicates()
    if len(df) > cfg.SAMPLE_SIZE:
        df = df.head(cfg.SAMPLE_SIZE)

    df.to_parquet(OUTPUT, index=False)
    print(f"Saved {len(df):,} candidate logins → {OUTPUT}")


if __name__ == "__main__":
    main()
