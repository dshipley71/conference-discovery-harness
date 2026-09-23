# CONFERENCE_SOURCES.md — Conference Source Ledger Template

> This is an intentional research template, not live research. Replace bracketed instructions with reviewed public evidence. Keep the exact artifact name `CONFERENCE_SOURCES.md`.

## Run

- Run ID: `[run ID from REQUEST.md]`
- Discovery completed at: `[ISO 8601 date-time]`
- Candidate conferences: `[count]`
- Reviewed direct sources: `[count]`
- Failed or ineligible leads: `[count]`

## Source Rules

- Prefer official conference and organizer pages for conference facts.
- Prefer official venue, registration, sponsor, hotel, and organization pages for related facts.
- Treat search snippets, inaccessible links, repeated syndication, and unreviewed aggregator records as discovery leads only.
- Use `A###` citations only for observed-listing claims. Use reviewed `S###` sources for extracted conference facts.

## Conference Source Record

Repeat this section once for every reviewed or attempted source.

### `[S###] [Source Title]`

- Stable source ID: `[S###]`
- Candidate conference ID: `[C### or unresolved]`
- Candidate conference name and aliases: `[source wording]`
- Source class: `[official-conference | official-organizer | official-registration | official-schedule | official-venue | official-sponsor | official-hotel | public-organization | public-government | other-direct]`
- Title: `[page or document title]`
- Publisher or owner: `[organization or person]`
- Public URL: `[URL]`
- Publication or update date: `[YYYY-MM-DD, source wording, not published, or unresolved]`
- Access date: `[YYYY-MM-DD]`
- Conference relationship: `[official site, organizer, venue, registration provider, schedule, sponsor, hotel, or other relationship]`
- Review state: `[reviewed | partially-reviewed | inaccessible | removed | paywalled | unresolved]`
- Bounded excerpt or faithful summary: `[short excerpt within quotation limits or a faithful summary]`
- Supported fields or claims: `[comma-separated controlled tokens: identity, series, organizers, description, dates, official-url, people, committees, schedule, registration, venue, sponsors, hotels, attendance, provenance, confidence, contradictions, unresolved-fields]`
- Reliability: `[high | medium | low | unresolved, with reason]`
- Independence: `[first-party | independent-direct | syndicated | unresolved, with reason]`
- Limitations: `[semicolon-separated dynamic content, missing date, conflict, incomplete page, or none observed]`
- Extraction eligibility: `[eligible | ineligible | limited]`
- Eligibility rationale: `[why the reviewed content can or cannot support extraction]`

## Failed and Ineligible Leads

Preserve each failure. Do not promote a failed lead into verified evidence.

| Lead ID | Candidate conference | Source class | URL | Failure reason | Access date | Extraction eligibility | Follow-up |
|---|---|---|---|---|---|---|---|
| `[S-FAIL-###]` | `[name or unresolved]` | `[class]` | `[URL]` | `[snippet-only, inaccessible, blocked, removed, paywalled, duplicate syndication, unreviewed, or other reason]` | `[YYYY-MM-DD]` | `ineligible` | `[replacement source ID or unresolved]` |

## Conference-to-Source Coverage

| Candidate conference ID | Official conference source | Other eligible source IDs | Unsupported branches | Discovery status |
|---|---|---|---|---|
| `[C###]` | `[S### or none found]` | `[S### list or none]` | `[branches or none]` | `[ready-for-extraction | blocked | unresolved]` |

## Freeze Record

- Frozen at: `[ISO 8601 date-time]`
- Frozen by: `[agent or operator identifier]`
- Downstream rule: Do not modify this artifact after discovery handoff.
