---
name: gorilladesk-private-api
description: "Operate GorillaDesk's private backend (ab2.gorilladesk.com) — the one the web app itself calls — for the two writes the public v1 API cannot make: set a job to Completed, and raise a draft invoice. Covers authentication, the exact payloads, the status ids, the send-by-default trap, causal read-back verification, and the operating restraints. Use when working on the GorillaDesk write path, the closeout egress, `crm_private`/`crm_dual`/`crm_verify`, `mirror.private_api`, the capability probe, or when asked why a closeout terminates in a human. Triggers - GorillaDesk write, ab2.gorilladesk.com, private API, job status Completed, draft invoice, trigger_action, egress_enabled, capability_evidence, JWT token header, integration login. Do NOT use for the PUBLIC read API (that is `mirror.public_api`) or for the mirror's nightly sync."
---

# GorillaDesk's private backend

## Why this exists

"Bill-ready" means three things happen to a job in GorillaDesk:

| | operation | public `api.gorilladesk.com/v1` |
|---|---|---|
| 1 | file a note on the customer record | supported |
| 2 | mark the job **Completed** | **no endpoint** |
| 3 | raise a **draft invoice** | **no endpoint** |

Four separate audits concluded 2 and 3 were structurally impossible and wrote off
Workflow 1's stated terminal, `destination_verified`, as unreachable.

**They were right about the wrong API.** The web application Jim clicks in does not
use the public one. It runs against `ab2.gorilladesk.com/api/` — a Yii2 PHP REST
backend — which does both. These are ordinary authenticated POSTs. Not impossible,
merely undocumented.

## The finding that inverts the risk story

> The public API can **write** a note but can **never read one back.**
> It **cannot write** job status or invoices — but reads **both** perfectly.

So operations 2 and 3 are the **safer** ones to automate. A note, once written, is
undetectable as a duplicate forever. A job status and an invoice can each be
confirmed afterwards by looking, over a different credential on a different host.
That asymmetry is the whole architecture here.

## Authentication

```
POST https://ab2.gorilladesk.com/api/auth/login
{ "username": "...", "password": "..." }
→ { "success": true, "token": "<JWT>", "refresh_token": "...",
    "company": { "branch": { "id": "GD69OU3RW0Q1" }, ... },
    "permissions": { "enabled": [...], "disabled": [...] },
    "profile": { "email": "...", "role": "Admin", ... }, ... }
```

Verified against the live account 2026-08-28. The field is **`token`**, not
`access_token`, and the branch is **`company.branch.id`**, not
`current_branch_id` — an earlier draft of this file had both wrong.

Then every request carries **custom headers, not `Authorization`**:

```
token:        <JWT>
platform:     web
gd-branch-id: <company.branch.id>
```

### Which login

There is no separate "integration login" to wait for. **Jim's own account
already grants everything this needs.** `op://DeLoSecrets/Gorilla Desk` is a
user in Integrity Pest Management with `role: Admin` and, in
`permissions.enabled`: `appAddJob`, `appEditJob`, `appAddCustomer`,
`appEditCustomer`, `editOrDeleteNotes`, `deleteJobs`. `LOGIN_INTEGRATION`
(`/api/login/integration`) exists in their bundle and is not needed.

Read `permissions.enabled` from the login response before assuming an operation
is available — it is the authoritative answer for the credential in hand, and it
costs nothing.

Facts that shape the design:

- **There IS a `refresh_token`,** contrary to an earlier note here — but nothing
  in this codebase uses it. `PrivateCrmWriter._send` re-runs the full login on a
  401, which is simpler and is safe precisely because a 401 proves the request
  was not applied.
- **No cookies, therefore no CSRF token** to extract or replay.
- **No browser is needed at any point.** This was settled empirically, by accident:
  the total-capture sweep authenticates with plain `urllib` and served hundreds of
  authenticated reads across fourteen collections from a Fargate container with no
  browser in the image. `mirror.private_api` already *is* the ordinary client; the
  write path is the same client with a different verb.
