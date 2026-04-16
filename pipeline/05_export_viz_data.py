"""
Step 05: Aggregate classified user data into JSON payloads for the frontend.

Outputs (all in data/viz/):
  cohort_curves.json        — per-cohort yearly percentile bands
  scatter_data.json         — per-user account age vs surge magnitude
  timeline.json             — aggregate commits by cohort by year
  inflection_histogram.json — distribution of inflection years
  summary.json              — top-level stats for the dashboard header
  age_surge_comparison.json — older-vs-newer and age-bin surge rates
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline.config as cfg

IN = cfg.DATA_PROCESSED / "classified_users.parquet"
OUT_DIR = cfg.DATA_VIZ

YEARS = list(range(cfg.ANALYSIS_START_YEAR, cfg.ANALYSIS_END_YEAR + 1))
AGE_GROUP_ORDER = ["0-2y", "3-5y", "6-10y", "11-15y", "16y+", "unknown"]
COHORT_LABELS = {
    "dormant_reactivated": "Dormant → Reactivated",
    "consistently_active": "Consistently Active",
    "new_surger": "New Surger",
    "always_sparse": "Always Sparse",
}
COHORT_COLORS = {
    "dormant_reactivated": "#e05c2a",
    "consistently_active": "#3a86ff",
    "new_surger": "#8ac926",
    "always_sparse": "#aaa",
}


def _sanitize_for_json(value):
    """Recursively convert NaN/inf to None for strict JSON output."""
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        return None
    return value


def write_json(path: Path, data) -> None:
    """Write strict JSON (no NaN) for frontend compatibility."""
    payload = _sanitize_for_json(data)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False))


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


def normalize_year_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize year columns to integer names and integer values."""
    rename_map = {}
    for col in df.columns:
        if isinstance(col, str) and col.isdigit():
            year = int(col)
            if year in YEARS:
                rename_map[col] = year
    if rename_map:
        df = df.rename(columns=rename_map)

    for year in YEARS:
        if year in df.columns:
            df[year] = df[year].fillna(0).astype(int)

    return df


