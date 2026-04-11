# Decision 002: Cohort Classification

**Date:** 2025-04

## Context

The core hypothesis is that a cohort of experienced developers (accounts pre-2019)
who were largely inactive suddenly surged post-2022. We need a classification scheme
that surfaces this signal without cherry-picking.

## Decision

Four cohorts defined by two era windows:
- **Pre era:** 2011–2018 (before widespread AI coding tools)
- **Post era:** 2022–2025 (after Copilot GA, ChatGPT, Claude)

| Cohort | Rule |
|---|---|
| `dormant_reactivated` | pre_mean ≤ 10 AND post_mean ≥ 30 AND surge_ratio ≥ 5× |
| `consistently_active` | pre_mean ≥ 50 AND post_mean ≥ 50 |
| `new_surger` | pre_mean < 5 AND post_mean ≥ 30 (account-age effect) |
| `always_sparse` | everything else |

Thresholds are in `pipeline/config.py` and tunable via `notebooks/01_classification_tuning.ipynb`.

## Alternatives considered

- **Single threshold (surge_ratio only):** Too many false positives from users who
  went from 1 commit to 6 commits (technically a 5× surge, but not interesting).
- **Percentile-based:** More robust to outliers but harder to explain and reproduce.
- **Manual labeling:** Ground truth for a sample, but doesn't scale.

## Why these specific numbers

- `pre_mean ≤ 10`: ~10 commits/year is roughly "occasional tinkering"
  (< 1 per month). The median pre-2019 user in the sample is well below this.
- `post_mean ≥ 30`: ~2.5 commits/month. Meaningfully active but not a prolific
  contributor (who would be 200+/year).
- `surge_ratio ≥ 5×`: A 5× increase is a strong signal; avoids classifying
  someone who went from 8 to 32 as "dormant" if they were already present.
- `pre_mean < 5` for new_surger: Separates "had account but barely used it" from
  "account existed and was active, then surged more."

## Consequences

- The `dormant_reactivated` cohort is the most analytically interesting but also
  the most sensitive to threshold choices — tune carefully
- `new_surger` isolates an important confound: accounts created 2017–2019 that
  simply matured as their owners gained skills
- The 2019–2021 "transition era" is not labeled; it acts as a buffer between eras
- Users with data only for part of the range (e.g., account created 2016) are
  handled gracefully — missing years default to 0 commits
