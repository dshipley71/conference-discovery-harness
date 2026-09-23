# Conference Discovery Harness

A four-stage agentic workflow for discovering conferences, reviewing public sources, creating structured conference data, resolving entities, and producing cited summaries.

The project uses Markdown instructions and JSON artifacts. It has no package dependency, database, hosted service, or source-specific scraper.

## Requirements

Use an LLM or coding-agent environment that can:

- read and write repository files;
- search and open intentionally public web pages;
- reason over Markdown and JSON;
- preserve source provenance;
- run Python 3 for deterministic validation.

## Workflow

```text
REQUEST.md
  -> discover-conference-sources
  -> AGGREGATORS.md + CONFERENCE_SOURCES.md
  -> extract-conference-data
  -> RAW_CONFERENCES.json
  -> normalize-conference-data
  -> NORMALIZED_CONFERENCES.json + ENTITY_RESOLUTION.md + QUALITY_REPORT.md
  -> report-conferences
  -> REPORT.md
```

Each run uses `runs/<run-id>/`. Existing runs are immutable.

## Full Run

Give this repository to the LLM and use a request like:

```text
Read AGENTS.md and PROJECT_MEMORY.md before starting.

Mode: full
Run ID: renewable-energy-conferences-2027

Find public conferences about renewable energy in Europe between
2027-01-01 and 2027-06-30.

Search languages: en, de, fr
Output language: en
Result limit: 20 conferences
Attendee mode: public-only

Collect aggregator listings and direct conference sources. Extract people,
committees, schedules, registration, venues, sponsors, events, hotels, and
public aggregate attendance facts. Freeze each stage before continuing.
```

The LLM creates:

```text
runs/renewable-energy-conferences-2027/
├── REQUEST.md
├── AGGREGATORS.md
├── CONFERENCE_SOURCES.md
├── RAW_CONFERENCES.json
├── NORMALIZED_CONFERENCES.json
├── ENTITY_RESOLUTION.md
├── QUALITY_REPORT.md
└── REPORT.md
```

## Discovery Only

```text
Read AGENTS.md and PROJECT_MEMORY.md before starting.

Mode: discovery_only
Run ID: public-health-discovery-2027
Objective: Find public-health conferences in North America during 2027.
Search languages: en, fr
Output language: en
Result limit: 50
Attendee mode: disabled

Create REQUEST.md, AGGREGATORS.md, and CONFERENCE_SOURCES.md.
Stop after discovery.
```

## Refresh

```text
Read AGENTS.md and PROJECT_MEMORY.md before starting.

Mode: refresh
Source run: renewable-energy-conferences-2027
Run ID: renewable-energy-conferences-2027-refresh-01

Repeat the confirmed source run scope. Report additions, removals, changes,
and unresolved differences. Do not change the source run.
```

## Resume a Stage

To continue from frozen discovery:

```text
Read AGENTS.md, PROJECT_MEMORY.md, and
skills/extract-conference-data/SKILL.md.

Run ID: public-health-discovery-2027

Use the existing REQUEST.md, AGGREGATORS.md, and CONFERENCE_SOURCES.md.
Do not search again and do not modify those files.
Create RAW_CONFERENCES.json.
```

The same pattern applies to normalization and reporting. Each skill lists its required upstream artifacts.

## Request Fields

A request defines:

- mode and unique run ID;
- objective and date range;
- geography and topics;
- search languages and output language;
- known sources;
- source requirements and exclusions;
- result limit;
- attendee mode;
- refresh source run when applicable;
- user constraints and clarifications.

Attendee mode is one of:

- `public-only`;
- `user-authorized-input`;
- `disabled`.

## Status Meanings

Every collection branch uses one status:

| Status | Meaning |
|---|---|
| `complete` | The reviewed sources support the collected branch. |
| `partial` | Some supported information exists, but material fields remain missing. |
| `not-published` | Reviewed sources do not publish the requested information. |
| `not-applicable` | The branch does not apply to this conference. |
| `inaccessible` | A relevant source could not be reviewed. |
| `not-authorized` | Collection would exceed the public or authorized scope. |
| `unresolved` | Sources conflict or identity remains uncertain. |

`null` means unknown. It does not mean false or not applicable.

## Validation

Run all tests:

```bash
python3 -m compileall -q tools tests
python3 -m unittest discover -s tests -v
```

Validate the included complete fixture:

```bash
python3 tools/validate_run.py tests/fixtures/valid-run
```

Validate a real run:

```bash
python3 tools/validate_run.py runs/<run-id>
```

Validate an incomplete frozen stage:

```bash
python3 tools/validate_run.py runs/<run-id> --stage discovery
python3 tools/validate_run.py runs/<run-id> --stage raw
python3 tools/validate_run.py runs/<run-id> --stage normalized
```

Invalid fixtures must return a nonzero status:

```bash
python3 tools/validate_run.py tests/fixtures/invalid-missing-artifacts
```

## Live Smoke Procedure

When the executing environment has public web access:

1. Create a bounded request with a small result limit.
2. Select an aggregator that the current search finds.
3. Record at least one matching listing under an `A###` ID.
4. Resolve one candidate to its reviewed official conference page.
5. Record that page under an `S###` ID.
6. Validate the run.

Do not hard-code an aggregator or conference. If web access is unavailable, record the blocker and do not claim success.

## Evidence Rules

- Aggregators support observed-listing claims.
- Reviewed official and first-party pages support conference facts.
- Search snippets and inaccessible pages are discovery leads only.
- Repeated syndication is not independent confirmation.
- Reports cite stable source IDs such as `[S001]`.
- Reports use `[A001]` only for observed-listing claims.
- Reports state `Insufficient evidence` when artifacts cannot support a claim.
- Normalized scalar values must reconcile with their raw evidence pointers or a recorded translation.
- Human-readable report and quality statements must reconcile with normalized JSON, including extra names, dates, counts, roles, URLs, conflicts, and privacy checks.
- Refresh narratives must identify an actual changed field or collection and cannot present an earlier value as the current result.

## Privacy

Collect only relevant public professional information or user-authorized data.

The harness does not access private registration systems, guess contacts, infer protected traits, perform face recognition, or infer attendance without evidence.

See `references/privacy.md`.

## Data Model

`RAW_CONFERENCES.json` preserves extracted source wording.

`NORMALIZED_CONFERENCES.json` contains normalized entities, translations, provenance, entity-resolution decisions, and quality metrics.

See `references/data-model.md` and the schemas under `schemas/`.

## Limitations

- Web coverage depends on the executing environment and public source availability.
- Dynamic, blocked, removed, or paywalled pages can remain inaccessible.
- Conference details can change after collection.
- Translation is LLM-generated unless a source supplies an official translation.
- Entity resolution is conservative and can leave candidates unresolved.
- The harness does not guarantee exhaustive coverage or verified attendance.
