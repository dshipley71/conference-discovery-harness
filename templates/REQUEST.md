# REQUEST.md — Run Request Template

> This is an intentional user-fill template, not a research result. Replace every bracketed instruction before research starts. Keep the exact artifact name `REQUEST.md`.

## Run Identity

- Project: `Conference Discovery Harness`
- Mode: `[required: full | discovery_only | refresh]`
- Run ID: `[required: unique lowercase filesystem-safe ID using letters, digits, and hyphens]`
- Refresh source run: `[required for refresh; otherwise none]`
- Request recorded at: `[required: ISO 8601 date-time]`

## Search Objective

`[required: the complete conference search question or objective; do not silently narrow it]`

## Scope

- Start date: `[required: YYYY-MM-DD or open-ended]`
- End date: `[required: YYYY-MM-DD or open-ended]`
- Geography: `[required: countries, regions, cities, remote scope, or worldwide]`
- Topics or keywords: `[required: comma-separated topics, industries, disciplines, or terms]`
- Search languages: `[required: comma-separated language codes]`
- Output language: `[required: one language code]`
- Result limit: `[required: positive integer or no-limit]`

## Known Public Sources

List user-supplied aggregator, conference, organizer, venue, or other intentionally public sources. Use `None supplied` when the user supplied no source.

| Source class | Name | Public URL | User note |
|---|---|---|---|
| `[aggregator, conference, organizer, venue, or other]` | `[name]` | `[public URL]` | `[scope or relevance]` |

## Source Rules

- Required source behavior: `[required: complete source rules, including direct-source preferences and any user constraints]`
- Required source classes: `[required: list or none]`
- Excluded source classes: `[required: list or none]`
- Required domains or publishers: `[list or none]`
- Excluded domains or publishers: `[list or none]`
- Access limits: Use only intentionally public pages or user-authorized data. Do not authenticate, bypass controls, probe systems, or infer hidden content.

## Attendee Collection

- Attendee mode: `[required: public-only | user-authorized-input | disabled]`
- Authorization basis: `[required: exactly intentionally-public, user-authorized-input, or disabled to match attendee mode]`
- Authorized input description: `[required for user-authorized-input; otherwise none]`
- Personal-data minimization: `[required: identify only attendee or contact fields relevant to this objective]`

## User Constraints

- `[required: one constraint per line, or none]`

## Clarification History

Record one focused clarification when conference identity, date range, geography, attendee authorization, or another material boundary was ambiguous. If no clarification was needed, record that the original request was sufficient.

| Date-time | Ambiguity | Question | User answer | Scope effect |
|---|---|---|---|---|
| `[ISO 8601 date-time]` | `[boundary or none]` | `[focused question or not needed]` | `[answer or original request sufficient]` | `[resulting scope]` |

## Completion Check

- [ ] Mode and unique run ID are complete.
- [ ] Objective, dates, geography, topics, and languages are complete.
- [ ] Known sources and all source rules are recorded.
- [ ] Result limit is a positive integer or `no-limit`.
- [ ] Attendee mode and authorization basis are explicit.
- [ ] Refresh source run is named when mode is `refresh`.
- [ ] Constraints and clarification history are complete.
