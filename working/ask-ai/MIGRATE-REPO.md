# Migrate Repo to Agent Workbench Conventions

## Reference
https://github.com/natepixel/agent-workbench

## Target conventions

### Top-level orienting docs
- `README.md` — project overview
- `AGENTS.md` — how AI and humans work in this repo
- `STATUS.md` — current state and open questions
- `DEPLOY.md` — deployment model

### Stable script entrypoints under `scripts/`
- `./scripts/dev.sh` — main local dev entrypoint
- `./scripts/check-env.sh` — verify required env vars
- `./scripts/status.sh` — show branch status
- `./scripts/export.sh` — bundle for AI handoff

### `working/` — mostly gitignored scratch space with committed structure
- `working/README.md`
- `working/ask-ai/TEMPLATE.md`
- `working/status/README.md`
- `working/notes/README.md`
- `working/export/README.md`

### `skills/` — committed, repeatable operational workflows
### `docs/decisions/` — durable design decisions
### `tests/README.md` — testing ladder
### `.env.example` — documents required config/secrets

## Migration steps (small, low-risk first)

1. Add `README.md`, `AGENTS.md`, `STATUS.md`, `DEPLOY.md`
2. Add `CONTRIBUTING.md`
3. Update `.env.example` to match convention
4. Add `scripts/dev.sh`, `scripts/dev.repo.sh`, `scripts/check-env.sh`
5. Create `working/` committed structure
6. Create `skills/` with at least `README.md` and one skill
7. Create `docs/decisions/` with key decisions
8. Create `tests/README.md`
9. Update `.gitignore` to enforce structure