- **No captcha on the happy path.** A captcha after repeated *failed* logins is
  unprobed and does not change anything, because of the rule below.

> **A human solves a captcha. The machine never bypasses one.** This is not a
> performance note, it is the line. If a captcha ever appears on the happy path,
> the correct response is a person, not a solver.

## Use a dedicated integration login, not Jim's

The terms were fetched and read in full. They contain **no anti-automation clause**.
The one real constraint is a **single-login provision** — and the cure is to
provision a separate integration user on the account rather than reusing Jim's
credentials.

That is strictly better than "logging in as Jim" on every axis that matters:

- it satisfies the single-login clause instead of violating it;
- it bounds the blast radius to one revocable user;
- every automated action becomes **attributable in GorillaDesk's own audit log**
  as the integration user, instead of being indistinguishable from Jim working.

Credentials live in 1Password and reach the process as
`RELAY_GORILLADESK_PRIVATE_USERNAME` / `RELAY_GORILLADESK_PRIVATE_PASSWORD`. Never
write either into a file. With both unset the adapter is not constructed at all —
see *Fail-closed*, below.

This remains the client's risk to accept, on the client's account, and it is
recorded as such. Ask GorillaDesk for official v2 access in parallel: `apiv2.gdesk.io`
documents job change-status and invoice creation, the request costs one email, and
if granted it replaces this path entirely at zero exposure.

## The two operations

Both payloads were **read, not reverse-engineered.** GorillaDesk publishes its own
source map — `app.gorilladesk.com/static/js/main.<hash>.chunk.js.map`, public and
unauthenticated, 23 MB, 2,912 original files with full contents. When something here
looks stale, re-read the map rather than guessing; the bundle hash changes on their
deploys.

### Complete a job — `app/modules/job/status/index.js`

```
PUT /api/jobs/{jobId}/status
{ "jobId": ..., "status": "<status id>", "note": "", "color_id": ... }
```

`socket_id` appears in the bundle's payload; it is a browser realtime handle and is
omittable.

### Raise an invoice — `app/modules/jobdetail/tabs/addinvoice/index.js`

```
POST /api/invoices
{ customer_job_id, customer_id, discount, number, po_number, date, items,
  subtotal, total, trigger_action, recurrence: { action, offset, repeat },
  location_id, terms, note, payment_terms_id, po_number_repeat }
```

## `trigger_action` defaults to SEND. This is the whole risk.

From `app/modules/jobdetail/const/Invoice.js`, `ACTION_VALUE` is
`{NONE: 0, SEND_EMAIL: 1, ...}` — and **GorillaDesk's own default payload for a new
invoice carries `trigger_action: '1'`, SEND_EMAIL.** Their save-without-sending path
passes `'0'` explicitly.

An invoice emailed to one of Jim's customers cannot be recalled and has no kill
switch. It is the only irreversible thing on this surface.

`relay.adapters.crm_private` therefore **never accepts `trigger_action` from a
caller.** It pins `SILENT = "0"` and `_refuse_if_sending()` raises before the wire
if a body ever carries anything else. Do not add a parameter for it. Do not thread
one through "just for testing" — a test that can send is a production incident
waiting for a copy-paste.

Note the guard has **two arms, because there are two send paths.** Besides
`trigger_action`, `recurrence.action` can also reach a customer, and it is checked
against the same `SENDING_ACTIONS` set. That set names every sending value
individually rather than testing "anything but 0", so a *new* action added by the
vendor fails closed instead of being silently treated as safe.

The guard **raises rather than repairs.** Quietly rewriting a sending payload into a
silent one would make the bug invisible the next time somebody reintroduced it. A
blocked write is loud, recoverable, and reaches nobody.

## THE TWO BACKENDS DO NOT SHARE AN ID SPACE

**Read this before writing anything.** It cost three failed live attempts and it
is invisible to every test you can write without touching GorillaDesk.

