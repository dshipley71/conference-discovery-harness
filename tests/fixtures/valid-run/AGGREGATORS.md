# AGGREGATORS.md — Synthetic Test Fixture

> Synthetic test data only. This ledger is not live conference research and does not claim exhaustive coverage.

## Run

- Run ID: `valid-run`
- Discovery completed at: `2026-09-22T00:01:00Z`
- Search scope summary: One synthetic conference in Exampleland during June 2099.
- Coverage statement: This ledger records only the synthetic listing used by the fixture.

## Coverage Summary

| Metric | Value |
|---|---:|
| Aggregators reviewed | 1 |
| Reviewable aggregators | 1 |
| Matching listings observed | 1 |
| Duplicate or syndicated listings | 0 |
| Inaccessible or failed leads | 0 |

## Aggregator Record

### A001 Synthetic Aggregator

- Stable aggregator ID: `A001`
- Provider name: Synthetic Aggregator
- Canonical public URL: https://aggregator.example.invalid/
- Observed geography: Exampleland
- Observed topics: validation
- Observed languages: en
- Observed date coverage: June 2099
- Reviewed listing page: https://aggregator.example.invalid/listing/synthetic-validation-conference
- Access date: 2026-09-22
- Reviewability: reviewed
- Reliability: medium; synthetic fixture
- Limitations: Synthetic test evidence only.
- Access failures: none

#### Matching Listings

| Listing ID | Observed title | Listing URL | Dates as displayed | Location as displayed | Candidate conference ID | Access date | Notes |
|---|---|---|---|---|---|---|---|
| A001-L001 | Synthetic Validation Conference | https://aggregator.example.invalid/listing/synthetic-validation-conference | 15 June 2099 | Example City | C001 | 2026-09-22 | Observed-listing claim only. |

#### Duplicate or Syndication Links

None.

## Failed Aggregator Leads

None.

## Freeze Record

- Frozen at: `2026-09-22T00:02:00Z`
- Frozen by: `synthetic-test`
- Downstream rule: Do not modify this fixture artifact during validation.
