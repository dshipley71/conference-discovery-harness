# Entity Resolution

## Purpose

Use these rules to deduplicate sources and conference-domain entities without collapsing distinct conferences, editions, people, organizations, venues, or events.

Normalization can create candidates. Only evidence can justify a resolution decision.

## Prepare Values

Before comparison:

- normalize Unicode and whitespace;
- compare case-folded text while preserving display case;
- normalize safe punctuation variants;
- canonicalize URLs without discarding meaningful path or query components;
- parse dates only when their meaning is unambiguous;
- normalize country and language codes;
- normalize telephone formats only when country context is supported.

Keep every original value and source ID.

## Candidate Generation

Potential duplicate signals include:

- matching or redirecting official domains;
- the same conference series and edition;
- overlapping dates and locations;
- matching organizer relationships;
- matching official identifiers or registration URLs;
- equivalent venue addresses;
- the same professional organization and role;
- a documented syndication relationship.

These signals create a candidate pair. They do not by themselves require a merge.

## Decision Standard

Never merge entities because names alone match.

Merge only when there is:

- one strong, source-supported unique identifier; or
- multiple corroborating attributes whose combined context identifies the same entity.

Useful corroboration includes domains, dates, locations, organizations, roles, official identifiers, and source relationships. Consider contradictions and edition boundaries before merging.

Keep candidates separate when evidence is insufficient. Use an unresolved decision rather than a speculative merge.

## Entity-Specific Rules

### Conferences and Series

Do not merge separate editions of one series. A series record may link editions while each conference retains its own ID, dates, venue, and status.

Substantial name similarity plus different dates does not prove either sameness or difference. Check series, edition, organizer, domain, and location evidence.

### Organizations and Sponsors

Distinguish an organization from its brands, chapters, subsidiaries, and similarly named organizations. A logo or name on a page does not establish a sponsor relationship without supporting context.

### People

Require professional-context corroboration such as organization, role, official biography, conference relationship, or a source-supported identifier.

Do not:

- use a name match alone;
- infer identity from photographs;
- perform face recognition;
- use unsupported profile similarity;
- guess social profiles or contact details.

### Venues and Hotels

Compare official domain, complete address, locality, venue type, and conference relationship. Do not merge a campus, complex, building, room, and hotel merely because they share an address.

### Sessions and Events

Distinguish a recurring session title from a specific dated occurrence. Use conference, track, date, time, room, and participants as context.

### Sources and Aggregator Listings

Treat mirrored pages, feeds, press-release copies, and syndication as one underlying source relationship. Preserve each reviewed URL, but do not count repeated content as independent confirmation.

## Decision Types

Record every candidate outcome:

- `merge`: two or more records represent one entity;
- `split`: one source or raw record contains multiple entities that require separate records;
- `alias`: a supported alternate name or ID redirects to a canonical entity;
- `rejected-candidate`: reviewed candidates are not the same entity;
- `unresolved-candidate`: available evidence cannot support a merge or rejection.

Do not omit rejected or unresolved candidates from the audit log.

## Merge Mechanics

For a merge:

1. select or assign the canonical run-local ID;
2. retain every original ID;
3. create explicit alias redirects from retired IDs to the canonical ID;
4. union only compatible, source-supported values;
5. preserve conflicting values as conflicts;
6. retain field-level provenance for every value;
7. update all foreign keys;
8. record the decision in normalized JSON and `ENTITY_RESOLUTION.md`.

Do not delete evidence or source relationships.

## Split Mechanics

For a split:

1. preserve the original raw record ID;
2. create separate normalized entity IDs;
3. assign each supported value and source to the correct entity;
4. leave ambiguous values unresolved;
5. update foreign keys only when the target is supported;
6. record the rationale and resulting IDs.

## Decision Record

Every `ER###` record and matching Markdown entry contains:

- entity type;
- candidate or original IDs;
- source IDs;
- compared attributes;
- decision;
- canonical and redirected IDs when applicable;
- confidence;
- rationale;
- contradictions;

Confidence describes evidence strength. It is not a substitute for rationale.

## Refresh Comparisons

IDs are run-local. For a refresh:

- preserve the source run unchanged;
- create a cross-run match only when the same evidence standard is met;
- record old and new IDs;
- classify additions, removals, changes, and unresolved differences;
- distinguish a removed listing from evidence that a conference was cancelled;
- do not copy an earlier fact when the new run lacks support.

## Stop Conditions

Stop the affected resolution when:

- identity depends on a name alone;
- evidence conflicts on a material edition, date, location, organization, or role;
- a foreign key target cannot be established;
- the decision would require a photograph, protected-trait inference, guessed profile, or private data;
- preserving provenance or original IDs is not possible.

Record the outcome as unresolved and keep the candidates separate.
