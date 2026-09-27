---
name: gorilladesk-private-api
description: Operate GorillaDesk job notes, job completion, invoice creation and invoice email through the private backend, with destination fences and causal read-back.
---

# GorillaDesk private API

Read `../project-invariants/SKILL.md` first. The current operator contract is:
approval files the note **on the bound job**, completes that job, and issues and
emails the invoice for the approved amount and billing destination. A draft
alone does not complete approval. Older draft-only restrictions are superseded.

## Credentials and transport

Use `relay.crm.open_crm` for product work. Private credentials are SSM references
`/james-brennan/relay/prod/gorilladesk_private_{username,password}`, held in memory.
Never write resolved credentials to files or logs. `PrivateCrmWriter` logs in
with `POST https://ab2.gorilladesk.com/api/auth/login`; the response supplies
`token` and `company.branch.id`. Requests use `token`, `platform: web`, and
`gd-branch-id` headers. A 401 may refresh authentication; an ambiguous write may
not be blindly repeated. A captcha requires a human.

The public API at `api.gorilladesk.com/v1` cannot write job notes, statuses or
invoices. Its note endpoint creates **customer-level** notes, which appear
across visits and do not fulfil a JobCard's bound-job note.

## Identifiers

Public hashids, private job ids, and private event ids are different:

| Identity | Source | Example |
|---|---|---|
| Public job | public `job.id` | `vKY1EVzMYj` |
| Work order / private event | public `work_order_number` | `90029` |
| Private job | private `data.job.id` | `90032` |
| Private customer | tail of public `customer.profile_url` | `16777` |
| Private location | private customer locations, matched to service address | `17367` |

`PrivateCrmWriter.resolve_job_id` accepts an id only when its row's `event.id`
matches the requested work order. Never address a write by work order alone:
it can be another visit's valid job id. Read customer locations from
`GET customers/{privateCustomerId}/locations`; match street, city, state and zip.
Missing or ambiguous identity refuses rather than guessing.

## Actual operations

Verified against the vendor app's current source map on 2026-09-27:

- `POST jobs/{privateJobId}/notes` with JSON `{content, notified_users: [],
  attachments: []}`. Read `jobs/{id}/timeline?fields=top_note&filters=-1&limit=20&offset=0`.
  Confirm the returned note id, approved content and `is_customer_note: 0`.
  A customer timeline or `top_note` does not prove a job attachment.
- `PUT jobs/{id}/status` with `{jobId, status: "2", note: ""}`. Private `2` is
  Completed; public Completed is `74nYKJdMJK`. Read current statuses from
  `GET job/statuses` when checking vendor changes.
- `POST invoices` with the approved `customer_job_id`, `customer_id`, private
  `location_id`, items, subtotal and total. Invoice number and terms come from
  `GET invoices/init`. Writable tax ids come from `taxes?fields=rate`, line
  item ids from `settings/items`. Never replace approved figures at dispatch.
- For an approved send, explicitly call `POST invoice/email/send` after create,
  using `template/invoice/email?invoice_id={id}&type=1`. The body carries
  `invoice_id`, `receiver`, `cc`, `bcc`, `subject`, `message`, `attachments`,
  `request_sig: false`. Creation's `trigger_action: "1"` alone left real
  one-off invoices as unsent drafts.
- Verify through **singular** `GET invoice/{id}`. Require its `job.id`,
  `customer.id`, `location.id`, `total.value` and `invoice_status_id: sent` to
  match. Keep the created invoice id and an unknown receipt when the send or
  read-back cannot be proved; never create a replacement invoice to retry mail.

GorillaDesk renders the billing party from the selected location's billing
contact. For the Miami Beach test cohort, email requests use the named
`ipm-testbed+<customer>@delo.sh` alias. This does not rewrite CRM contacts.

## Authority

Approval binds an immutable snapshot and action digest. Egress, CRM-owned
geography, origin policy and the operation ledger remain required. The tooling
fence is permanently Miami Beach, FL; the product fence is the deployment's
`RELAY_WRITE_SCOPE_CITY` / `_STATE`. Never clear that fence to make a test pass.
Real sends within it are authorized; do not downgrade them to drafts.

`InvoiceWrite.trigger_action` is required: `SILENT="0"` for an explicitly silent
probe, `SEND_EMAIL="1"` for approval. Recurring sends and automatic card charges
are not part of this operation.

## Implementation and verification

- `apps/relay/src/relay/adapters/crm_dual.py`: public identity reads, private writes.
- `apps/relay/src/relay/adapters/crm_private.py`: vendor transport and read-back.
- `apps/relay/src/relay/review/plan.py`: immutable approved action.
- `apps/relay/src/relay/app.py` and `consumer.py`: both note call sites carry job id.
- `apps/relay/tests/test_approved_job_effects.py`: distinct id spaces, job-note
  verification and invoice amount/customer/location mismatches.

A green fixture suite is not vendor proof. Run approval on an approvable fenced
JobCard, read its note from that job's timeline, read Completed status and the
sent invoice's amount, billing party and email activity. Repeating approval
must not create another note or bill.