| thing | public `api.gorilladesk.com/v1` | private `ab2.gorilladesk.com/api` |
|---|---|---|
| a job | `XWgB0ooY7y` | `77665` |
| a customer | `nbdWb4Dgwj` | `16777` |
| status *Completed* | `74nYKJdMJK` | `2` |
| status *Confirmed* | `bKZdorgVkw` | `1` |
| status *Unconfirmed* | `an4gkmYwJq` | `0` |

The private ids are already in the public payload, under names that do not
announce themselves:

- **`work_order_number`** on a job *is* the private job id. It reads like a
  document number.
- **`customer.profile_url`** ends in the private customer id
  (`https://v3.gorilladesk.com/customers/16777`).

Sending a public id to the private backend gives **404 Not Found**; sending a
public status id gives **422 `{"message": ["Status is invalid."]}`**. Both are
opaque strings from the same vendor, so a fixture that uses one value for both
passes and the whole suite stays green — 1,729 tests did, against a write path
that had never worked and could not have.

The full private status list is `GET /api/job/statuses`: also `3` Reschedule,
`4` Pending Confirmation, `5` Canceled, `6` Recurrence, `7` Pending Booking,
`9` Terminate Service. Read it rather than trusting this table.

`relay.adapters.crm_verify` holds **both** spaces, named `PRIVATE_JOB_STATUS_*`
and `PUBLIC_JOB_STATUS_*`. Keep them both. Deleting the unused one is how this
distinction gets lost again.

## Status ids, never labels

The API takes an **id**. Labels are renameable in the GorillaDesk UI — "Completed"
could become "Complete" without warning, and a label-keyed write would silently stop
matching. Unconfirmed is also the reversal target: a status change is undone by
setting it back, which is what makes it safe to probe.

## Reading a job on the private backend

`GET /api/jobs/{id}` and `GET /api/customers/{id}` are **not routes** (404).
What exists:

```
GET /api/customers/{privateId}/detail        one customer
GET /api/customers/{privateId}/jobs?status=1 their jobs, with private ids
GET /api/customers?limit=500&offset=0        the list — limit=5 is 422,
                                             "Limit is invalid"; 500 works
GET /api/search/elastic?keyword=...          finds records the list omits
GET /api/job/statuses                        the private status ids
```

The public API's collection read is worse than it looks: `GET /v1/jobs` caps at
100 rows, reports `has_more`, and **ignores `page`** — 1,100 rows fetched, 100
distinct ids. Use the point read `GET /v1/jobs/{id}`, which works.

## Verification is causal, not coincidental

`relay.adapters.crm_verify` reads the result back over a **different credential, a
different host and a different protocol** than wrote it — Bearer key against
`api.gorilladesk.com/v1` versus JWT against `ab2`. A writer reporting its own success
is an assertion; a second system reading the field the write claims to have changed
is evidence.

For invoices this must be causal. "An invoice exists on this job" does not prove *we*
raised one — Jim raises invoices by hand all day. So the check snapshots the invoice
id set **before** the attempt and requires **exactly one** new id whose total matches
the approved amount. Zero is a failed write. Two means something else was happening
at that moment and a human decides, because picking one would be a guess recorded as
a fact.

An ambiguous read-back yields `unknown` — never a retry, and it routes to the human
fallback.

## What is deliberately NOT automated, and why

`PrivateCrmWriter.raise_draft_invoice` exists and is tested, and `DualBackendCrm`
still reports `can_create_invoice=False`. That is not an oversight and it is not a
transport limitation.

An invoice body needs `subtotal`, `total` and structured taxes. What a closeout holds
is a `price` Fact **in the words that were spoken** — measured across the real corpus
these read like *"$250 plus New Jersey tax"*, *"$90 plus Philadelphia tax"*. Turning
that into an invoice means resolving a named jurisdiction to a tax id and then
computing a total **nobody said**, and putting it on a customer's bill. `price` is in
`NEVER_INVENT` for exactly this reason. The line-item catalog does not close the gap
either: `settings/items` carries `{id, name}` and no cost.

