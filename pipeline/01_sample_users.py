"""
Step 01: Sample candidate GitHub usernames from GH Archive via BigQuery.

Strategy: TABLESAMPLE 1% of 3 years of PushEvents (2015-2018) to surface
users who were active before the AI era. Cheap scan (~10GB), diverse sample.

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

QUERY = f"""
SELECT DISTINCT actor.login AS login
FROM `{cfg.BQ_SOURCE_TABLE}`
TABLESAMPLE SYSTEM (1 PERCENT)
WHERE type = 'PushEvent'
  AND _PARTITIONTIME BETWEEN TIMESTAMP('2015-01-01') AND TIMESTAMP('2018-12-31')
  AND actor.login IS NOT NULL
  AND actor.login NOT LIKE '%[bot]%'
  AND actor.login NOT LIKE '%bot%'
  AND actor.login NOT LIKE '%-bot'
  AND actor.login NOT LIKE '%Bot%'
LIMIT {cfg.SAMPLE_SIZE}
"""

OUTPUT = cfg.DATA_RAW / "sampled_users.parquet"


def main():
    dry_run = "--dry-run" in sys.argv

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
