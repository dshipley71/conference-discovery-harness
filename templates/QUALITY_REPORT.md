# QUALITY_REPORT.md — Data Quality Report Template

> This is an intentional quality-report template, not a completed validation result. Replace bracketed instructions only with results from commands and artifact reviews that actually ran. Keep the exact artifact name `QUALITY_REPORT.md`.

## Run

- Run ID: `[run ID from REQUEST.md]`
- Assessed at: `[ISO 8601 date-time]`
- Mode: `[full | discovery_only resumed by direct stage use | refresh]`
- Reporting readiness: `[ready | blocked]`

## Artifact and Schema Results

| Artifact | Check | Result | Evidence or error |
|---|---|---|---|
| `REQUEST.md` | `[presence and request contract]` | `[pass | fail | not-run]` | `[command or finding]` |
| `AGGREGATORS.md` | `[presence and ledger review]` | `[pass | fail | not-run]` | `[command or finding]` |
| `CONFERENCE_SOURCES.md` | `[presence and ledger review]` | `[pass | fail | not-run]` | `[command or finding]` |
| `RAW_CONFERENCES.json` | `[JSON and raw schema]` | `[pass | fail | not-run]` | `[command or finding]` |
| `NORMALIZED_CONFERENCES.json` | `[JSON and normalized schema]` | `[pass | fail | not-run]` | `[command or finding]` |
| `ENTITY_RESOLUTION.md` | `[presence and decision completeness]` | `[pass | fail | not-run]` | `[command or finding]` |

## Entity Counts

| Entity type | Count |
|---|---:|
| Conferences | `[count]` |
| Conference series | `[count]` |
| Organizations | `[count]` |
| People | `[count]` |
| Venues | `[count]` |
| Sessions and events | `[count]` |
| Registration offers | `[count]` |
| Sponsors and partnerships | `[count]` |
| Hotels | `[count]` |
| Attendee records or aggregates | `[count]` |
| Sources | `[count]` |
| Translations | `[count]` |
| Entity-resolution decisions | `[count]` |

## Duplicate Candidates and Resolution Outcomes

- Duplicate candidates: `[count]`
- Applied decisions: `[count]`
- Rejected decisions: `[count]`
- Unresolved decisions: `[count]`

| Candidate IDs | Entity type | Decision ID | Outcome | Confidence | Remaining concern |
|---|---|---|---|---|---|
| `[IDs]` | `[type]` | `[ER###]` | `[applied | rejected | unresolved]` | `[high | medium | low]` | `[note or none]` |

## Reference Integrity

### Unresolved Foreign Keys

- `[List each JSON quality value exactly. Write only "None." when the JSON list is empty.]`

### Unresolved Source References

- `[List each JSON quality value exactly. Write only "None." when the JSON list is empty.]`

## Branch Coverage

Use only these collection statuses: `complete`, `partial`, `not-published`, `not-applicable`, `inaccessible`, `not-authorized`, `unresolved`.

| Branch | Complete | Partial | Not published | Not applicable | Inaccessible | Not authorized | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Identity and aliases | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Series, edition, and acronym | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Organizers | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Description, themes, topics, type, and languages | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Dates, times, timezone, recurrence, and status | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Websites and event URLs | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| People and contacts | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Committees and roles | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Schedule, tracks, sessions, workshops, and social events | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Registration | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Venue | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Sponsors, exhibitors, and partners | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Hotels | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Attendees and attendance aggregates | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Provenance | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Confidence | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Contradictions | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |
| Unresolved fields | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` | `[count]` |

## Source-Class Coverage

| Source class | Reviewed count | Eligible count | Conferences covered | Limitations |
|---|---:|---:|---:|---|
| `[class]` | `[count]` | `[count]` | `[count]` | `[note]` |

## Conferences Without Official Sources

- `[List each conference ID from quality_metrics.conferences_without_official_sources. Write only "None." when the JSON list is empty.]`

## Conflicts

- `[List each conflict from quality_metrics.conflicts. Write only "None." when the JSON list is empty.]`

## Translation Quality

- Translatable fields: `[count]`
- Translation records: `[count]`
- LLM-generated translations: `[count]`
- Official-source translations: `[count]`
- Human-reviewed translations: `[count]`
- Uncertain translations: `[count]`

| Translation ID | Entity and field | Source language | Target language | Method | Uncertainty | Protected-literal issue |
|---|---|---|---|---|---|---|
| `[T###]` | `[ID and JSON Pointer]` | `[language]` | `[language]` | `[llm-generated | official-source | human-reviewed]` | `[none | low | medium | high]` | `[none or issue]` |

## Attendee Privacy and Authorization

- Attendee mode matches `REQUEST.md`: `[pass | fail]`.
- `[Copy each attendee_privacy_checks and attendee_authorization_checks sentence without its final period]`: `[copy its exact result]`.

Do not add other bullets to this section. Put details in the JSON quality-check records.

## Inaccessible Sources and Collection Gaps

| JSON Pointer or source ID | Source IDs | Gap or access failure | Status | Reporting effect |
|---|---|---|---|---|
| `[JSON Pointer or S###]` | `[S### list or none]` | `[description]` | `[inaccessible | not-published | not-authorized | unresolved-conflict]` | `[effect]` |

## Blocking Warnings

- `[warning that prevents supported reporting, or none]`

## Non-Blocking Warnings

- `[limitation that does not prevent supported reporting, or none]`

## Refresh Differences

Complete this section only in `refresh` mode.

| Entity or branch | Addition, removal, change, or unresolved difference | Source-run evidence | New-run evidence |
|---|---|---|---|
| `[ID or branch]` | `[classification and explanation]` | `[source-run artifact and IDs]` | `[new-run artifact and IDs]` |
