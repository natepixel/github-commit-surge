"""
Step 04: Classify users into cohorts and compute surge statistics.

Inputs:
  data/raw/yearly_commits.parquet  (login, year, push_events, commit_count)
  data/raw/gh_profiles.parquet    (login, created_at, account_year, followers, …)

Output:
  data/processed/classified_users.parquet
    Includes cohort labels plus surge flags and account-age segment fields for
    older-vs-newer comparison.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline.config as cfg

COMMITS_IN = cfg.DATA_RAW / "yearly_commits.parquet"
PROFILES_IN = cfg.DATA_RAW / "gh_profiles.parquet"
OUT = cfg.DATA_PROCESSED / "classified_users.parquet"

YEARS = list(range(cfg.ANALYSIS_START_YEAR, cfg.ANALYSIS_END_YEAR + 1))
PRE_ERA = list(range(cfg.ANALYSIS_START_YEAR, cfg.OLD_ACCOUNT_CUTOFF_YEAR))
TRANSITION_ERA = list(range(cfg.OLD_ACCOUNT_CUTOFF_YEAR, 2022))
POST_ERA = list(range(2022, cfg.ANALYSIS_END_YEAR + 1))


def build_wide(df_commits: pd.DataFrame) -> pd.DataFrame:
    """Pivot long commit data to wide (one row per user, one col per year)."""
    pivot = df_commits.pivot_table(
        index="login", columns="year", values="commit_count", aggfunc="sum", fill_value=0
    )
    for year in YEARS:
        if year not in pivot.columns:
            pivot[year] = 0
    return pivot[YEARS]


def age_group_from_account_year(account_year: float | int | None) -> str:
    if pd.isna(account_year):
        return "unknown"

    age_pre_2022 = max(0, 2022 - int(account_year))
    if age_pre_2022 <= 2:
        return "0-2y"
    if age_pre_2022 <= 5:
        return "3-5y"
    if age_pre_2022 <= 10:
        return "6-10y"
    if age_pre_2022 <= 15:
        return "11-15y"
    return "16y+"


def classify_row(row: pd.Series, account_year: float | int | None) -> dict:
    pre = row[PRE_ERA]
    post = row[POST_ERA]

    pre_mean = float(pre.mean()) if PRE_ERA else 0.0
    post_mean = float(post.mean()) if POST_ERA else 0.0
    pre_max = float(pre.max()) if PRE_ERA else 0.0
    post_max = float(post.max()) if POST_ERA else 0.0
    lifetime = float(row[YEARS].sum())

    surge_ratio = post_mean / (pre_mean + 1.0)
    surge_magnitude = post_max - pre_max

    yoy = row[YEARS].diff().fillna(0)
    post_yoy = yoy[[year for year in YEARS if year >= 2019]]
    inflection_year = int(post_yoy.idxmax()) if post_yoy.max() > 0 else None

    has_account_year = not pd.isna(account_year)
    older_account = bool(has_account_year and int(account_year) < cfg.OLD_ACCOUNT_CUTOFF_YEAR)
    account_age_pre_2022 = (
        max(0, 2022 - int(account_year))
        if has_account_year
        else None
    )
    age_group = age_group_from_account_year(account_year)

    is_dormant_pre = pre_mean <= cfg.DORMANT_MAX_PRE_MEAN
    is_active_post = post_mean >= cfg.ACTIVE_MIN_POST_MEAN
    is_consistent = (
        pre_mean >= cfg.CONSISTENT_MIN_MEAN
        and post_mean >= cfg.CONSISTENT_MIN_MEAN
    )
    is_ai_surge = is_active_post and surge_ratio >= cfg.SURGE_MIN_RATIO
    is_dormant_ai_surge = is_dormant_pre and is_ai_surge
    is_new_account = has_account_year and int(account_year) >= cfg.OLD_ACCOUNT_CUTOFF_YEAR

    if older_account and is_dormant_ai_surge:
        cohort = "dormant_reactivated"
    elif is_consistent:
        cohort = "consistently_active"
    elif is_new_account and pre_mean <= cfg.NEW_SURGER_MAX_PRE_MEAN and is_ai_surge:
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
        "ai_surge": bool(is_ai_surge),
        "dormant_ai_surge": bool(is_dormant_ai_surge),
        "older_account": bool(older_account),
        "account_age_pre_2022": account_age_pre_2022,
        "age_group": age_group,
    }


def print_age_segment_summary(df: pd.DataFrame) -> None:
    valid = df[df["account_year"].notna()].copy()
    if valid.empty:
        print("\nNo account_year data available for age-segment summary.")
        return

    print("\nAI surge rates by age_group:")
    by_age = (
        valid.groupby("age_group")
        .agg(
            n_users=("login", "count"),
            ai_surge_rate=("ai_surge", "mean"),
            dormant_ai_surge_rate=("dormant_ai_surge", "mean"),
            median_post_mean=("post_mean", "median"),
        )
        .sort_values("n_users", ascending=False)
    )
    print((by_age.assign(
        ai_surge_rate=lambda x: (x["ai_surge_rate"] * 100).round(2),
        dormant_ai_surge_rate=lambda x: (x["dormant_ai_surge_rate"] * 100).round(2),
    )).to_string())

    print("\nOlder vs newer surge comparison:")
    by_old_new = (
        valid.groupby("older_account")
        .agg(
            n_users=("login", "count"),
            ai_surge_rate=("ai_surge", "mean"),
            dormant_ai_surge_rate=("dormant_ai_surge", "mean"),
        )
        .rename(index={True: "older_accounts", False: "newer_accounts"})
    )
    print((by_old_new.assign(
        ai_surge_rate=lambda x: (x["ai_surge_rate"] * 100).round(2),
        dormant_ai_surge_rate=lambda x: (x["dormant_ai_surge_rate"] * 100).round(2),
    )).to_string())


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

    account_year_map = dict(zip(df_profiles["login"], df_profiles["account_year"]))

    print("Classifying users …")
    classifications = [
        classify_row(wide.loc[login], account_year_map.get(login))
        for login in wide.index
    ]
    df_class = pd.DataFrame(classifications, index=wide.index).reset_index()
    df_class = df_class.rename(columns={"index": "login"})

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
    print(df_out.groupby("cohort")["surge_ratio"].describe().round(2).to_string())

    print_age_segment_summary(df_out)


if __name__ == "__main__":
    main()
