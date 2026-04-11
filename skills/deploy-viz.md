# Skill: Deploy the Visualization

## Purpose

Push an updated static visualization to GitHub Pages.

## Automatic deploy (recommended)

Any push to `main` that touches `viz/**` or `data/viz/**` triggers
`.github/workflows/deploy-viz.yml` automatically.

```bash
# After running the pipeline and syncing viz data:
git add data/viz/ viz/data/
git commit -m "chore: refresh viz data"
git push origin main
# → GitHub Actions deploys to Pages within ~1 minute
```

## Manual deploy

```bash
# From repo root:
./scripts/export.sh     # optional: bundle for review before deploying

git add viz/ data/viz/
git commit -m "feat: update visualization"
git push origin main
```

## Enable GitHub Pages (first time)

1. Go to repo Settings → Pages
2. Source: **GitHub Actions** (not "Deploy from a branch")
3. Save
4. Push to `main` — the workflow runs and publishes

## Check deploy status

```bash
gh run list --workflow=deploy-viz.yml --limit 5
gh run view $(gh run list --workflow=deploy-viz.yml --limit 1 --json databaseId -q '.[0].databaseId')
```

## Demo mode fallback

If `data/viz/*.json` files don't exist in the repo yet, the deployed site runs in
demo mode automatically (synthetic data, labeled in the subtitle). This is safe to
deploy — it shows the visualization structure without real data.

## Rollback

```bash
git revert HEAD
git push origin main
# GitHub Actions redeploys the previous version
```
