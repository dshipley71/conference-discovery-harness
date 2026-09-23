# REQUEST.md — Illustrative Example

> Illustrative request only. This file demonstrates a safe complete request. It contains no live research findings and does not claim that any conference exists.

## Run Identity

- Project: `Conference Discovery Harness`
- Mode: `full`
- Run ID: `illustrative-circular-economy-conferences-2027`
- Refresh source run: `none`
- Request recorded at: `2026-09-22T00:00:00Z`

## Search Objective

Find intentionally public conferences about circular-economy policy and industrial reuse that are scheduled in Europe from 2027-03-01 through 2027-09-30. Collect reviewable aggregator listings and direct conference sources, then extract, normalize, resolve, and report up to 12 conferences without ranking them.

## Scope

- Start date: `2027-03-01`
- End date: `2027-09-30`
- Geography: `Europe; include in-person, hybrid, and Europe-hosted online conferences`
- Topics or keywords: `circular economy, industrial reuse, material recovery, product life extension`
- Search languages: `en, fr, de, es`
- Output language: `en`
- Result limit: `12`

## Known Public Sources

| Source class | Name | Public URL | User note |
|---|---|---|---|
| None supplied | None supplied | None supplied | Discover relevant public sources during the bounded search. |

## Source Rules

- Required source behavior: Use aggregators for observed listings. Prefer reviewed official conference and organizer pages for conference facts. Prefer official venue, registration, sponsor, hotel, and organization pages for related facts.
- Required source classes: At least one reviewed aggregator when available and one reviewed official or first-party source for each reported conference.
- Excluded source classes: Private registration systems, login-only sources, scraped contact databases, guessed profiles, and inaccessible pages as factual evidence.
- Required domains or publishers: None.
- Excluded domains or publishers: None.
- Access limits: Use only intentionally public pages. Do not authenticate, bypass controls, probe systems, enumerate hidden endpoints, or solve access challenges.

## Attendee Collection

- Attendee mode: `public-only`
- Authorization basis: `intentionally-public`
- Authorized input description: `none`
- Personal-data minimization: Collect only public aggregate attendance facts and publicly identified professional conference roles when directly relevant and explicitly supported. Do not treat those professional roles as attendee records or infer attendance from speaking, registration, social activity, or photographs.

## User Constraints

- Do not rank or recommend conferences.
- Do not claim exhaustive coverage.
- Preserve original text with every translation.
- Use `Insufficient evidence` for unsupported material conclusions.

## Clarification History

| Date-time | Ambiguity | Question | User answer | Scope effect |
|---|---|---|---|---|
| `2026-09-22T00:00:00Z` | None | Not needed. | The original illustrative request is sufficient. | Use the scope recorded in this file. |

## Completion Check

- [x] Mode and unique run ID are complete.
- [x] Objective, dates, geography, topics, and languages are complete.
- [x] Known sources and all source rules are recorded.
- [x] Result limit is a positive integer.
- [x] Attendee mode and authorization basis are explicit.
- [x] Refresh source run is not applicable.
- [x] Constraints and clarification history are complete.
