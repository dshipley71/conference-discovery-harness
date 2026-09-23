# QUALITY_REPORT.md — Synthetic Test Fixture

> Synthetic test data only. These findings describe only the validator fixture.

## Run

- Run ID: `valid-run`
- Assessed at: `2026-09-22T00:05:00Z`
- Mode: `full`
- Reporting readiness: `ready`

## Artifact and Schema Results

| Artifact | Result | Finding |
|---|---|---|
| `RAW_CONFERENCES.json` | pass | Synthetic fixture conforms to the raw schema. |
| `NORMALIZED_CONFERENCES.json` | pass | Synthetic fixture conforms to the normalized schema. |

## Entity Counts

| Collection | Count |
|---|---:|
| Conferences | 1 |
| Conference series | 0 |
| Organizations | 1 |
| People | 1 |
| Venues | 0 |
| Sessions and events | 0 |
| Registration offers | 0 |
| Sponsors and partnerships | 0 |
| Hotels | 0 |
| Attendee records or aggregates | 1 |
| Sources | 2 |
| Translations | 0 |
| Entity-resolution decisions | 0 |

## Duplicate Candidates and Resolution Outcomes

- Duplicate candidates: 0.
- Applied decisions: 0.
- Rejected decisions: 0.
- Unresolved decisions: 0.

## Reference Integrity

### Unresolved Foreign Keys

- None.

### Unresolved Source References

- None.

## Branch Coverage

| Branch | Complete | Partial | Not published | Not applicable | Inaccessible | Not authorized | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Identity and aliases | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Series, edition, and acronym | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Organizers | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Description, themes, topics, type, and languages | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Dates, times, timezone, recurrence, and status | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Websites and event URLs | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| People and contacts | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Committees and roles | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule, tracks, sessions, workshops, and social events | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Registration | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Venue | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Sponsors, exhibitors, and partners | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Hotels | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Attendees and attendance aggregates | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| Provenance | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Confidence | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Contradictions | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Unresolved fields | 0 | 0 | 1 | 0 | 0 | 0 | 0 |

## Source-Class Coverage

| Source class | Reviewed count | Eligible count | Conferences covered | Limitations |
|---|---:|---:|---|---|
| aggregator-listing | 1 | 0 | C001 | Supports only the synthetic observed-listing claim. |
| official-conference | 1 | 1 | C001 | Synthetic direct source only. |

## Conferences Without Official Sources

- None.

## Conflicts

- None.

## Translation Quality

- Translatable fields: 0.
- Translation records: 0.
- LLM-generated translations: 0.
- Official-source translations: 0.
- Human-reviewed translations: 0.
- Uncertain translations: 0.

## Attendee Privacy and Authorization

- Attendee mode matches `REQUEST.md`: pass.
- No individual attendee or private registration data is present: pass.
- Aggregate attendance evidence is intentionally public: pass.

## Inaccessible Sources and Collection Gaps

| JSON Pointer or source ID | Source IDs | Gap or access failure | Status | Reporting effect |
|---|---|---|---|---|
| /conferences/0/collection_statuses/series_edition_and_acronym | S001 | The synthetic source does not publish series, edition, or acronym data. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/description_themes_topics_type_and_languages | S001 | The synthetic source does not publish descriptive classification data. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/committees_and_roles | S001 | The synthetic source does not publish a separate committee ledger. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/schedule_tracks_sessions_workshops_and_social_events | S001 | The synthetic source does not publish a schedule. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/registration | S001 | The synthetic source does not publish registration data. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/venue | S001 | The synthetic source does not publish venue data. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/sponsors_exhibitors_and_partners | S001 | The synthetic source does not publish sponsor or partner data. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/hotels_and_booking | S001 | The synthetic source does not publish hotel or booking data. | not-published | Use `Insufficient evidence`. |
| /conferences/0/collection_statuses/unresolved_fields | S001 | The synthetic source does not publish unresolved-field data. | not-published | Use `Insufficient evidence`. |

## Blocking Warnings

- None.

## Non-Blocking Warnings

- All fixture content is synthetic and must not be presented as live research.
