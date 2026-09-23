---
name: normalize-conference-data
description: Normalize and translate frozen raw conference data, deduplicate records, resolve entities conservatively, and produce the normalized dataset and quality artifacts. Use after extraction, not to search sources or rewrite raw evidence.
---

# Normalize Conference Data

## Purpose

Transform one frozen raw dataset into structured, linked, and auditable conference entities while preserving the original evidence and every material resolution decision.

## Required Inputs

Read these exact upstream artifacts:

- `runs/<run-id>/REQUEST.md`
- `runs/<run-id>/AGGREGATORS.md`
- `runs/<run-id>/CONFERENCE_SOURCES.md`
- `runs/<run-id>/RAW_CONFERENCES.json`

For `refresh` mode, also read the complete frozen source run named by `REQUEST.md` for comparison. Never modify it.

Stop if an upstream artifact is missing, malformed, inconsistent, or not frozen. Stop if any target output already exists.

## References

Read:

- [`../../references/data-model.md`](../../references/data-model.md)
- [`../../references/entity-resolution.md`](../../references/entity-resolution.md)
- [`../../references/privacy.md`](../../references/privacy.md)

Read [`../../references/source-policy.md`](../../references/source-policy.md) only when resolving source eligibility, syndication, or provenance conflicts.

## Outputs

Write only:

- `runs/<run-id>/NORMALIZED_CONFERENCES.json`
- `runs/<run-id>/ENTITY_RESOLUTION.md`
- `runs/<run-id>/QUALITY_REPORT.md`

## Workflow

1. Validate raw JSON syntax, required branches, statuses, source references, and authorization basis.
2. Copy source-backed values into the normalized model without changing the frozen raw artifact.
3. Normalize whitespace, Unicode, case where semantically safe, punctuation, URLs, dates, telephone formats, country codes, and language codes.
4. Translate only when the output language requires it. Preserve the original text and every protected literal listed in the data-model reference.
5. Generate duplicate candidates using normalized values, then apply the conservative entity-resolution rules. Name similarity alone is never sufficient.
6. Assign unique run-local IDs with distinct prefixes. Resolve every foreign key and field-level provenance reference.
7. Preserve original IDs and alias redirects for merged entities. Keep unresolved candidates separate.
8. Record every merge, split, alias, rejected candidate, and unresolved candidate in both the normalized decision collection and `ENTITY_RESOLUTION.md`.
9. Verify that each retained normalized scalar is present in, or conservatively derived from, its cited raw evidence. Use a translation record when the output language changes the value.
10. Compute all required quality metrics and write every required check, gap, conflict, warning, and privacy result to `QUALITY_REPORT.md`.
11. Copy attendee privacy and authorization check sentences and results exactly into the required Markdown bullets. When an empty JSON quality list has a dedicated section, write only `None.` in that section.
12. In `refresh` mode, compare the new run with the named source run and record meaningful additions, removals, changes, cross-run matches, and unresolved differences.
13. Run `python3 tools/validate_run.py runs/<run-id> --stage normalized` when the validator is available. Correct only current-stage outputs. Stop if a safe correction is not possible.

## Transformation Rules

- Preserve meaning and source wording. Normalized values supplement raw values; they do not replace evidence.
- Do not cite a raw evidence pointer that lacks the normalized name, number, date, URL, role, contact value, or other retained scalar.
- Keep `null` distinct from `not-applicable`, `not-published`, `inaccessible`, `not-authorized`, and unresolved conflict.
- Preserve names, URLs, numbers, dates, prices, identifiers, and quotations in translations.
- Label LLM translations `llm-generated`. Do not claim certified translation without direct evidence.
- Treat repeated listings and syndicated copies as duplicate evidence, not independent confirmation.
- Do not lower an unresolved or not-authorized status merely to make the dataset appear complete.
- Do not repair missing evidence by inference.

## Privacy Boundaries

- Retain only people and attendee fields allowed by the request, attendee mode, provenance, and authorization basis.
- Do not enrich, guess, or infer contacts, identities, attendance, protected traits, or sensitive personal data.
- Do not use photographs or unsupported profile similarity for identity resolution.
- Record privacy and attendee-authorization checks in `QUALITY_REPORT.md`.
- If raw input contains prohibited data, do not propagate it. Record the issue and stop unless safe removal preserves the required evidence boundary.

## Frozen Handoff

Complete and review all three outputs, then declare them frozen together.

- Hand the exact outputs and frozen provenance artifacts to `report-conferences`.
- Never modify `RAW_CONFERENCES.json` or earlier artifacts.
- Do not create `REPORT.md`.
- If a material defect is found after the handoff, do not edit frozen outputs. Stop and require a new run ID.

## Stop Conditions

Stop and report the exact blocker when:

- an upstream artifact is missing, malformed, mutable, or inconsistent;
- prohibited data cannot be removed safely;
- entity identity would require unsupported inference;
- a foreign key or source reference cannot be resolved;
- translation would alter a protected literal or source meaning;
- a target output would overwrite an existing artifact;
- validation fails and no safe current-stage fix is available.
