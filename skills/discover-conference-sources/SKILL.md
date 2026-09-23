---
name: discover-conference-sources
description: Discover public conference aggregators, matching listings, official conference sites, and other direct sources for a Conference Discovery Harness run. Use for the discovery stage or discovery-only mode, not for fact extraction, normalization, or reporting.
---

# Discover Conference Sources

## Purpose

Create reviewable source ledgers for one run. This stage finds sources and determines whether they are eligible for later extraction. It does not extract the full conference dataset.

## Required Inputs

Read:

- `runs/<run-id>/REQUEST.md`
- `runs/<source-run-id>/REQUEST.md` when mode is `refresh`
- the source run's frozen discovery artifacts when mode is `refresh`

Before research, confirm that `REQUEST.md` contains every required request value from `AGENTS.md`. Ask one focused question and stop when conference identity, dates, geography, attendee authorization, or another material boundary is ambiguous.

Stop if the run ID is not filesystem-safe, the target run represents an earlier frozen run, or either target output already exists.

## References

- Always read [`../../references/source-policy.md`](../../references/source-policy.md).
- Read [`../../references/privacy.md`](../../references/privacy.md) before seeking people, contact, or attendee-related sources.

Do not load the data-model or entity-resolution reference during ordinary discovery.

## Outputs

Write only:

- `runs/<run-id>/AGGREGATORS.md`
- `runs/<run-id>/CONFERENCE_SOURCES.md`

Use stable run-local aggregator IDs and source IDs defined by the source policy.

## Workflow

1. Derive a bounded search plan from the complete request, including dates, geography, topics, search languages, known sources, source rules, exclusions, and result limit.
2. Review relevant aggregator providers and their public listing pages. Record the required aggregator fields, matching listings, duplicate or syndication relationships, limitations, and failures.
3. Turn observed listings and other public leads into conference candidates. Do not treat a listing as a verified conference fact.
4. For each candidate, seek the official conference site and relevant direct public sources such as organizer, venue, sponsor, hotel, institution, or government pages.
5. Review the actual public page before marking a source extraction-eligible. Preserve blocked, removed, inaccessible, paywalled, or unresolved leads with their failure reason.
6. Reconcile duplicate listings and syndicated copies without treating them as independent confirmation.
7. In `refresh` mode, preserve the source run and note cross-run candidate and source relationships that later stages can compare.
8. Check both ledgers for stable IDs, complete required fields, truthful access status, and compliance with the request.

If a bounded search finds no qualifying results, write completed zero-result ledgers that record the attempted scope and failures. Do not present an empty scaffold or claim exhaustive coverage.

## Evidence and Access Rules

- Aggregator IDs support only claims that a listing was observed.
- Search snippets, inaccessible pages, repeated syndication, and unreviewed aggregator records are discovery leads only.
- Prefer reviewed official or first-party pages for conference facts.
- Use bounded excerpts or faithful summaries. Preserve publication or update dates when available and record access dates.
- Do not authenticate, bypass controls, solve access challenges, probe systems, enumerate hidden endpoints, or use guessed URLs as evidence.
- Do not collect private attendee data, guessed contacts, credentials, payment data, sensitive personal data, or unsupported identities.

## Frozen Handoff

Complete and review both output files, then declare them frozen together.

- In `discovery_only` mode, stop after the handoff.
- In `full` or `refresh` mode, hand the exact frozen files to `extract-conference-data`.
- Do not perform extraction, normalization, entity resolution, or reporting in this stage.
- If a material defect is found after the handoff, do not edit the frozen files. Stop and require a new run ID.

## Stop Conditions

Stop and report the exact blocker when:

- required request scope is missing or materially ambiguous;
- attendee authorization is unclear for a requested discovery path;
- an output path would overwrite an existing artifact;
- a requested source requires authentication, bypass, probing, or another prohibited action;
- public availability or authorization is unclear;
- source requirements conflict or cannot be followed;
- no reviewed direct source is eligible for extraction after the bounded search.
