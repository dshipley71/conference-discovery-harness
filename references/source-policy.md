# Source Policy

## Purpose

Use this policy to decide which public sources may support discovery, extraction, and reporting claims. It does not authorize access beyond intentionally public pages or user-authorized input.

## Stable Source IDs

IDs are unique within one run:

- `A001`, `A002`, and so on identify aggregator providers and reviewed listing records in `AGGREGATORS.md`.
- `S001`, `S002`, and so on identify conference-related sources in `CONFERENCE_SOURCES.md`.

Never reuse an ID for a different record. A refresh creates new run-local IDs and may record cross-run links to the source run's IDs.

## Source Roles

### Aggregators

An aggregator collects or republishes conference listings across multiple events. Use it to:

- discover candidates;
- document that a listing was observed;
- understand the aggregator's observed geographic, topical, language, and date coverage.

An aggregator ID supports only an observed-listing claim. It does not support a final conference date, venue, price, speaker, attendee, or status claim.

### Direct sources

A direct source has a first-party or authoritative relationship to the supported fact. Typical classes are:

- official conference or event page;
- official organizer page;
- official venue page;
- official sponsor, exhibitor, or partner page;
- official hotel or conference booking page;
- official institution, association, or government page;
- user-authorized input for the specific authorized data.

Prefer the source closest to the fact. For example, use the official registration page for ticket terms and the official venue page for venue contact details.

### Independent public sources

An independent publication may corroborate a fact when its content is reviewable and its relationship and limitations are recorded. It does not replace a more direct official source when one is available.

## Reviewability and Eligibility

A web source is reviewed only when the executor opens the public page and inspects the content that supports the claim.

A source is extraction-eligible only when:

1. its content is intentionally public or specifically user-authorized;
2. the actual supporting content was reviewed;
3. its publisher, URL, conference relationship, access date, and supported claims are recorded;
4. its limitations and conflicts are preserved;
5. the requested use complies with `references/privacy.md`.

These are discovery leads, not verified direct evidence:

- search-result snippets;
- inaccessible, blocked, removed, or paywalled pages;
- guessed or unreviewed URLs;
- repeated syndication;
- an unreviewed aggregator record.

Preserve each failed lead and its failure reason. Do not convert it into a supported claim.

## Supported-Claim Tokens

Use only these tokens in source ledgers and JSON source records:

`observed-listing`, `identity`, `series`, `organizers`, `description`, `dates`, `official-url`, `people`, `committees`, `schedule`, `registration`, `venue`, `sponsors`, `hotels`, `attendance`, `provenance`, `confidence`, `contradictions`, and `unresolved-fields`.

An `A###` aggregator record uses only `observed-listing`. An `S###` direct source lists every branch that its reviewed content can support. Do not use a source for a branch whose token is absent.

## Aggregator Record Contract

For each aggregator, record:

- stable aggregator ID;
- provider name;
- canonical public URL;
- observed geography;
- observed topics;
- observed languages;
- observed date coverage;
- reviewed listing or search page;
- access date;
- whether direct content was reviewable;
- matching listings and their displayed wording;
- duplicate or syndication links;
- reliability;
- limitations;
- access failures.

The coverage fields describe only what was observed during the bounded run. Never claim that the aggregator search or web coverage is exhaustive.

## Conference Source Record Contract

For each source, record:

- stable source ID;
- candidate conference and known aliases;
- source class;
- page title;
- publisher or owner;
- public URL;
- publication or update date when available;
- access date;
- relationship to the conference;
- bounded excerpt or faithful summary;
- supported fields or claims;
- reliability;
- independence;
- limitations;
- extraction eligibility and reason.

Use a short excerpt only when exact wording matters. Otherwise write a faithful summary. Do not copy an entire page or use a quotation outside the evidence needed for the record.

## Reliability and Independence

Describe reliability as a reasoned assessment, not a numeric fact invented from appearance.

Consider:

- whether the source owns or administers the claimed fact;
- whether the page is current and identifies the relevant conference edition;
- whether the content is specific rather than generic;
- whether other reviewed sources contradict it;
- whether the page is a syndicated copy.

Repeated pages under the same publisher, feed, press release, or listing network are one underlying source relationship. Record syndication links and do not count them as independent confirmation.

## Conflicts and Changes

Preserve conflicting supported values with separate source IDs, dates, and notes. Prefer neither value silently. Extraction records the conflict; normalization resolves it only when the evidence meets the entity-resolution rules.

For changing facts such as dates, venues, registration state, or schedules:

- record publication or update dates when available;
- distinguish a later update from an independent source;
- retain superseded wording when it is material to a refresh comparison.

## Citation Rules

- Cite direct factual claims with `[S###]`.
- Cite `[A###]` only to say that a listing was observed.
- Every material reported claim must resolve to a recorded source.
- If support is missing, write `Insufficient evidence`.
- A citation does not repair an ineligible source.

Do not rank, recommend, or infer popularity or attendance unless the request asks for that analysis and eligible evidence supports it.

## Access Boundaries

Use normal public navigation only. Do not:

- authenticate or use an account;
- evade access controls or paywalls;
- solve access challenges;
- probe or scan systems;
- enumerate hidden endpoints;
- guess private routes;
- use credentials, secrets, or payment data.

When public availability or authorization is unclear, stop that source path and record the failure.
