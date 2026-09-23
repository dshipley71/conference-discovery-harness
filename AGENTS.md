# Conference Discovery Harness

## Purpose

Use this repository to research conferences with public web sources. Preserve each stage as a reviewable run artifact.

The harness has exactly four operational skills:

1. `skills/discover-conference-sources/SKILL.md`
2. `skills/extract-conference-data/SKILL.md`
3. `skills/normalize-conference-data/SKILL.md`
4. `skills/report-conferences/SKILL.md`

Do not create or invoke a fifth project agent. `tools/validate_run.py` is a deterministic validation tool.

## Read First

Before each task:

1. Read `PROJECT_MEMORY.md`.
2. Read the user's complete request.
3. Read the applicable skill.
4. Read only the references that the skill requires.
5. Inspect existing run artifacts before you create or change files.

## Required Request Values

Obtain these values before research starts:

- mode: `full`, `discovery_only`, or `refresh`
- unique filesystem-safe run ID
- complete search objective
- start and end dates
- geography
- topics or keywords
- search languages
- output language
- known public sources
- source requirements and exclusions
- result limit or an explicit no-limit instruction
- attendee mode: `public-only`, `user-authorized-input`, or `disabled`
- source run when mode is `refresh`
- user constraints

Ask one focused question when conference identity, date range, geography, attendee authorization, or another material boundary is ambiguous.

## Run Contract

Write every run under:

```text
runs/<run-id>/
├── REQUEST.md
├── AGGREGATORS.md
├── CONFERENCE_SOURCES.md
├── RAW_CONFERENCES.json
├── NORMALIZED_CONFERENCES.json
├── ENTITY_RESOLUTION.md
├── QUALITY_REPORT.md
└── REPORT.md
```

An existing run is frozen. Do not overwrite it.

A refresh must use a new run ID. It must name and preserve the source run.

## Workflow

### `full`

1. Create `REQUEST.md`.
2. Use `discover-conference-sources`.
3. Freeze `AGGREGATORS.md` and `CONFERENCE_SOURCES.md`.
4. Use `extract-conference-data`.
5. Freeze `RAW_CONFERENCES.json`.
6. Use `normalize-conference-data`.
7. Run `python3 tools/validate_run.py runs/<run-id> --stage normalized`.
8. Use `report-conferences`.
9. Run `python3 tools/validate_run.py runs/<run-id>`.

### `discovery_only`

1. Create `REQUEST.md`.
2. Use `discover-conference-sources`.
3. Freeze the discovery artifacts.
4. Stop without creating later artifacts.

### `refresh`

1. Require a source run and a new run ID.
2. Preserve the source run.
3. Repeat discovery, extraction, normalization, and reporting.
4. Record meaningful additions, removals, changes, and unresolved differences.

### Direct Stage Use

A skill can run directly when all required upstream artifacts exist. Do not recreate or modify frozen upstream artifacts.

## Source Rules

- Use aggregators to discover conference listings.
- Prefer official conference and organizer pages for conference facts.
- Prefer official venue, sponsor, hotel, and organization pages for related facts.
- Treat search snippets and inaccessible pages as discovery leads only.
- Treat repeated syndication as one underlying source.
- Preserve bounded excerpts or faithful summaries.
- Record publication dates and access dates.
- Preserve contradictions and source failures.
- Do not claim exhaustive web coverage.

## People and Attendee Rules

Collect only relevant public professional information or user-authorized data.

Do not:

- access private registration records;
- authenticate or bypass access controls;
- guess contact details, identities, or profiles;
- collect secrets, credentials, payment details, or sensitive personal data;
- infer protected traits;
- perform face recognition;
- infer attendance from a speaking role, registration link, social activity, or photograph;
- republish contact information without provenance and a public or authorized basis.

Use `not-authorized` or `unresolved` when the collection basis is unclear.

## Data Rules

- Preserve raw source wording.
- Do not overwrite raw data during normalization.
- Use stable run-local IDs.
- Resolve every foreign key.
- Attach field-level provenance to material values.
- Distinguish unknown, not applicable, not published, inaccessible, not authorized, and unresolved data.
- Preserve original text with every translation.
- Do not merge entities from name similarity alone.
- Record every entity-resolution decision.

Read `references/data-model.md` before extraction or normalization.

## Validation

Run:

```bash
python3 -m compileall -q tools tests
python3 -m unittest discover -s tests -v
python3 tools/validate_run.py tests/fixtures/valid-run
```

Run the validator against each invalid fixture. Each invalid fixture must fail.

For a real run, use:

```bash
python3 tools/validate_run.py runs/<run-id>
```

Use a stage boundary before the run is complete:

```bash
python3 tools/validate_run.py runs/<run-id> --stage discovery
python3 tools/validate_run.py runs/<run-id> --stage raw
python3 tools/validate_run.py runs/<run-id> --stage normalized
```

Do not report success for a command that did not run.

## Circular Imports

Check Python compilation and imports before and after changes. Fix introduced, touched, or validation-blocking cycles with minimal changes.

Do not add a dependency only to detect cycles.

## Project Memory

Read `PROJECT_MEMORY.md` before changes.

Append an error entry only after you reproduce and fix the error. Include the exact reproduce and verification commands.

Append durable architecture or workflow decisions. Do not fabricate history.

## Stop Conditions

Stop and report the blocker when:

- a run ID already exists;
- required scope remains ambiguous;
- upstream artifacts are missing or malformed;
- a requested source needs authentication or access-control bypass;
- attendee authorization is unclear;
- no reviewed direct source supports extraction;
- validation fails and a safe fix is not available;
- reporting would require unsupported facts;
- the task requires a prohibited service or product expansion.

## Repository Boundaries

Do not add a hosted site, API server, database, CRM, crawler service, authentication system, registration system, outreach tool, browser extension, or paid integration without separate approval.

Preserve `.llm-harness`. Do not commit ordinary runtime runs, caches, environments, credentials, local provider state, dependencies, or build artifacts.
