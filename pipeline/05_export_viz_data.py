"""
Step 05: Aggregate classified user data into JSON payloads for the frontend.

Outputs (all in data/viz/):
  cohort_curves.json    — per-cohort yearly percentile bands
  scatter_data.json     — per-user account age vs. surge magnitude
  timeline.json         — aggregate commits by cohort by year
  inflection_histogram.json — distribution of inflection years
  summary.json          — top-level stats for the dashboard header
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
COHORT_LABELS = {
    "dormant_reactivated": "Dormant → Reactivated",
    "consistently_active": "Consistently Active",
    "new_surger":          "New Surger",
    "always_sparse":       "Always Sparse",
}
COHORT_COLORS = {
    "dormant_reactivated": "#e05c2a",
    "consistently_active": "#3a86ff",
    "new_surger":          "#8ac926",
    "always_sparse":       "#aaa",
}


def export_cohort_curves(df: pd.DataFrame):
    """Per-cohort yearly p25/p50/p75/mean commit counts."""
    out = {"cohorts": {}}
    for cohort in COHORT_LABELS:
        sub = df[df["cohort"] == cohort][YEARS]
        records = []
        for year in YEARS:
            col = sub[year]
            records.append({
                "year": year,
                "p25":  float(col.quantile(0.25)),
                "p50":  float(col.median()),
                "p75":  float(col.quantile(0.75)),
                "mean": float(col.mean()),
                "n":    int(len(col)),
            })
        out["cohorts"][cohort] = records

    out["meta"] = {
        "labels": COHORT_LABELS,
        "colors": COHORT_COLORS,
        "ai_milestones": [
            {"year": 2021, "label": "Copilot Technical Preview"},
            {"year": 2022, "label": "Copilot GA"},
            {"year": 2023, "label": "ChatGPT / Claude mainstream"},
            {"year": 2024, "label": "AI coding agents surge"},
        ]
    }

    path = OUT_DIR / "cohort_curves.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"  → {path}")


def export_scatter(df: pd.DataFrame):
    """Per-user scatter: account age vs surge magnitude."""
    # Exclude always_sparse (too noisy / boring)
    sub = df[df["cohort"] != "always_sparse"].copy()
    sub = sub[sub["surge_magnitude"].notna()]
    sub["account_age"] = 2022 - sub["account_year"].fillna(2015).astype(int)

    records = sub[[
        "login", "account_age", "account_year", "surge_magnitude",
        "surge_ratio", "inflection_year", "lifetime_commits", "cohort"
    ]].copy()

    # Cap extreme outliers for display
    cap = records["surge_magnitude"].quantile(0.99)
    records["surge_magnitude"] = records["surge_magnitude"].clip(upper=cap)

    out = records.to_dict(orient="records")
    path = OUT_DIR / "scatter_data.json"
    path.write_text(json.dumps(out, indent=2))
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
    path.write_text(json.dumps(records, indent=2))
    print(f"  → {path}")


def export_inflection_histogram(df: pd.DataFrame):
    """Distribution of inflection years among surging users."""
    surgers = df[df["cohort"].isin(["dormant_reactivated", "new_surger"])]
    surgers = surgers[surgers["inflection_year"].notna()]
    counts = surgers["inflection_year"].astype(int).value_counts().sort_index()
    records = [{"year": int(y), "count": int(n)} for y, n in counts.items() if y >= 2019]

    path = OUT_DIR / "inflection_histogram.json"
    path.write_text(json.dumps(records, indent=2))
    print(f"  → {path}")


def export_summary(df: pd.DataFrame):
    """Top-level stats for the dashboard header."""
    cohort_counts = df["cohort"].value_counts().to_dict()
    dormant = df[df["cohort"] == "dormant_reactivated"]

    out = {
        "total_users_analyzed": len(df),
        "cohort_counts": cohort_counts,
        "dormant_reactivated_pct": round(
            100 * cohort_counts.get("dormant_reactivated", 0) / len(df), 1
        ),
        "median_surge_ratio_dormant": round(float(dormant["surge_ratio"].median()), 1),
        "peak_inflection_year": int(
            df[df["inflection_year"].notna()]["inflection_year"].astype(int).mode().iloc[0]
        ) if df["inflection_year"].notna().any() else None,
        "account_year_range": [
            int(df["account_year"].min()),
            int(df["account_year"].max()),
        ],
    }

    path = OUT_DIR / "summary.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"  → {path}")


def main():
    if not IN.exists():
        print(f"ERROR: {IN} not found. Run 04_classify_cohorts.py first.")
        sys.exit(1)

    df = pd.read_parquet(IN)
    print(f"Loaded {len(df):,} classified users")

    # Coerce year columns to int
    for y in YEARS:
        if y in df.columns:
            df[y] = df[y].fillna(0).astype(int)

    print("Exporting visualization data …")
    export_cohort_curves(df)
    export_scatter(df)
    export_timeline(df)
    export_inflection_histogram(df)
    export_summary(df)

    print("\nDone. Copy data/viz/ into viz/data/ and open viz/index.html.")


if __name__ == "__main__":
    main()
