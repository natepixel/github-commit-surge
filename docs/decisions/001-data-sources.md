# Decision 001: Data Sources

**Date:** 2025-04

## Context

We need per-user annual commit counts going back to 2011 at scale (~10k users),
plus account creation dates, without violating GitHub ToS or spending money.

Several sources were evaluated.

## Decision

Use **GH Archive via BigQuery** as the primary commit source, supplemented by the
**GitHub REST API** for account metadata (creation date, type, profile).

## Alternatives considered

| Source | Why not used |
|---|---|
| GitHub Octoverse | Aggregate only, not per-user |
| GitHub Innovation Graph | Quarterly, economy-level aggregates only |
| GitHub REST API (commits) | Max 1,000 results per search, cannot enumerate all commits for a user |
| GitHub GraphQL `contributionsCollection` | 15 requests/user/year — too expensive at scale; used as validation only |
| BigQuery `github_repos.commits` | Covers only repos specifically snapshotted; GH Archive has broader coverage |

## Why GH Archive

- Complete public timeline since 2011
- No per-request rate limits (BigQuery cost model)
- TABLESAMPLE enables cheap exploratory queries
- Hourly granularity; 15+ event types including PushEvent
- JOIN-filtered scans are feasible within the 1 TB/mo free tier

## Consequences

- Only public GitHub activity is counted (private commits excluded)
- PushEvent payloads cap commits at 20 per event — bulk imports undercount slightly
- User identity is login-based only (no linking across accounts)
- No demographic data (age, geography is freeform text field only)
- Account creation year is a proxy for developer tenure, not actual developer age