def ensure_comparison_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill comparison columns if missing in older classified parquet files."""
    if "ai_surge" not in df.columns:
        df["ai_surge"] = (
            (df["post_mean"] >= cfg.ACTIVE_MIN_POST_MEAN)
            & (df["surge_ratio"] >= cfg.SURGE_MIN_RATIO)
        )
    if "dormant_ai_surge" not in df.columns:
        df["dormant_ai_surge"] = (
            (df["pre_mean"] <= cfg.DORMANT_MAX_PRE_MEAN)
            & df["ai_surge"]
        )
    if "older_account" not in df.columns:
        df["older_account"] = df["account_year"].apply(
            lambda year: (not pd.isna(year)) and int(year) < cfg.OLD_ACCOUNT_CUTOFF_YEAR
        )
    if "account_age_pre_2022" not in df.columns:
        df["account_age_pre_2022"] = df["account_year"].apply(
            lambda year: max(0, 2022 - int(year)) if not pd.isna(year) else None
        )
    if "age_group" not in df.columns:
        df["age_group"] = df["account_year"].apply(age_group_from_account_year)

    return df


def pct(value: float | None) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value) * 100, 2)


def export_cohort_curves(df: pd.DataFrame):
    """Per-cohort yearly p25/p50/p75/mean commit counts."""
    out = {"cohorts": {}}
    for cohort in COHORT_LABELS:
        sub = df[df["cohort"] == cohort][YEARS]
        records = []
        for year in YEARS:
            col = sub[year]
            n = int(len(col))
            if n == 0:
                p25 = p50 = p75 = mean = 0.0
            else:
                p25 = float(col.quantile(0.25))
                p50 = float(col.median())
                p75 = float(col.quantile(0.75))
                mean = float(col.mean())
            records.append(
                {
                    "year": year,
                    "p25": p25,
                    "p50": p50,
                    "p75": p75,
                    "mean": mean,
                    "n": n,
                }
            )
        out["cohorts"][cohort] = records

    out["meta"] = {
        "labels": COHORT_LABELS,
        "colors": COHORT_COLORS,
        "ai_milestones": [
            {"year": 2021, "label": "Copilot Technical Preview"},
            {"year": 2022, "label": "Copilot GA"},
            {"year": 2023, "label": "ChatGPT / Claude mainstream"},
            {"year": 2024, "label": "AI coding agents surge"},
        ],
    }

    path = OUT_DIR / "cohort_curves.json"
    write_json(path, out)
    print(f"  → {path}")


def export_scatter(df: pd.DataFrame):
    """Per-user scatter: account age vs surge magnitude."""
    sub = df[df["cohort"] != "always_sparse"].copy()
    sub = sub[sub["surge_magnitude"].notna()]
    sub["account_age"] = 2022 - sub["account_year"].fillna(2015).astype(int)

    records = sub[
        [
            "login",
            "account_age",
            "account_year",
            "surge_magnitude",
            "surge_ratio",
            "inflection_year",
            "lifetime_commits",
            "cohort",
        ]
    ].copy()

    cap = records["surge_magnitude"].quantile(0.99)
    records["surge_magnitude"] = records["surge_magnitude"].clip(upper=cap)

    out = records.to_dict(orient="records")
    path = OUT_DIR / "scatter_data.json"
    write_json(path, out)
    print(f"  → {path}  ({len(out):,} points)")


def export_timeline(df: pd.DataFrame):
    """Aggregate total commits per cohort per year."""
    records = []
    for year in YEARS:
        row = {"year": year}
        for cohort in COHORT_LABELS:
            sub = df[df["cohort"] == cohort]
            row[cohort] = int(sub[year].sum())
        row["total"] = sum(row[c] for c in COHORT_LABELS)
        records.append(row)

    path = OUT_DIR / "timeline.json"
    write_json(path, records)
    print(f"  → {path}")


def export_inflection_histogram(df: pd.DataFrame):
    """Distribution of inflection years among surging users."""
    surgers = df[df["cohort"].isin(["dormant_reactivated", "new_surger"])]
    surgers = surgers[surgers["inflection_year"].notna()]
    counts = surgers["inflection_year"].astype(int).value_counts().sort_index()
    records = [{"year": int(year), "count": int(n)} for year, n in counts.items() if year >= 2019]

    path = OUT_DIR / "inflection_histogram.json"
    write_json(path, records)
    print(f"  → {path}")


def compute_age_surge_comparison(df: pd.DataFrame) -> dict:
    valid = df[df["account_year"].notna()].copy()

    if valid.empty:
        return {
            "old_account_cutoff_year": cfg.OLD_ACCOUNT_CUTOFF_YEAR,
            "overall": {},
            "older_vs_newer": [],
            "age_bins": [],
        }

    older_vs_newer = []
    for label, sub in [("older_accounts", valid[valid["older_account"]]), ("newer_accounts", valid[~valid["older_account"]])]:
        n_users = int(len(sub))
        older_vs_newer.append(
            {
                "segment": label,
                "n_users": n_users,
                "ai_surge_rate_pct": pct(sub["ai_surge"].mean()) if n_users else None,
                "dormant_ai_surge_rate_pct": pct(sub["dormant_ai_surge"].mean()) if n_users else None,
                "median_post_mean": round(float(sub["post_mean"].median()), 2) if n_users else None,
            }
        )

    age_bins = []
    grouped = (
        valid.groupby("age_group")
        .agg(
            n_users=("login", "count"),
            ai_surge_rate=("ai_surge", "mean"),
            dormant_ai_surge_rate=("dormant_ai_surge", "mean"),
            median_post_mean=("post_mean", "median"),
        )
    )
    for age_group in AGE_GROUP_ORDER:
        if age_group not in grouped.index:
            continue
        row = grouped.loc[age_group]
        age_bins.append(
            {
                "age_group": age_group,
                "n_users": int(row["n_users"]),
                "ai_surge_rate_pct": pct(row["ai_surge_rate"]),
                "dormant_ai_surge_rate_pct": pct(row["dormant_ai_surge_rate"]),
                "median_post_mean": round(float(row["median_post_mean"]), 2),
            }
        )

    return {
        "old_account_cutoff_year": cfg.OLD_ACCOUNT_CUTOFF_YEAR,
        "overall": {
            "n_users": int(len(valid)),
            "ai_surge_rate_pct": pct(valid["ai_surge"].mean()),
            "dormant_ai_surge_rate_pct": pct(valid["dormant_ai_surge"].mean()),
        },
        "older_vs_newer": older_vs_newer,
        "age_bins": age_bins,
    }


def export_age_surge_comparison(df: pd.DataFrame) -> dict:
    comparison = compute_age_surge_comparison(df)
    path = OUT_DIR / "age_surge_comparison.json"
    write_json(path, comparison)
    print(f"  → {path}")
    return comparison


def export_summary(df: pd.DataFrame, comparison: dict):
    """Top-level stats for the dashboard header."""
    cohort_counts = df["cohort"].value_counts().to_dict()
    dormant = df[df["cohort"] == "dormant_reactivated"]

    older_segment = next((x for x in comparison.get("older_vs_newer", []) if x["segment"] == "older_accounts"), None)
    newer_segment = next((x for x in comparison.get("older_vs_newer", []) if x["segment"] == "newer_accounts"), None)

    out = {
        "total_users_analyzed": len(df),
        "cohort_counts": cohort_counts,
        "dormant_reactivated_pct": round(100 * cohort_counts.get("dormant_reactivated", 0) / len(df), 1),
        "median_surge_ratio_dormant": round(float(dormant["surge_ratio"].median()), 1),
        "peak_inflection_year": (
            int(df[df["inflection_year"].notna()]["inflection_year"].astype(int).mode().iloc[0])
            if df["inflection_year"].notna().any()
            else None
        ),
        "account_year_range": [
            int(df["account_year"].min()),
            int(df["account_year"].max()),
        ],
        "old_account_cutoff_year": cfg.OLD_ACCOUNT_CUTOFF_YEAR,
        "ai_surge_rate_older_accounts_pct": older_segment["ai_surge_rate_pct"] if older_segment else None,
        "ai_surge_rate_newer_accounts_pct": newer_segment["ai_surge_rate_pct"] if newer_segment else None,
        "dormant_ai_surge_rate_older_accounts_pct": older_segment["dormant_ai_surge_rate_pct"] if older_segment else None,
        "dormant_ai_surge_rate_newer_accounts_pct": newer_segment["dormant_ai_surge_rate_pct"] if newer_segment else None,
    }

    path = OUT_DIR / "summary.json"
    write_json(path, out)
    print(f"  → {path}")


def main():
    if not IN.exists():
        print(f"ERROR: {IN} not found. Run 04_classify_cohorts.py first.")
        sys.exit(1)

    df = pd.read_parquet(IN)
    print(f"Loaded {len(df):,} classified users")

    df = normalize_year_columns(df)
    df = ensure_comparison_columns(df)

    print("Exporting visualization data …")
    export_cohort_curves(df)
    export_scatter(df)
    export_timeline(df)
    export_inflection_histogram(df)
    comparison = export_age_surge_comparison(df)
    export_summary(df, comparison)

    print("\nDone. Copy data/viz/ into viz/data/ and open viz/index.html.")


if __name__ == "__main__":
    main()
