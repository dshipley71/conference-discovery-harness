# Privacy and Authorization

## Scope

Use only intentionally public content or data the user is authorized to provide for this run. Public availability does not remove the duties to minimize data, preserve provenance, and respect the stated objective.

## Attendee Modes

### `public-only`

Collect only public aggregate attendance facts that a reviewed source explicitly states.

Do not collect individual attendee records in `public-only` mode. Public speakers, committee members, organizers, and other professional conference participants are people records, not attendee records, and remain subject to the allowed-people rules.

Do not infer attendance from a speaking role, registration link, sponsor role, follower relationship, social activity, photograph, or intended-audience description.

### `user-authorized-input`

Collect only the minimal relevant attendee data that the user supplies or explicitly identifies as authorized input. Record:

- authorization basis;
- supplying party;
- scope and purpose;
- access or receipt date;
- applicable restrictions.

This mode does not authorize access to a private registration system, account, or third-party dataset.

### `disabled`

Do not collect attendee records or aggregates. Mark the attendee branch `not-authorized` with the reason `attendee-mode-disabled`.

## Allowed People Data

Collect a field only when it is relevant and supported:

- name;
- public professional role;
- organization;
- job title;
- official biography;
- conference role;
- explicitly published business email;
- explicitly published business telephone number;
- public aggregate attendance fact;
- user-authorized attendee data.

Attach source provenance and authorization basis. A page URL used as provenance is not permission to enrich or guess another profile.

## Contact Rules

An email address or telephone number is eligible only when:

1. it is explicitly published as a business contact by the person, employer, conference, organizer, or another authorized source;
2. the reviewed page and source ID are recorded;
3. the contact is relevant to the request;
4. republication is necessary for the requested output.

Do not derive addresses from naming patterns, domains, cached snippets, data brokers, or similar contacts. Do not republish contact details merely because they are public.

## Prohibited Data and Actions

Do not:

- access private registration or attendee records;
- authenticate or use an account;
- bypass access controls, paywalls, robots restrictions, or challenges;
- probe or scan systems;
- enumerate hidden endpoints or guess private routes;
- guess email addresses, telephone numbers, identities, or profiles;
- collect secrets, credentials, payment data, or authentication artifacts;
- collect sensitive personal data;
- infer protected traits;
- perform face recognition;
- infer identity from photographs or unsupported profile similarity;
- infer attendance without explicit evidence;
- use a public source for a purpose outside the request;
- republish personal contact information without provenance and a public or authorized basis.

Do not use an apparent public misconfiguration or exposed private record as intentionally public authorization.

## Sensitive and Irrelevant Data

Exclude data about private life, health, disability, biometrics, exact personal location, government identifiers, financial information, protected traits, account access, and other sensitive personal matters unless a requirement explicitly allows it and the user has lawful, specific authorization. This harness does not create such an allowance.

Remove irrelevant personal details from biographies and free text. Preserve only the professional information needed for conference research.

## Authorization Record

For intentionally public or user-authorized data, record an authorization object or equivalent fields:

- basis: `intentionally-public` or `user-authorized-input`;
- scope;
- source or supplying party;
- date recorded;
- restrictions;
- source IDs or local input reference.

When the basis is unclear, do not collect the value. Use `not-authorized` or `unresolved` and explain why.

## Stage Rules

### Discovery

Locate public conference-related pages. Do not enumerate people or attendee sources beyond the request. Stop a source path when access or authorization is unclear.

### Extraction

Apply attendee mode before reading or recording attendee-level data. Keep contact values source-faithful and attach provenance.

### Normalization

Do not enrich people records. Do not use photographs or unsupported profile similarity for entity resolution. Exclude prohibited raw values from normalized output and record the quality issue.

### Reporting

Minimize personal data in the final report. Include contacts or attendee-level details only when directly requested, supported, and authorized. Prefer aggregate statements when they answer the request.

## Stop Conditions

Stop the affected collection or reporting path when:

- public availability is unclear;
- attendee authorization is absent or ambiguous;
- a source requires authentication or bypass;
- identity depends on guessing, a photograph, or unsupported similarity;
- a contact is not explicitly published as a relevant business contact;
- the request would expose private, sensitive, credential, payment, or registration data.

Record the blocker without reproducing the restricted value.
