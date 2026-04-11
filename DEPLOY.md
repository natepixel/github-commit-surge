# DEPLOY

## Visualization (GitHub Pages)

The static site (`viz/`) deploys automatically to GitHub Pages on every push to `main`
that touches `viz/**` or `data/viz/**`.

**URL:** `https://natepixel.github.io/github-commit-surge/` *(once Pages is enabled)*

### Enable GitHub Pages

1. Go to repo Settings → Pages
2. Source: **GitHub Actions**
3. The `deploy-viz.yml` workflow handles the rest

### What deploys

- Everything in `viz/` (HTML, CSS, JS, charts)
- `data/viz/*.json` copied into `viz/data/` at deploy time
- If no JSON files exist, the site runs in demo mode automatically

---

## Data Pipeline

The pipeline is not a persistent service — it's a batch job that runs once (or weekly)
to refresh the data, then commits the resulting JSON files.

### Option A: Local run

```bash
cp .env.example .env       # add GCP_PROJECT_ID and GITHUB_TOKEN
./scripts/check-env.sh
pip install -r requirements.txt
gcloud auth application-default login   # for BigQuery access
python pipeline/01_sample_users.py
python pipeline/03_enrich_github_api.py
python pipeline/02_fetch_yearly_commits.py   # run ONCE; ~100GB BQ scan
python pipeline/04_classify_cohorts.py
python pipeline/05_export_viz_data.py
cp data/viz/*.json viz/data/
git add data/viz/ viz/data/
git commit -m "chore: refresh pipeline data"
git push
```

### Option B: GitHub Actions (automated, weekly)

The `run-pipeline.yml` workflow runs every Sunday at 4am UTC.
It requires these GitHub Actions secrets:

| Secret | Description |
|---|---|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GCP_SERVICE_ACCOUNT_KEY` | JSON key for a service account with BigQuery access |
| `GH_TOKEN` | GitHub personal access token (no scopes needed) |

The workflow skips expensive steps if output Parquet files are already cached
(checked in as GitHub Actions artifacts or committed to a data branch).

### Option C: Google Cloud Run Job *(future)*

For larger refreshes or automation without GitHub Actions:

```bash
gcloud run jobs create github-stats-pipeline \
  --image gcr.io/PROJECT/github-stats-pipeline \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=PROJECT \
  --set-secrets GITHUB_TOKEN=github-token:latest
gcloud run jobs execute github-stats-pipeline
```

---

## Quota notes

| Resource | Free tier | Estimated usage |
|---|---|---|
| BigQuery (scan) | 1 TB/month | ~160 GB first run; ~10 GB incremental |
| GitHub API (REST) | 5,000 req/hr | ~50k requests (enrichment); disk-cached after first run |
| GitHub Pages | Free | Static, no limit |

**BigQuery is the only real cost risk.** Step 02 scans ~100 GB. Always dry-run with
`python pipeline/02_fetch_yearly_commits.py --dry-run` before executing for real.
Once step 02 runs and materializes to a BQ table in your project, subsequent runs
query the cheap materialized table instead.

---

## Rollback

The viz is a static site. To roll back:
```bash
git revert HEAD
git push
```
GitHub Actions will redeploy the previous version of `viz/` automatically.
