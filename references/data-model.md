# Conference Data Model

## Purpose and Authority

This reference defines the semantic contract for raw and normalized conference data. JSON Schemas under `schemas/` define the exact machine validation rules when present. If a schema and this reference disagree, stop and report the conflict instead of silently changing data.

## Shared Rules

- Use UTF-8 JSON.
- Use stable IDs that are unique within one run.
- Resolve every foreign key.
- Preserve raw source wording.
- Attach field-level provenance to every material value.
- Use `null` only for unknown values.
- Never treat a missing value as proof that a fact is false.
- Never overwrite `RAW_CONFERENCES.json`.

## ID Prefixes

Use distinct run-local prefixes:

| Record | Prefix | Example |
|---|---|---|
| Aggregator | `A` | `A001` |
| Source | `S` | `S001` |
| Conference | `C` | `C001` |
| Conference series | `CS` | `CS001` |
| Organization | `O` | `O001` |
| Person | `P` | `P001` |
| Venue | `V` | `V001` |
| Session or event | `E` | `E001` |
| Registration offer | `R` | `R001` |
| Sponsor or partnership | `SP` | `SP001` |
| Hotel | `H` | `H001` |
| Attendee record or aggregate | `AT` | `AT001` |
| Translation | `T` | `T001` |
| Entity-resolution decision | `ER` | `ER001` |

Use zero-padded numeric suffixes of at least three digits. Never assign one ID to multiple entity types.

## Collection Status

Every conference branch and every related collection path has exactly one status:

| Status | Meaning |
|---|---|
| `complete` | Reviewed evidence supports the collected branch and no known material field is missing. |
| `partial` | Some supported information exists, but material fields are missing. |
| `not-published` | Reviewed relevant sources do not publish the requested information. |
| `not-applicable` | The branch does not apply to this conference. |
| `inaccessible` | A relevant source exists but could not be reviewed. |
| `not-authorized` | Collection would exceed the request, public scope, or user authorization. |
| `unresolved` | Sources conflict or identity remains uncertain. |

Store a reason and supporting source IDs with the status when applicable.

## Field-Level Provenance

Each entity or branch uses an explicit JSON Pointer map:

```json
{
  "field_provenance": {
    "/name": ["S001"],
    "/dates/start": ["S001", "S004"],
    "/registration_url": ["S003"]
  }
}
```

Pointers are relative to the containing record unless the schema states otherwise. Each source ID must resolve to `CONFERENCE_SOURCES.md` or, only for an observed-listing field, `AGGREGATORS.md`.

For a conflict, preserve each candidate value and its own source IDs. Do not attach one combined citation to values that different sources support.

## Raw Dataset

`RAW_CONFERENCES.json` preserves extraction results before translation, canonicalization, deduplication, or entity resolution.

It contains:

- run metadata that matches `REQUEST.md`;
- source references used during extraction;
- one raw record per conference candidate;
- branch statuses;
- source-faithful values and bounded raw text;
- field-level provenance;
- confidence assessments;
- contradictions;
- unresolved fields;
- possible duplicate links that do not make a resolution decision.

Keep uncertain candidates separate. Raw IDs remain stable and are never rewritten during normalization.

### Required Conference Branches

Address every branch:

1. identity and aliases;
2. series, edition, acronym, and organizers;
3. description, themes, topics, type, and languages;
4. dates, times, timezone, recurrence, and status;
5. websites and event URLs;
6. people and public conference contacts;
7. committees and roles;
8. schedule, tracks, sessions, workshops, and social events;
9. registration, deadlines, ticket classes, prices, currency, eligibility, and URL;
10. venue;
11. sponsors, exhibitors, partners, and tiers;
12. hotels and booking details;
13. attendees and attendance aggregates;
14. provenance;
15. confidence;
16. contradictions and unresolved fields.

Each branch contains its status, source-faithful values, provenance, and notes. An empty value collection still requires a status and reason.

## Normalized Dataset

`NORMALIZED_CONFERENCES.json` contains top-level collections for:

- `conferences`;
- `conference_series`;
- `organizations`;
- `people`;
- `venues`;
- `sessions_and_events`;
- `registration_offers`;
- `sponsors_and_partnerships`;
- `hotels`;
- `attendee_records_or_aggregates`;
- `sources`;
- `translations`;
- `entity_resolution_decisions`;
- `run_metadata`;
- `quality_metrics`.

