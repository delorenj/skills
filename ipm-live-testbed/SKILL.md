---
name: ipm-live-testbed
description: "Create and remove test records on Integrity Pest Management's LIVE GorillaDesk account so Workflow 1 can be exercised end to end without being able to touch a real customer. Covers the geographic write fence, the board format (a whole day of jobs as one committed JSON file), the scenarios, the approver credential, and the exact commands. Use when asked to make test users or test jobs, to stage an acceptance run, to build an edge case (twins, no house number, back-to-back), to clean the account up, or when a closeout has nothing to match against. Triggers - test users, Miami Beach, testbed, job set, board, relay-testbed, stage a call, create a test job, clean up test data, write scope, blast radius. Do NOT use to write CLOSEOUTS (that is the relay itself) or to change job status (that is gorilladesk-private-api)."
---

# The IPM live testbed

Test records on a **client's production CRM**. Everything below assumes that and
is shaped by it.

## The one idea

IPM's book is **Philadelphia** — 227 real jobs. The write scope is **Miami
Beach**. So every record this tool can create or destroy is disjoint from every
real customer *by construction*, not because anybody remembered to be careful.

```
RELAY_WRITE_SCOPE_CITY="Miami Beach"
RELAY_WRITE_SCOPE_STATE="FL"
```

Unset admits nothing. The comparison is exact on a canonical form and never a
prefix — `Miami` does not admit `Miami Beach`, which is the difference between
"the test records" and "a real customer in Miamisburg, Ohio".

**If IPM ever takes work in the scope city, change the scope city first.**

## Setup, every time

```bash
cd ~/code/james-brennan/apps/relay
export AWS_PROFILE=brennan
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN   # stale .env creds shadow SSO
export RELAY_GORILLADESK_API_KEY=$(aws ssm get-parameter --region us-east-1 \
  --name /james-brennan/relay/prod/gorilladesk_api_key --with-decryption \
  --query 'Parameter.Value' --output text)
export RELAY_GORILLADESK_PRIVATE_USERNAME=$(op read "op://DeLoSecrets/Gorilla Desk/username")
export RELAY_GORILLADESK_PRIVATE_PASSWORD=$(op read "op://DeLoSecrets/Gorilla Desk/password")
export RELAY_WRITE_SCOPE_CITY="Miami Beach" RELAY_WRITE_SCOPE_STATE="FL"
```

Both credentials are needed: customers are created on the **public** API, jobs
only exist on the **private** one (`POST /v1/jobs` is 404).

## Commands

```bash
.venv/bin/python -m relay.testbed boards        # what boards exist, and why each job is on them
.venv/bin/python -m relay.testbed load day-one  # a whole day on the account, ~10s
.venv/bin/python -m relay.testbed load day-one --date 2026-09-02
.venv/bin/python -m relay.testbed make twins    # one shape, no file
.venv/bin/python -m relay.testbed list          # every job the fence admits
.venv/bin/python -m relay.testbed clean --yes   # jobs off; CUSTOMERS ARE KEPT
```

`clean` removes **jobs and never customers**: a customer carries the account
number the corpus and mirror already reference, and a job is the thing that
accumulates. Jobs are ephemeral by design.

## Boards — a day of work as one file

`~/code/james-brennan/boards/*.json`. This is the thing to reach for when asked
for "a different board" or "another job set".

```json
{
  "name": "day-two",
  "why": "One sentence on what this day is FOR. Required.",
  "city": "Miami Beach", "state": "FL", "zip": "33139",
  "jobs": [
    { "customer": "Ana Reyes", "address": "1450 Washington Avenue", "at": "08:00",
      "why": "Required. What this job proves." }
  ]
}
```

- Two jobs naming the **same customer** share one customer record. That is how a
  board says "back to back" without a second concept.
- `at` is `HH:MM`; the day comes from `--date` (default today).
- Optional per job: `minutes` (default 60), `service_id`.
- **`why` is mandatory on the board and on every job.** A test record whose
  purpose nobody wrote down becomes a record nobody dares delete — this account
  already had two of those. A test asserts every committed board has them.

A board is committed because **an acceptance result is meaningless without the
board it was measured on.** Fork rather than edit `day-one` if a run needs
something different.

### `day-one`, the standing board

Seven stops, every hard case exactly once: a clean match at 08:00; twins two
doors apart at 10:00 (unresolvable by address *or* clock — must terminate in a
person); two numberless Collins Avenue addresses at 12:30 and 14:00 (35% of the
real call corpus has no house number); one customer back-to-back at 15:30 and
16:30.

## Built-in scenarios

For a quick shape with no file: `plain`, `twins`, `same-street`,
`no-house-number`, `back-to-back`. `--at`, `--date`, `--street`,
`--from-number`. A scenario compiles to a board — one execution path, not two.

## Three vendor behaviours that will waste your afternoon

1. **`POST /api/jobs` ignores a `time` field.** `{"date": "2026-08-29", "time":
   "10:00 AM"}` returns **200** and creates a job at **midnight**. The hour goes
   inside the date string: `{"date": "2026-08-29 10:00:00"}`.
2. **`POST /v1/customers` returns `{"id": ...}` and nothing else.** The private
   customer id is in `profile_url`, which is only on the **GET**. Read it back.
3. **The vendor drops `tags`.** The `test` tag is sent and does not stick.
   Nothing depends on it — the fence reads the city off the CRM.

And the one that cost three live attempts: **the two backends do not share an id
space.** See the `gorilladesk-private-api` skill.

## Approving a test closeout

A closeout writes because a **named principal** granted it. For testing:

```
name        automaticai
1Password   op://DeLoSecrets/IPM Surface approver - automaticai
cohort      RELAY_APPROVERS=jim,automaticai
```

Named `automaticai` and **not** `jim` deliberately: the approver's name lands on
the record and travels into the audit trail, so an approval we made must never
look like one Jim made.

Minting another: `python -m relay.auth mint <name>` prints
`name:rounds:salt:hash` — a *verifier*. **Put the passcode in 1Password and
verify it landed BEFORE appending the verifier to SSM
(`/james-brennan/relay/prod/approver_credentials`).** A verifier whose passcode
was lost between those steps is a credential nobody can sign in with, and it
looks completely healthy.

## Before believing any of it

```bash
.venv/bin/python -m relay.capability <a-real-philadelphia-job-id>
```

It must refuse, naming the city:

> refused: the destination record is in Philadelphia, and this deployment may
> only affect records in Miami Beach, FL. Nothing was sent.

A safeguard nobody has watched refuse something is a safeguard nobody has tested.

## Where the rest is

`~/code/james-brennan/workshop/2026-08-28-the-live-testbed.md` — the full
mechanism, why each layer exists, and how the six gates compose.
