# REQUEST.md — Synthetic Test Fixture

> Synthetic test data only. This fixture is not live conference research.

## Run Identity

- Project: `Conference Discovery Harness`
- Mode: `full`
- Run ID: `valid-run`
- Refresh source run: `none`
- Request recorded at: `2026-09-22T00:00:00Z`

## Search Objective

Validate one synthetic conference record through the complete harness workflow.

## Scope

- Start date: `2099-06-01`
- End date: `2099-06-30`
- Geography: `Synthetic Exampleland`
- Topics or keywords: `validation, synthetic conference data`
- Search languages: `en`
- Output language: `en`
- Result limit: `1`

## Known Public Sources

| Source class | Name | Public URL | User note |
|---|---|---|---|
| aggregator | Synthetic Aggregator | https://aggregator.example.invalid/ | Synthetic test source only. |

## Source Rules

- Required source behavior: Use the synthetic aggregator only for an observed-listing claim and the synthetic direct source for conference facts.
- Required source classes: aggregator-listing, official-conference
- Excluded source classes: private, authenticated
- Required domains or publishers: example.invalid
- Excluded domains or publishers: none
- Access limits: Use only intentionally public synthetic fixture content.

## Attendee Collection

- Attendee mode: `public-only`
- Authorization basis: `intentionally-public`
- Authorized input description: `none`
- Personal-data minimization: Retain only one synthetic aggregate attendance fact.

## User Constraints

- Do not treat fixture data as live research.

## Clarification History

| Date-time | Ambiguity | Question | User answer | Scope effect |
|---|---|---|---|---|
| 2026-09-22T00:00:00Z | none | Not needed. | The synthetic request is complete. | Use the recorded fixture scope. |

## Completion Check

- [x] Synthetic request fields are complete.