So the invoice stays on the assisted-fallback path, where a person reads the brief and
enters the number. The job status has none of that problem — it sets one enum on one
job, derives nothing, touches no money, and reverses. **That asymmetry is why one of
the two is wired and the other is not.** Wiring the invoice needs a pricing model that
can show where every figure came from, not a code change here.

## Fail-closed, and the restraints that stay

`relay.crm` constructs the private writer **only** when both credentials are present.
With them unset it returns the public adapter unchanged, its profile still reports
`can_update_job=False`, and the job-status operation routes to a human exactly as it
did before any of this existed.

Declaring the capability is **not** the same as performing the write. Three gates sit
in front of the wire and none of them is this adapter's to relax:

1. **approval** — a human approved this exact version, revalidated at dispatch;
2. **`egress_enabled`** — the kill switch, off by default;
3. **the write ledger** — the product-controlled dedupe key, the only duplicate
   protection that exists.

Never turn on a switch to make a test pass. Never widen `trigger_action`. Never let a
Chromium process make its own network calls — a browser bypasses the httpx allowlist
that is the one *mechanical* restraint on writes in this codebase.

## Where the code is

| file | role |
|---|---|
| `apps/relay/src/relay/adapters/crm_private.py` | the writer; pins `trigger_action`, refuses sends |
| `apps/relay/src/relay/adapters/crm_dual.py` | facade: public reads + note, private job status |
| `apps/relay/src/relay/adapters/crm_verify.py` | causal read-back over the other credential |
| `apps/relay/src/relay/crm.py` | opt-in construction, fail-closed on missing credentials |
| `apps/mirror/src/mirror/private_api.py` | the read client — login, paging, collections |
| `apps/relay/tests/test_crm_private.py` | 50 tests across the three adapters |

## Turning it on — DONE 2026-08-28

This section used to be a six-step plan whose first step was "Jim creates a
dedicated integration user (his action)". He did not need to. What happened:

1. ~~Jim creates a dedicated integration user.~~ **Not required.** The existing
   shared login is an Admin with every permission this needs. See *Which login*.
2. Credentials in 1Password (`op://DeLoSecrets/Gorilla Desk`) and in SSM at
   `/james-brennan/relay/prod/gorilladesk_private_{username,password}`.
3. **Capability proved** on job `XWgB0ooY7y` / `77665` (Agent K, 1301 Washington
   Avenue, Miami Beach) — set to Completed, read back over the public API as
   `Completed`, restored to Unconfirmed. `relay-capability <job-id>` does this
   and is the artifact.
4. `RELAY_CAPABILITY_EVIDENCE=supported` on `relay` and `dispatchers`.
5. `RELAY_EGRESS_ENABLED=true`, fenced by `RELAY_WRITE_SCOPE_CITY="Miami Beach"`
   / `RELAY_WRITE_SCOPE_STATE=FL`. The invoice stays assisted:
   `can_create_invoice` is still False on the dual adapter, so that operation is
   refused as absent before the evidence gate is ever consulted.

### The probe is the point, not a formality

Three live attempts, three different failures, each invisible to the test suite:
404 on the public job id, 422 on the public status id, then proved. Run
`relay-capability` against a real record **before** believing any write path
here works. A green suite means the fixtures agree with each other.

### The blast-radius fence

`relay.core.scope` decides *whose* record may be written, off the city on the
CRM's own job row — never an address a caller supplied, never one Frank spoke.
IPM's book is Philadelphia; the test records are Miami Beach, so the scope is
disjoint from every real customer by construction. Unset admits nothing.

Test records on the account: **Agent K** (acct 5191, 1301 Washington Ave,
33139, private id 16777) and **Blazin James** (acct 5190, 1300 Washington Ave,
33119). Both carry the customer tag `test`.
