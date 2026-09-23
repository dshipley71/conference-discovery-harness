# Conference Discovery Harness — Project Memory

Read this file before each change. Preserve earlier entries.

## Error Entry Format

```text
## E-N. Short title
**Symptom:** observed failure
**Cause:** verified root cause
**Fix:** applied correction
**Reproduce:** exact failing command
**Verify:** exact passing command
```

Add an error entry only after the error was reproduced and fixed.

## Decision Entry Format

```text
## D-N. Short title
**Decision:** selected approach
**Rationale:** reason for the decision
**Rejected alternatives:** alternatives and rejection reasons
```

## D-1. Four frozen workflow stages

**Decision:** Use discovery, extraction, normalization, and reporting as the four operational stages.

**Rationale:** Frozen handoffs make source review, data cleaning, and report generation independently auditable.

**Rejected alternatives:** One large research agent obscures provenance. More agents add coordination without a confirmed need.

## D-2. Markdown and JSON with one Python validator

**Decision:** Use Markdown skills and ledgers, JSON datasets, JSON Schemas, and one Python standard-library validator.

**Rationale:** LLMs perform semantic research and resolution. Deterministic code checks structure and references.

**Rejected alternatives:** A hosted service, database, package dependency, or source-specific scraper expands version 1 scope.

## D-3. Public or authorized people data only

**Decision:** Collect attendee and contact data only when it is intentionally public or user-authorized.

**Rationale:** Conference research does not justify private registration access, guessed contacts, or sensitive-person enrichment.

**Rejected alternatives:** Login automation, contact guessing, face recognition, and private attendee collection are prohibited.

## D-4. Aggregators are discovery evidence

**Decision:** Use aggregator records for observed-listing claims. Prefer reviewed direct sources for conference facts.

**Rationale:** Aggregator records can be stale, duplicated, or incomplete.

**Rejected alternatives:** Treating repeated listings as independent confirmation would inflate confidence and duplicate conferences.

## D-5. Provenance and branch-state enforcement

**Decision:** Require field-level provenance for every nonempty material field in normalized domain records. Reject normalized values when the corresponding raw branch is not `complete` or `partial`.

**Rationale:** Matching status labels alone does not prevent unsupported normalized facts or partially traceable records.

**Rejected alternatives:** Relying only on schema presence checks would allow material values without evidence and values that contradict explicit absence statuses.

## D-6. Attendee and authorization literals

**Decision:** Allow public aggregate attendance facts in `public-only` mode. Require `user-authorized-input` for individual attendee records. Use `intentionally-public` and `user-authorized-input` as authorization-basis literals.

**Rationale:** This separates public professional people records from attendee records and keeps policy text, schemas, and validation behavior consistent.

**Rejected alternatives:** Public individual attendee collection creates unnecessary privacy risk. Alternate literals make run artifacts incompatible with the schemas.

## D-7. Controlled source-claim vocabulary

**Decision:** Require each reviewed source to declare support with controlled claim tokens, and require every retained raw branch and reported material claim to use a compatible token.

**Rationale:** Stable claim semantics prevent a citation from being treated as support for facts that the source record does not cover.

**Rejected alternatives:** Free-form source descriptions are useful context but cannot deterministically prove claim coverage.

## D-8. Cross-artifact narrative reconciliation

**Decision:** Reconcile quality metrics, gap narratives, attendee checks, comparison cells, and conference-summary facts against normalized JSON.

**Rationale:** Valid Markdown structure and valid citations do not prevent a human-readable report from contradicting the underlying dataset.

**Rejected alternatives:** Reviewing only JSON or checking only for citations allows fabricated or stale report text to pass.

## D-9. Field-specific refresh reporting

**Decision:** Compare refresh runs recursively after excluding provenance-only metadata, and require each refresh narrative to identify an actual changed field, entity collection, or changed value.

**Rationale:** A generic change statement can conceal a different normalized-data change and make refresh outputs misleading.

**Rejected alternatives:** Requiring only the words addition, removal, or change verifies format but not the truth of the refresh summary.