The schema may provide display labels, ordering, or supporting objects, but these semantic collections must remain distinct.

### Conferences

Represent:

- canonical name, aliases, acronym, edition, type, themes, topics, and languages;
- series and organizer references;
- start and end dates, times, timezone, recurrence, format, and status;
- official and related URLs;
- references to people, committees, sessions and events, registration offers, venue, sponsors and partnerships, hotels, and attendee records or aggregates;
- branch statuses;
- field-level provenance;
- confidence, contradictions, and unresolved fields.

### People and Committees

People contain only fields allowed by `references/privacy.md`. Conference roles and committee memberships are explicit relationships with conference IDs, organization IDs when supported, role labels, relevant dates, provenance, and authorization basis when needed.

### Venues

Represent:

- canonical name and aliases;
- venue type;
- postal address;
- locality;
- administrative area;
- country;
- postal code;
- latitude and longitude only when supported;
- official website;
- public business telephone number;
- public business email;
- public contact page;
- public map URL;
- conference rooms or buildings;
- accessibility notes;
- transport notes;
- conference relationship;
- relevant dates;
- provenance;
- collection status.

A public map URL is data, not permission to infer unsupported coordinates. Do not require a geocoding API key.

### Sessions and Events

Represent tracks, sessions, workshops, social events, and other subevents with conference ID, title, type, dates and times, timezone, location or room, people and organization references, status, URLs, provenance, and unresolved details.

### Registration Offers

Represent registration state, ticket class, eligibility, sales window or deadline, price as source wording plus normalized amount when unambiguous, currency, tax or fee notes, registration URL, provenance, and status.

### Sponsors and Partnerships

Represent the conference, organization, relationship type, tier, official URL, relevant dates, provenance, and status. Do not infer sponsorship from a logo without supporting context.

### Hotels

Represent canonical name, address, official or conference booking URL, public rate wording, currency, booking deadline, relationship to the conference or venue, transport notes, provenance, and status.

### Attendee Records or Aggregates

Represent only data allowed by the attendee mode:

- a public aggregate attendance fact with scope, period, value, wording, and provenance; or
- a user-authorized attendee record with authorization basis and minimal relevant fields.

Do not mix an estimate, intended audience, and verified attendance count. Label each fact type.

## Translation Records

Each translation uses a `T###` ID and preserves:

- original text;
- source language;
- translated text;
- target language;
- translation method;
- uncertainty;
- source IDs;
- the target entity and field.

Protected literals are names, URLs, numbers, dates, prices, identifiers, and quotations. Preserve them exactly unless an official localized form is supported and both forms are retained.

Use `llm-generated` for an LLM translation. Use `official-source` or `human-reviewed` only when evidence supports that method. Do not label a translation certified without evidence.

## Entity-Resolution Decisions

Each decision uses an `ER###` ID and records:

- entity type;
- candidate or original IDs;
- source IDs;
- compared attributes;
- decision type: `merge`, `split`, `alias`, `rejected-candidate`, or `unresolved-candidate`;
- outcome: `applied`, `rejected`, or `unresolved`;
- canonical ID and alias redirects when applicable;
- confidence;
- rationale;

The same decisions appear in `ENTITY_RESOLUTION.md` in human-reviewable form.

## Quality Metrics and Report

`QUALITY_REPORT.md` records:

- artifact and schema results;
- entity counts;
- duplicate candidates;
- merge, split, alias, rejected, and unresolved outcomes;
- unresolved foreign keys;
- unresolved source references;
- branch coverage;
- source-class coverage;
- conferences without official sources;
- conflicting names, dates, locations, or status;
- translation coverage and uncertainty;
- attendee privacy and authorization checks;
- inaccessible sources;
- collection gaps;
- blocking warnings;
- non-blocking warnings;
- refresh additions, removals, changes, and unresolved differences when applicable.

`REPORT.md` includes:

- search scope and collection date;
- aggregator and direct-source coverage;
- a conference comparison table;
- one summary per conference;
- dates, location, venue, format, registration state, and official URL;
- supported people, committees, schedule, sponsors, events, hotels, and attendee information;
- quality warnings;
- material entity-resolution and translation notes;
- stable source citations.

Use `Insufficient evidence` for unsupported requested facts.
