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

QUERY = f"""
WITH older_candidates AS (
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
),
newer_candidates AS (
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
)
SELECT DISTINCT login
FROM (
  SELECT login FROM older_candidates
  UNION ALL
  SELECT login FROM newer_candidates
)
LIMIT {cfg.SAMPLE_SIZE}
"""

OUTPUT = cfg.DATA_RAW / "sampled_users.parquet"


def main():
    dry_run = "--dry-run" in sys.argv

    print(
        "Sampling target: "
        f"{cfg.SAMPLE_SIZE:,} users "
        f"(~{OLDER_LIMIT:,} older-window + ~{NEWER_LIMIT:,} newer-window)"
    )

    print("Estimating BigQuery scan cost …")
    gb = dry_run_bytes(QUERY) / 1e9
    print(f"  Estimated scan: {gb:.2f} GB")

    if dry_run:
        print("Dry run complete. Pass no flags to execute.")
        return

    print("Running query …")
    rows = run_query(QUERY)
    logins = [row.login for row in tqdm(rows, desc="Collecting logins")]

    df = pd.DataFrame({"login": logins}).drop_duplicates()
    df.to_parquet(OUTPUT, index=False)
    print(f"Saved {len(df):,} candidate logins → {OUTPUT}")


if __name__ == "__main__":
    main()
