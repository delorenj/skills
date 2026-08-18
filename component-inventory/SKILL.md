---
name: component-inventory
description: Keep a per-repo CSV ledger of every billable and load-bearing component across every provider, refreshed against live provider APIs, reconciled line-by-line against the actual bill, and audited for the components nobody is watching. Use when asked to inventory infrastructure, find or explain cloud cost, work out what a project actually costs per month, reconcile a bill against what is deployed, add a newly provisioned component to the record, refresh a stale inventory, find forgotten or duplicated resources, check a free-tier window, or decide what can be torn down. Triggers - component inventory, service inventory, what does this cost, monthly cost, cloud spend, AWS bill, cost reconciliation, unused resources, forgotten resources, free tier expiry, teardown plan, what is still running, rollback-only resource. Do NOT use for provisioning, deleting or modifying infrastructure (this skill is read-only against every provider), for application performance, or for BMAD planning artifacts.
pipeline-status: new
---

# component-inventory

A ledger that **notices**. One CSV per repo, one row per billable or
load-bearing component, refreshed from live provider APIs rather than from
memory, and audited on every run for the failure this skill exists to prevent:

> A component that costs money, that nobody has decided about, whose figure was
> assumed rather than measured.

That is not hypothetical. In the `james-brennan` repo an Aurora Serverless v2
cluster was reported at "about $0/month" from its *configured* auto-pause while
the *measured* floor was **$43.80/month**, and after its replacement went live
it kept running beside it with nothing in the system saying so.

## Read-only, always

Every command here issues `describe` / `list` / `get` calls and nothing else. It
never creates, modifies or deletes a provider resource, and it never writes a
credential to a file, a log, or its own output. Credentials are resolved from
1Password per invocation and live in one process's memory.

## The invariants

1. **Every figure names where it came from.** `cost_basis` says what kind of
   figure it is; `cost_source` says which API call or bill line produced it;
   `billing_key` names the provider's own usage-type string so a machine can
   check it. A number with no source is the bug.
2. **Every zero is a decided zero.** `free-tier` and `included-in-plan` name the
   allowance. A zero on an `estimated` basis, or with no source at all, alarms.
3. **Every cheap number carries its ceiling.** `monthly_usd_max` is what the row
   costs when the condition holding it down stops holding. A paused Aurora
   cluster reads $0.00 and $43.80 in the same row, and both are true.
4. **Every row says who pays.** `owner` separates ours from the client's from
   the operator's pre-existing tooling. Only `owner=automaticai` rows sum into
   the project total, so nobody can quote the organization's bill as the
   engagement's cost.
5. **Every row says how it ends.** `teardown` plus `teardown_risk`
   (`safe` / `destructive` / `blocked`) plus `depends_on` for ordering.
6. **Every row says when to look again.** `last_verified` is when a machine last
   confirmed it; `review_by` is when a human must re-decide it. A row past its
   `review_by` alarms.
7. **A refresh never makes a row say less.** Machine writes fill blanks and
   sharpen figures; they do not overwrite hand-written provenance with a shorter
   machine string.

## Commands

```bash
INV=~/.claude/skills/component-inventory/scripts/inventory.py
CSV=devops/inventory/components.csv
```

| command | what it does |
|---|---|
| `python3 $INV --csv $CSV list [--provider P] [--owner O] [--status S]` | print the ledger and the running total |
| `python3 $INV --csv $CSV add --component-id ID --provider P ...` | add or replace one row (every column is a flag) |
| `python3 $INV --csv $CSV set --id ID --field col=value` | change named fields, restamping `last_verified` |
| `python3 $INV --csv $CSV verify --provider all ...` | re-read live APIs, refresh figures, stamp verification, report undeclared live resources |
| `python3 $INV --csv $CSV reconcile --start D --end D ...` | attribute every line of the actual bill to a row, both directions |
| `python3 $INV --csv $CSV audit` | findings; exits non-zero when anything alarms |

### verify

```bash
python3 $INV --csv $CSV verify --provider all \
  --aws-profile <profile-that-can-assume> \
  --aws-assume-role-arn arn:aws:iam::<account>:role/OrganizationAccountAccessRole
```

Per provider it re-reads what is actually there, refreshes what is directly
measurable (RDS class through the Pricing API, Aurora ACU through CloudWatch,
ECR bytes, S3 objects, KMS key manager, Cloudflare subscription price, Twilio
usage records), and stamps `last_verified` / `verified_by`.

Its most important output is the last line: **every live resource it finds that
is named nowhere in the ledger.** That sweep is what would have caught a second
database running beside the first.

`--provider aws | cloudflare | twilio | all`. Cloudflare and Twilio credentials
come from 1Password; AWS from a profile or an assumed role. A provider that
cannot be reached leaves its rows exactly as they were and says so.

### reconcile

```bash
python3 $INV --csv $CSV reconcile --start 2026-08-01 --end 2026-08-19 \
  --aws-profile <profile> --aws-account <linked-account-id>
```

Checks both directions, and both matter:

- every usage type on the bill maps to the row that claims it, with the
  unattributed remainder printed as a number rather than a shrug;
- every `billing_key` the ledger declares that the provider has **not** charged
  for, which is how a forward run-rate with no bill behind it gets caught.

Run it from the payer when the target is a member account: the payer's
linked-account view refreshes sooner and settles to the cent.

### audit

Findings at two levels. `ALARM` exits non-zero, so this belongs in CI or a
weekly job. It checks: retired components that can still bill, zeros with no
source behind them, `measured` figures with no bill line to point at, cheap
figures with an expensive ceiling, missing provenance or teardown, verification
older than `--stale-days` (default 14), passed `review_by` dates, unowned costs,
and two live rows doing the same job.

## Starting a ledger in a new repo

1. `mkdir -p devops/inventory`
2. Sweep the providers first (`verify` against an empty ledger reports
   everything as undeclared — that list *is* the work-list).
3. `add` one row per component, in provider order.
4. `verify --provider all`, then `reconcile`, then `audit` until the only
   findings left are ones a human genuinely has to decide.
5. Commit the CSV. It is diffable on purpose: a cost change should show up in
   `git log`, attributable to a commit and a ticket.

Column semantics and the closed vocabularies are in
[references/columns.md](references/columns.md).

## What this skill will not do

- Provision, modify or delete anything. Teardown commands are **recorded, never
  executed** — the ledger raises the question and the operator answers it.
- Invent a figure. A cost that belongs to somebody else's contract is left empty
  with `cost_basis=client-billed` rather than guessed from a public price list.
- Treat a shared subscription as a project cost. A plan that predates the work
  and serves other projects is `owner=shared-operator-tooling` and stays out of
  the total, with the sharing named in the row.
