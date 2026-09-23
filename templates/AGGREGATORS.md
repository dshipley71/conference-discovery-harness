# AGGREGATORS.md — Aggregator and Listing Ledger Template

> This is an intentional research template, not live research. Replace bracketed instructions with observed evidence. Keep the exact artifact name `AGGREGATORS.md`. Coverage is bounded by the request and must never be described as exhaustive.

## Run

- Run ID: `[run ID from REQUEST.md]`
- Discovery completed at: `[ISO 8601 date-time]`
- Search scope summary: `[dates, geography, topics, and languages]`
- Coverage statement: `This ledger records only the aggregator providers and listings observed during the bounded search.`

## Coverage Summary

| Metric | Value |
|---|---|
| Aggregators reviewed | `[count]` |
| Reviewable aggregators | `[count]` |
| Matching listings observed | `[count]` |
| Duplicate or syndicated listings | `[count]` |
| Inaccessible or failed leads | `[count]` |

## Aggregator Record

Repeat this section once for each provider.

### `[A###] [Provider Name]`

- Stable aggregator ID: `[A###]`
- Provider name: `[name]`
- Canonical public URL: `[URL]`
- Observed geography: `[observed scope; do not infer unreviewed coverage]`
- Observed topics: `[observed topics]`
- Observed languages: `[observed languages]`
- Observed date coverage: `[observed date span or unresolved]`
- Reviewed listing page: `[public URL]`
- Access date: `[YYYY-MM-DD]`
- Reviewability: `[reviewed | partially-reviewed | inaccessible | unresolved]`
- Reliability: `[high | medium | low | unresolved, with reason]`
- Limitations: `[staleness, missing metadata, dynamic content, scope limits, or none observed]`
- Access failures: `[failed URL and reason, or none]`

#### Matching Listings

Aggregator IDs support only claims that a listing was observed. They do not independently verify conference facts.

| Listing ID | Observed title | Listing URL | Dates as displayed | Location as displayed | Candidate conference ID | Access date | Notes |
|---|---|---|---|---|---|---|---|
| `[A###-L###]` | `[source wording]` | `[URL]` | `[source wording or not published]` | `[source wording or not published]` | `[C### or unresolved]` | `[YYYY-MM-DD]` | `[lead-only limitations]` |

#### Duplicate or Syndication Links

| Related aggregator or listing ID | Relationship | Evidence | Counting treatment |
|---|---|---|---|
| `[A### or A###-L###]` | `[duplicate | syndicated-copy | shared-feed | unresolved]` | `[bounded observation]` | `[same underlying listing, separate, or unresolved]` |

## Failed Aggregator Leads

Preserve every failed lead. Search snippets and inaccessible pages remain discovery leads only.

| Lead ID | Candidate provider or page | URL | Failure reason | Access date | Follow-up result |
|---|---|---|---|---|---|
| `[A-FAIL-###]` | `[name or title]` | `[URL]` | `[inaccessible, blocked, removed, paywalled, unreviewed, or other reason]` | `[YYYY-MM-DD]` | `[stopped, replaced by reviewed source, or unresolved]` |

## Freeze Record

- Frozen at: `[ISO 8601 date-time]`
- Frozen by: `[agent or operator identifier]`
- Downstream rule: Do not modify this artifact after discovery handoff.

