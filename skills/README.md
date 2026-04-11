# skills/

Committed, repo-specific operational runbooks.

A skill belongs here when it:
- helps humans or AIs repeatedly operate in this repo
- captures a recurring workflow (pipeline run, BQ query, viz deploy)
- documents repo-specific debugging or inspection steps
- does not belong in production code

## What's here

- `run-pipeline.md` — how to run the full data pipeline end-to-end
- `bigquery-quota-discipline.md` — rules for managing the 1TB/mo free quota
- `deploy-viz.md` — how to deploy / update the GitHub Pages visualization

## Promotion rule

Draft skills can start in `working/notes/` and be promoted here once proven useful.

## Suggested format

Each skill should cover:
- **Purpose** — what this skill does
- **When to use it** — triggers or scenarios
- **Steps** — ordered, concrete commands
- **Expected output** — what success looks like
- **Caveats** — edge cases, quota risks, known issues
