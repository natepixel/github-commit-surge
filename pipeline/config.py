import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Paths
ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_VIZ = ROOT / "data" / "viz"

for d in (DATA_RAW, DATA_PROCESSED, DATA_VIZ):
    d.mkdir(parents=True, exist_ok=True)

# BigQuery
GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
BQ_DATASET = os.getenv("BQ_DATASET", "github_stats_work")
BQ_SOURCE_TABLE = "githubarchive.year.*"
BQ_CONFIRMED_USERS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.confirmed_users"
BQ_YEARLY_COMMITS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.yearly_commits"

# GitHub API
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GH_API_THREADS = int(os.getenv("GH_API_THREADS", "4"))
GH_MAX_NEW_PROFILES = int(os.getenv("GH_MAX_NEW_PROFILES", "0"))

# Pipeline parameters
SAMPLE_SIZE = int(os.getenv("SAMPLE_SIZE", "60000"))
OLD_ACCOUNT_CUTOFF_YEAR = int(os.getenv("OLD_ACCOUNT_CUTOFF_YEAR", "2019"))  # Older-account boundary
ACCOUNT_CUTOFF_YEAR = OLD_ACCOUNT_CUTOFF_YEAR  # Backward-compatible alias
MIN_PRE_AI_YEARS = 2             # Must have had account for at least N years before 2022
ANALYSIS_START_YEAR = 2011
ANALYSIS_END_YEAR = 2025

# Cohort classification thresholds (tunable)
DORMANT_MAX_PRE_MEAN = 10        # ≤ N commits/year average pre-2019 = "dormant"
ACTIVE_MIN_POST_MEAN = 30        # ≥ N commits/year average post-2022 = "active"
SURGE_MIN_RATIO = 5.0            # post_mean / pre_mean must be ≥ this for "reactivated"
CONSISTENT_MIN_MEAN = 50         # Both pre and post means ≥ this = "consistently active"
NEW_SURGER_MAX_PRE_MEAN = float(os.getenv("NEW_SURGER_MAX_PRE_MEAN", "5"))
