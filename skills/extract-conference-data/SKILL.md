---
name: extract-conference-data
description: Extract source-faithful conference records from a run's frozen discovery ledgers and reviewed public or user-authorized evidence. Use after discovery, not to discover new providers, normalize entities, or write the final report.
---

# Extract Conference Data

## Purpose

Convert reviewed discovery evidence into one raw, provenance-rich dataset. Preserve source wording, contradictions, gaps, and authorization limits for later normalization.

## Required Inputs

Read these exact upstream artifacts:

- `runs/<run-id>/REQUEST.md`
- `runs/<run-id>/AGGREGATORS.md`
- `runs/<run-id>/CONFERENCE_SOURCES.md`

For `refresh` mode, also read the source run named by `REQUEST.md` only as comparison context. Never modify it.

Stop if an upstream artifact is missing, malformed, inconsistent with the run ID, or not frozen. Stop if `RAW_CONFERENCES.json` already exists.

## References

Read:

- [`../../references/source-policy.md`](../../references/source-policy.md)
- [`../../references/data-model.md`](../../references/data-model.md)
- [`../../references/privacy.md`](../../references/privacy.md)

Do not load the entity-resolution reference; this stage records possible duplicates but does not resolve them.

## Output

Write only:

- `runs/<run-id>/RAW_CONFERENCES.json`

The file must be valid JSON and conform to the raw-data schema when that schema is present.

## Workflow

1. Verify every referenced aggregator and source ID against the frozen ledgers.
2. Select only sources marked extraction-eligible. Re-open and review the direct public content when it remains available.
3. Create one raw conference record for every in-scope candidate. Keep uncertain candidate identities separate.
4. Address every conference branch listed in the data-model reference. Assign exactly one allowed collection status to every branch.
5. Preserve source wording in raw values. Record field-level provenance, access context, confidence, contradictions, and unresolved fields.
6. Extract related people, committees, sessions, registration offers, venue details, sponsors, hotels, and attendee data only when supported and within the request.
7. Apply the attendee mode and authorization rules before collecting any attendee-level value.
8. Record inaccessible or unpublished data with the correct status and reason. Do not interpret absence as a negative fact.
9. In `refresh` mode, preserve source-run references needed for later comparison without copying unsupported earlier facts into the new raw dataset.
10. Check JSON syntax, source references, branch coverage, statuses, and privacy basis before handoff.

## Evidence and Transformation Rules

- Use direct reviewed source IDs for conference facts. Aggregator IDs may appear only in observed-listing provenance.
- Do not use search snippets, inaccessible content, or repeated syndication as verified evidence.
- Do not normalize away source spelling, punctuation, date wording, prices, names, or other literal values.
- Do not translate, merge, deduplicate, or choose a canonical entity in this stage.
- Represent conflicting supported values independently and link each value to its sources.
- Use `null` only for an unknown value. Use branch status and reason fields for not applicable, not published, inaccessible, not authorized, and unresolved conditions.
- Coordinates, contacts, prices, attendance, and identity claims require explicit supporting evidence.

## Privacy and Access Boundaries

- Collect only relevant public professional information or user-authorized attendee data.
- Do not authenticate, bypass access controls, solve challenges, probe systems, scan systems, enumerate hidden endpoints, or access private registration records.
- Do not guess identities, profiles, email addresses, telephone numbers, attendance, or source URLs.
- Do not collect secrets, credentials, payment data, sensitive personal data, or protected-trait inferences.
- Do not perform face recognition or infer identity from photographs or unsupported profile similarity.
- Mark the affected branch `not-authorized` or `unresolved` when the collection basis is unclear.

## Frozen Handoff

Complete and review `RAW_CONFERENCES.json`, then declare it frozen.

- Hand the exact file to `normalize-conference-data`.
- Do not modify `REQUEST.md`, `AGGREGATORS.md`, or `CONFERENCE_SOURCES.md`.
- Do not create normalized artifacts or `REPORT.md`.
- If a material defect is found after the handoff, do not edit the frozen file. Stop and require a new run ID.

## Stop Conditions

Stop and report the exact blocker when:

- an upstream artifact is absent, malformed, mutable, or internally inconsistent;
- no reviewed direct source supports extraction for any candidate;
- the requested path requires prohibited access or unsupported inference;
- attendee authorization is missing or unclear;
- source IDs or provenance cannot be resolved;
- a target output would overwrite an existing artifact;
- valid JSON cannot be produced without inventing data.
