"""
Step 04: Classify users into cohorts and compute surge statistics.

Inputs:
  data/raw/yearly_commits.parquet  (login, year, push_events, commit_count)
  data/raw/gh_profiles.parquet    (login, created_at, account_year, followers, …)

Output:
  data/processed/classified_users.parquet
    columns: login, account_year, cohort, pre_mean, post_mean, surge_ratio,
             inflection_year, surge_magnitude, lifetime_commits, [year cols…]

Cohort definitions:
  dormant_reactivated  — low pre-AI activity, high post-2022, surge_ratio ≥ 5
  consistently_active  — high activity in both eras
  new_surger           — near-zero pre-2019 activity, surged post-2022
                         (account age effect; separates from truly dormant)
  always_sparse        — low activity throughout
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline.config as cfg

COMMITS_IN = cfg.DATA_RAW / "yearly_commits.parquet"
PROFILES_IN = cfg.DATA_RAW / "gh_profiles.parquet"
OUT = cfg.DATA_PROCESSED / "classified_users.parquet"

YEARS = list(range(cfg.ANALYSIS_START_YEAR, cfg.ANALYSIS_END_YEAR + 1))
PRE_ERA = list(range(2011, 2019))       # pre-AI baseline
TRANSITION_ERA = list(range(2019, 2022))
POST_ERA = list(range(2022, 2026))      # post-Copilot/Claude


def build_wide(df_commits: pd.DataFrame) -> pd.DataFrame:
    """Pivot long commit data to wide (one row per user, one col per year)."""
    pivot = df_commits.pivot_table(
        index="login", columns="year", values="commit_count", aggfunc="sum", fill_value=0
    )
    # Ensure all years present even if no data
    for y in YEARS:
        if y not in pivot.columns:
            pivot[y] = 0
    return pivot[YEARS]


def classify_row(row: pd.Series) -> dict:
    pre = row[PRE_ERA]
    post = row[POST_ERA]

    pre_mean = float(pre.mean())
    post_mean = float(post.mean())
    pre_max = float(pre.max())
    post_max = float(post.max())
    lifetime = float(row[YEARS].sum())

    surge_ratio = post_mean / (pre_mean + 1.0)
    surge_magnitude = post_max - pre_max

    # Inflection: year with the largest YoY increase from 2019 onward
    yoy = row[YEARS].diff().fillna(0)
    post_yoy = yoy[[y for y in YEARS if y >= 2019]]
    inflection_year = int(post_yoy.idxmax()) if post_yoy.max() > 0 else None

    # Cohort assignment
    is_dormant_pre = pre_mean <= cfg.DORMANT_MAX_PRE_MEAN
    is_active_post = post_mean >= cfg.ACTIVE_MIN_POST_MEAN

    if is_dormant_pre and is_active_post and surge_ratio >= cfg.SURGE_MIN_RATIO:
        cohort = "dormant_reactivated"
    elif pre_mean >= cfg.CONSISTENT_MIN_MEAN and post_mean >= cfg.CONSISTENT_MIN_MEAN:
        cohort = "consistently_active"
    elif pre_mean < 5 and is_active_post:
        cohort = "new_surger"
    else:
        cohort = "always_sparse"

    return {
        "pre_mean": round(pre_mean, 2),
        "post_mean": round(post_mean, 2),
        "surge_ratio": round(surge_ratio, 2),
        "surge_magnitude": round(surge_magnitude, 2),
        "inflection_year": inflection_year,
        "lifetime_commits": int(lifetime),
        "cohort": cohort,
    }


def main():
    if not COMMITS_IN.exists():
        print(f"ERROR: {COMMITS_IN} not found. Run 02_fetch_yearly_commits.py first.")
        sys.exit(1)
    if not PROFILES_IN.exists():
        print(f"ERROR: {PROFILES_IN} not found. Run 03_enrich_github_api.py first.")
        sys.exit(1)

    print("Loading data …")
    df_commits = pd.read_parquet(COMMITS_IN)
    df_profiles = pd.read_parquet(PROFILES_IN)[["login", "account_year", "followers", "location"]]

    print(f"  {len(df_commits):,} commit rows, {df_commits['login'].nunique():,} unique users")

    wide = build_wide(df_commits)
    print(f"  Pivot shape: {wide.shape}")

    print("Classifying users …")
    classifications = [classify_row(wide.loc[login]) for login in wide.index]
    df_class = pd.DataFrame(classifications, index=wide.index).reset_index()
    df_class = df_class.rename(columns={"index": "login"})

    # Merge with year-level commit columns and profile data
    year_cols = wide.reset_index().rename(columns={"index": "login"})
    df_out = df_class.merge(year_cols, on="login", how="left")
    df_out = df_out.merge(df_profiles, on="login", how="left")

    df_out.to_parquet(OUT, index=False)
    print(f"\nSaved {len(df_out):,} classified users → {OUT}")

    print("\nCohort distribution:")
    counts = df_out["cohort"].value_counts()
    for cohort, n in counts.items():
        pct = 100 * n / len(df_out)
        print(f"  {cohort:<25} {n:>6,}  ({pct:.1f}%)")

    print("\nSurge ratio stats by cohort:")
    print(df_out.groupby("cohort")["surge_ratio"].describe().round(1).to_string())


if __name__ == "__main__":
    main()
