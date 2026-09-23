---
name: report-conferences
description: Produce the single authoritative cited conference report from frozen normalized data and provenance artifacts. Use only after normalization, not to search, extract, change entities, or create additional final reports.
---

# Report Conferences

## Purpose

Create one concise, evidence-bounded report that answers the request, summarizes each conference, and exposes material limitations.

## Required Inputs

Read these exact frozen artifacts:

- `runs/<run-id>/REQUEST.md`
- `runs/<run-id>/AGGREGATORS.md`
- `runs/<run-id>/CONFERENCE_SOURCES.md`
- `runs/<run-id>/RAW_CONFERENCES.json`
- `runs/<run-id>/NORMALIZED_CONFERENCES.json`
- `runs/<run-id>/ENTITY_RESOLUTION.md`
- `runs/<run-id>/QUALITY_REPORT.md`

For `refresh` mode, also read the named source run's frozen report and supporting artifacts. Never modify the source run.

Stop if an upstream artifact is missing, malformed, inconsistent, not frozen, or fails required validation. Stop if `REPORT.md` already exists.

## References

Read:

- [`../../references/source-policy.md`](../../references/source-policy.md)
- [`../../references/data-model.md`](../../references/data-model.md)
- [`../../references/privacy.md`](../../references/privacy.md)

Read [`../../references/entity-resolution.md`](../../references/entity-resolution.md) only when a recorded decision needs interpretation beyond `ENTITY_RESOLUTION.md`.

## Output

Write only:

- `runs/<run-id>/REPORT.md`

This is the run's only authoritative final report.

## Workflow

1. Reconcile the request with normalized records, quality findings, source ledgers, and material raw contradictions.
2. State the search scope, collection date, aggregator coverage, and direct-source coverage without claiming exhaustive web coverage.
3. Create a conference comparison table with dates, location, venue, format, registration state, official URL, and stable citations.
4. Write one summary for every normalized conference.
5. Include supported people, committees, schedules, sponsors, events, hotels, and attendee information when relevant to the request.
6. Include material data-quality warnings, unresolved conflicts, entity-resolution notes, translation notes, inaccessible-source effects, and collection gaps.
7. In `refresh` mode, report meaningful additions, removals, changes, and unresolved differences from the named source run.
8. Verify every material claim against its field-level provenance and stable source ID. Include only normalized values; do not append an unsupported name, date, count, role, URL, or conclusion to a supported statement.
9. Run `python3 tools/validate_run.py runs/<run-id>` after writing the report. Do not claim completion if validation fails.

## Reporting Rules

- Cite direct-source claims with stable source IDs such as `[S001]`.
- Use aggregator IDs such as `[A001]` only for claims that a listing was observed.
- Write `Insufficient evidence` when the frozen artifacts do not support a requested fact.
- Preserve contradictions instead of silently choosing a convenient value.
- Keep identity and organizer bullets value-focused. Ensure date, URL, person-role, and attendance statements contain no extra values absent from the normalized records.
- Do not rank or recommend conferences unless the request asks for that analysis and the evidence supports it.
- Do not infer popularity or attendance unless the request asks for that analysis and the evidence supports it.
- Do not introduce facts from memory, a new web search, or an uncited source.
- In refresh sections, name the actual changed field or collection. If a previous value is shown, also state the current normalized value.
- Do not create a second final report, dashboard, database, or recommendation product.

## Privacy Boundaries

- Report personal data only when it is relevant, intentionally public or user-authorized, and linked to provenance and authorization basis.
- Minimize business contact details; do not republish them when the request does not require them.
- Do not expose private attendee data, sensitive personal data, secrets, credentials, payment data, or unsupported identities.
- Do not imply attendance from a speaking role, registration link, sponsorship, social activity, or photograph.
- Use `Insufficient evidence`, `not-authorized`, or the applicable recorded status when the basis is inadequate.

## Frozen Handoff

Complete and review `REPORT.md`, run complete validation, then declare the run complete and frozen.

- Do not modify any upstream artifact.
- If a material defect is found after completion, preserve the run and create a new refresh run with a new ID.

## Stop Conditions

Stop and report the exact blocker when:

- an upstream artifact is missing, malformed, mutable, inconsistent, or invalid;
- a material claim lacks a resolvable source citation;
- reporting would require a prohibited inference or privacy violation;
- refresh comparison cannot identify or read the named source run;
- the target report would overwrite an existing artifact;
- complete-run validation fails and no safe report-only fix is available.
