# CONFERENCE_SOURCES.md — Synthetic Test Fixture

> Synthetic test data only. This ledger is not live conference research.

## Run

- Run ID: `valid-run`
- Discovery completed at: `2026-09-22T00:01:00Z`
- Candidate conferences: `1`
- Reviewed direct sources: `1`
- Failed or ineligible leads: `0`

## Conference Source Record

### S001 Synthetic Validation Conference Source

- Stable source ID: `S001`
- Candidate conference ID: `C001`
- Candidate conference name and aliases: Synthetic Validation Conference
- Source class: official-conference
- Title: Synthetic Validation Conference
- Publisher or owner: Synthetic Conference Organization
- Public URL: https://conference.example.invalid/
- Publication or update date: 2099-01-01
- Access date: 2026-09-22
- Conference relationship: Synthetic official conference site.
- Review state: reviewed
- Bounded excerpt or faithful summary: The synthetic page identifies the conference, organizer, one professional, and a prior-edition aggregate attendance count.
- Supported fields or claims: identity, dates, official-url, organizers, people, attendance, provenance, confidence, contradictions
- Reliability: high; synthetic first-party fixture
- Independence: first-party
- Limitations: Synthetic test evidence only.
- Extraction eligibility: eligible
- Eligibility rationale: The fixture models reviewed direct public content.

## Failed and Ineligible Leads

None.

## Conference-to-Source Coverage

| Candidate conference ID | Official conference source | Other eligible source IDs | Unsupported branches | Discovery status |
|---|---|---|---|---|
| C001 | S001 | none | schedule, registration, venue, sponsors, hotels | ready-for-extraction |

## Freeze Record

- Frozen at: `2026-09-22T00:02:00Z`
- Frozen by: `synthetic-test`
- Downstream rule: Do not modify this fixture artifact during validation.
