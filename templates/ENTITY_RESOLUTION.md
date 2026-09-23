# ENTITY_RESOLUTION.md — Entity-Resolution Decision Log Template

> This is an intentional decision-log template, not live research. Replace bracketed instructions with actual normalization decisions. Keep the exact artifact name `ENTITY_RESOLUTION.md`.

## Run

- Run ID: `[run ID from REQUEST.md]`
- Normalization completed at: `[ISO 8601 date-time]`
- Raw artifact preserved: `RAW_CONFERENCES.json`
- Decision records: `[count]`

## Method

- Normalize formatting without changing source meaning.
- Never merge entities because names alone match.
- Compare official domains, dates, locations, organizations, roles, and source relationships.
- Keep candidates separate when evidence is insufficient.
- Record every merge, split, alias, rejected candidate, and unresolved candidate.
- Preserve original IDs and alias redirects after an applied merge.
- Do not infer identity from photographs or unsupported profile similarity.

## Decision Summary

| Decision type | Proposed | Applied | Rejected | Unresolved |
|---|---:|---:|---:|---:|
| Merge | `[count]` | `[count]` | `[count]` | `[count]` |
| Split | `[count]` | `[count]` | `[count]` | `[count]` |
| Alias | `[count]` | `[count]` | `[count]` | `[count]` |
| Rejected candidate | `[count]` | `[count]` | `[count]` | `[count]` |
| Unresolved candidate | `[count]` | `[count]` | `[count]` | `[count]` |

## Decision Record

Repeat this section for every decision, including rejected and unresolved candidates.

### `[ER###] [Decision Type]: [Short Label]`

- Decision ID: `[ER###]`
- Decision type: `[merge | split | alias | rejected-candidate | unresolved-candidate]`
- Outcome: `[applied | rejected | unresolved]`
- Entity type: `[conference | conference-series | organization | person | venue | session-event | registration-offer | sponsor-partnership | hotel | attendee | source]`
- Candidate or original IDs: `[IDs compared]`
- Canonical ID: `[retained ID or none]`
- Created IDs: `[IDs created by a split or none]`
- Source IDs: `[A### and S### IDs used in the comparison]`
- Compared attributes: `[attribute, value per candidate, match or conflict, and supporting source IDs]`
- Corroborating evidence: `[domains, dates, locations, organizations, roles, or source relationships]`
- Conflicting evidence: `[material conflicts or none]`
- Confidence: `[high | medium | low]`
- Rationale: `[evidence-based explanation; name similarity alone is insufficient]`
- Alias redirects: `[old ID -> canonical ID mappings or none]`
- Preserved source wording: `[names or labels retained from the raw artifact]`
- Review note: `[manual review need, limitation, or none]`

## Alias Redirect Map

| Original ID | Canonical ID | Decision ID | Reason |
|---|---|---|---|
| `[old ID]` | `[retained ID]` | `[ER###]` | `[merge or alias rationale]` |

## Refresh Differences

Complete this section only in `refresh` mode.

| Entity ID | Source-run state | New-run state | Addition, removal, change, or unresolved difference | Supporting decision or source IDs |
|---|---|---|---|---|
| `[ID]` | `[earlier value]` | `[new value]` | `[classification and explanation]` | `[ER###, A###, or S###]` |

