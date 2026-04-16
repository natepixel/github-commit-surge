# GitHub Commit Surge

Visualizing the "dormant developer reactivation" effect — GitHub users who had sparse
commit histories before 2022 and surged after AI coding tools (Copilot, Claude Code,
Cursor) became mainstream.

**One command to start locally:** `./scripts/dev.sh`

## Hypothesis

A cohort of experienced developers (older accounts) may have gone relatively quiet,
then surged post-2022. We compare that surge signal against newer-account cohorts to
separate behavior change from pure account-growth effects.

## How it works

```
GH Archive (BigQuery)  ──┐
                          ├──▶  pipeline/  ──▶  data/viz/  ──▶  viz/ (static site)
GitHub REST/GraphQL API ──┘
```

1. **Sample** ~60k GitHub users from balanced older/newer activity windows via BigQuery
2. **Enrich** with GitHub API to confirm account age and filter bots
3. **Fetch** per-user annual commit counts 2011–2025 from BigQuery (targeted JOIN)
4. **Classify** users into cohorts: dormant-reactivated, consistently-active, new-surger, always-sparse
5. **Export** pre-aggregated JSON → static visualization

## Key files

- `README.md` — this file
- `AGENTS.md` — how AI and humans work in this repo
- `STATUS.md` — current state and open questions
- `DEPLOY.md` — deployment model (GitHub Pages + optional Cloud Run)
- `pipeline/` — Python data pipeline (5 sequential steps)
- `viz/` — static HTML/JS visualization (Observable Plot)
- `data/viz/` — pre-computed JSON output (committed, served by viz/)
  - includes `age_surge_comparison.json` for older-vs-newer surge analysis
- `notebooks/` — exploration and threshold-tuning notebooks
- `skills/` — operational runbooks

## Structure

```
github-commit-surge/
├── README.md
├── AGENTS.md
├── STATUS.md
├── DEPLOY.md
├── CONTRIBUTING.md
├── .env.example
├── requirements.txt
├── scripts/
│   ├── dev.sh            # ← start here locally
│   ├── dev.repo.sh
│   ├── check-env.sh
│   ├── status.sh
│   └── export.sh
├── pipeline/             # Python data pipeline
│   ├── 01_sample_users.py
│   ├── 02_fetch_yearly_commits.py
│   ├── 03_enrich_github_api.py
│   ├── 04_classify_cohorts.py
│   ├── 05_export_viz_data.py
│   ├── config.py
│   └── utils/
├── viz/                  # Static visualization site
│   ├── index.html
│   ├── style.css
│   ├── main.js
│   ├── charts/
│   └── data/             # ← symlink or copy of data/viz/ JSONs
├── data/
│   ├── viz/              # Committed JSON outputs (served by viz/)
│   ├── raw/              # Gitignored intermediate pipeline data
│   └── processed/        # Gitignored classification output
├── notebooks/            # Jupyter exploration
├── docs/decisions/       # Durable design decisions
├── skills/               # Operational runbooks
├── tests/                # Testing ladder
└── working/              # Scratch space (mostly gitignored)
```

## Getting started

```bash
cp .env.example .env        # fill in GCP_PROJECT_ID and GITHUB_TOKEN
./scripts/check-env.sh      # verify required config
./scripts/dev.sh            # serve the viz on localhost
```

To run the full pipeline (requires GCP + GitHub credentials):

```bash
pip install -r requirements.txt
python pipeline/01_sample_users.py
python pipeline/03_enrich_github_api.py
python pipeline/02_fetch_yearly_commits.py
python pipeline/04_classify_cohorts.py
python pipeline/05_export_viz_data.py
cp data/viz/*.json viz/data/
```

The visualization also works without running the pipeline — it ships with demo data
and falls back to it automatically when real JSON files are absent.

## Data sources

| Source | What | Quota |
|---|---|---|
| GH Archive (BigQuery) | All public PushEvents 2011–present | 1 TB/mo free |
| GitHub REST API | Account creation date, profile | 5,000 req/hr |
| GitHub GraphQL API | Yearly contribution counts | 5,000 pts/hr |
