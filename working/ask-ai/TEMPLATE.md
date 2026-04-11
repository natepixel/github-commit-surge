# Ask AI Template

## Question
What specific question do you want answered?

## Goal
What outcome are you trying to reach?

## Constraints
- stack: Python 3.11, BigQuery, GitHub API, Observable Plot (static site)
- deployment: GitHub Pages (viz), local or Cloud Run (pipeline)
- quota: BigQuery 1TB/mo free — always dry-run expensive queries
- things that should not change: pipeline step ordering (01→03→02→04→05)

## Relevant files
List only the files that matter. Generate a bundle with `./scripts/export.sh`.

## Relevant snippets
Paste only the minimal code or config excerpts needed.

## Current behavior
What happens now?

## Desired behavior
What should happen instead?

## What local AI already thinks
Summarize any local AI analysis here.

## What kind of answer you want
Examples:
- BigQuery SQL optimization
- threshold tuning recommendation
- visualization design suggestion
- pipeline debugging hypothesis
- new cohort definition

## AI safety note
This repo does not contain PII beyond public GitHub usernames.
Do not share `.env` contents or GCP service account keys.
