# tests/

Testing expectations for this project.

## Testing ladder

### 1. Smoke tests (run locally in < 30s)

- `./scripts/check-env.sh` passes
- `./scripts/dev.sh` starts the local server without error
- `viz/index.html` loads in a browser (demo mode, no pipeline required)
- Pipeline config imports cleanly: `python -c "import pipeline.config"`

### 2. Unit tests

Current: none formally defined.

**Candidates:**
- `pipeline/04_classify_cohorts.py` — `classify_row()` with synthetic inputs
  - A user with pre_mean=0, post_mean=100 → `dormant_reactivated`
  - A user with pre_mean=200, post_mean=300 → `consistently_active`
  - A user with pre_mean=0, post_mean=5 → `always_sparse`
- `pipeline/utils/cache.py` — cache set/get/flush round-trip
- `pipeline/utils/gh_client.py` — rate limit state update from headers

**To run (once written):**
```bash
python -m pytest tests/unit/ -v
```

### 3. Integration tests

- BigQuery dry-run returns a cost estimate without billing:
  `python pipeline/01_sample_users.py --dry-run`
  `python pipeline/02_fetch_yearly_commits.py --dry-run`

- GitHub API returns a valid user profile:
  `python -c "from pipeline.utils.gh_client import get_user; print(get_user('torvalds'))"`

### 4. End-to-end tests

Not yet implemented. Future:
- Playwright: load `http://127.0.0.1:PORT/` → all four chart containers are non-empty
- Pipeline smoke: run steps 04+05 against a synthetic small parquet → JSON files produced

## Minimum before merge to main

- `./scripts/check-env.sh` passes
- No Python import errors: `python -m py_compile pipeline/*.py pipeline/utils/*.py`
- Viz loads in browser (demo mode)

## Running the current smoke tests

```bash
./scripts/check-env.sh
python -m py_compile pipeline/config.py pipeline/01_sample_users.py \
  pipeline/02_fetch_yearly_commits.py pipeline/03_enrich_github_api.py \
  pipeline/04_classify_cohorts.py pipeline/05_export_viz_data.py \
  pipeline/utils/bq_client.py pipeline/utils/gh_client.py pipeline/utils/cache.py
echo "All smoke tests passed"
```
