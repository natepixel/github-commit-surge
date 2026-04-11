# working/status/

Branch-specific status notes live here.

## Filename convention

Use the **safe branch filename** so `./scripts/status.sh` detects notes automatically:

- start with the git branch name
- replace `/` with `__`
- replace `:` with `__`
- add `.md`

Examples:
- `main` → `main.md`
- `feature/add-geo` → `feature__add-geo.md`
- `bugfix:scatter-tooltip` → `bugfix__scatter-tooltip.md`

## Suggested contents

```markdown
# Status: [branch name]

**Date:** YYYY-MM-DD
**Goal:** [one sentence]

## Current state
[what's working, what's in progress]

## Last meaningful commits
- abc1234 — [description]

## Next step
[concrete next action]

## Blockers
[anything blocking progress]
```
