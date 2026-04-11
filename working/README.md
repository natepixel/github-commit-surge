# working/

Scratch space for temporary, AI-friendly, non-durable project work.

## What belongs here

- One-off BigQuery exploration queries
- Debug notes from a pipeline run
- Intermediate analysis drafts
- Screenshots / evidence
- AI handoff bundles
- Branch-specific status notes
- Temporary experiments with classification thresholds

## Rule of thumb

| Temporary → | `working/` |
| Durable → | top-level docs, `docs/`, `skills/`, `scripts/`, `pipeline/` |

## What is tracked vs ignored

Most files under `working/` are gitignored. The committed structure is:

```
working/
├── README.md               ← this file (committed)
├── ask-ai/
│   ├── TEMPLATE.md         ← AI handoff template (committed)
│   └── MIGRATE-REPO.md     ← migration template (committed)
├── export/
│   └── README.md           ← export instructions (committed; .zips ignored)
├── status/
│   └── README.md           ← branch status convention (committed)
└── notes/
    └── README.md           ← notes convention (committed)
```

`working/dev-state/` is script-managed and gitignored — don't edit by hand.

## Subfolders

### `ask-ai/`
Templates for handing off work to external AI tools (ChatGPT, Claude.ai, etc.).
Use `./scripts/export.sh` to create a zip bundle and attach it with the template.

### `export/`
Output of `./scripts/export.sh`. `.zip` files are gitignored.

### `status/`
Branch-specific status notes. Filename = safe branch name + `.md`
(replace `/` and `:` with `__`). Auto-detected by `./scripts/status.sh`.

### `notes/`
Lightweight committed notes. Promote anything durable to `docs/` or `STATUS.md`.
