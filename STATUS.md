# STATUS

## What this repo is

A data pipeline + static visualization analyzing "dormant developer reactivation" on
GitHub — the theory that experienced developers (accounts pre-2019) with low historical
activity surged dramatically after AI coding tools went mainstream (~2022).

## Current state

**Phase: Scaffolded, not yet run**

All pipeline code and visualization are written. No real data has been collected yet.
The viz runs in demo mode (synthetic data) until the pipeline is executed against a
GCP project with BigQuery access.

## What's built

- [x] Full 5-step Python data pipeline (`pipeline/01` – `pipeline/05`)
- [x] BigQuery sampling query with `TABLESAMPLE` quota discipline
- [x] GitHub REST API enrichment with disk cache + rate limiting
- [x] Cohort classification logic with tunable thresholds
- [x] JSON export for visualization
- [x] Static visualization: cohort curves, scatter, timeline, inflection histogram
- [x] Demo data fallback (viz works without running the pipeline)
- [x] GitHub Actions: deploy viz to GitHub Pages
- [x] GitHub Actions: weekly pipeline run
- [x] Agent Workbench conventions (docs, scripts, working/, skills/, tests/)

## What's next

- [ ] **Run step 01** — requires GCP project + BigQuery enabled
- [ ] **Run step 03** — requires `GITHUB_TOKEN` in `.env`
- [ ] **Run step 02** — the expensive BQ scan; do this once
- [ ] **Run steps 04+05** — fast; produces real JSON for the viz
- [ ] **Deploy to GitHub Pages** — push to main; Actions auto-deploys
- [ ] Tune cohort thresholds using `notebooks/01_classification_tuning.ipynb`
- [ ] Add a "who are these people?" table to the viz (top dormant-reactivated users)
- [ ] Consider adding a free-text location field parser to approximate geography

## Open questions

- What GCP project / billing account will be used? (needs to be separate from personal)
- Should we seed with a hand-picked list of notable dormant-then-active users as a
  validation set for the classification?
- How should we handle multi-account developers (same person, different logins)?
- Is 2011–2018 the right "pre-era"? Some meaningful AI-adjacent activity started ~2019.
- How to handle the 20-commit cap in GH Archive PushEvents for bulk pushes?

## Key files to understand the current state

- `pipeline/config.py` — all thresholds and paths
- `pipeline/04_classify_cohorts.py` — cohort logic
- `viz/main.js` — demo data shape and fallback behavior
- `notebooks/00_quota_exploration.ipynb` — BQ cost estimation before running
