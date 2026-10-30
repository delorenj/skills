---
name: milkshake
description: Run AutomaticAI's billing and finance for any client through Milkshake's `ms` CLI. Use for billing, customer invoices and statements (Yrds), the month close, projected statements and true-ups, pricing, margins, retainers and inference sold at list, vendor costs and manual invoices (bois, boi fetch), shakedown readiness and line items, Mercury transactions, payments and reconciliation, transaction tagging and categories (Jev), the cross-client portfolio, the audit and trend, the Farm client portal and Bloodbank events, and onboarding a new client. Teaches the finance doctrine, plan versus apply, who may run what (agents never issue, settle, deliver or push), the ledger store rules and every refusal's recovery.
---

# Milkshake (`ms`)

Milkshake is AutomaticAI's billing authority. Vendor cost readings (bois) and rules become a
customer statement (a Yrd); Mercury cash becomes tagged cash books. Everything that changes state
is an event on an append-only, hash-chained ledger, written only through `ms` commands. This file
is the entrypoint: the doctrine, the ground rules, who may run what and the command surface. The
detail is one level down.

## The doctrine

- **A utility belt for every client.** Every command takes a client; James Brennan is the dogfood
  client, never a special case. A new client is data (seeds and commands), never code.
- **No dead ends.** Every needs-input item, line-item state and refusal carries the `ms` command
  that moves it on (`command`, `resolution`, `next_command`). Run the resolver's command (a plan
  wherever it reaches outside the ledger); a state with no way out is a bug to report.
- **Bill to make money, inside the contract.** The default is a margin at the pricing policy; a
  client at cost is a recorded decision, never an accident. When a line earns less than policy,
  propose the forward-dated rule that fixes it. The contract guard always wins; only a signed
  instrument (or an operator's recorded decision) changes it.
- **Vendors never appear on the statement face.** A few catalog lines (Telephony, Cloud Hosting,
  Inference, Development Costs, Platform, Usage above plan); vendor detail lives only in the
  evidence pack.
- **Cash is never summed with accrual.** Tags say what happened in the bank; bois and rules
  decide what a client is charged.

All seventeen points (B1-B17) and the vocabulary map (a line item is a boi scope's effective
head; a module is an OldMac): `docs/doctrine.md`. Decisions D1-D24: `docs/decisions.md`.

## Where to go next

| you need | read |
| --- | --- |
| the monthly close for any client, in order, with who runs each step | [references/month-close.md](references/month-close.md) |
| the statement face: line catalog, narrative rules, merging, label guard, adjustment lines | [references/statement-lines.md](references/statement-lines.md) |
| pricing: policy and bands, model choice, margins, retainer, inference as a product, contracts | [references/pricing.md](references/pricing.md) |
| the cash books: sync, autotag, Jev, tags, categories, attribution, push to Mercury | [references/cash-books.md](references/cash-books.md) |
| onboarding a client: seeds, credentials, ordered commands | [references/onboarding.md](references/onboarding.md) |
| what each command appends; the store, read-only mode, backups, the cache | [references/behaviour.md](references/behaviour.md) |
| the audit, its feedback loop and trend (with a replayed walkthrough) | [references/audit-and-trend.md](references/audit-and-trend.md) |
| the Farm snapshot (its Cash and Inference tabs included), Farm-originated commands, Bloodbank events | [references/farm.md](references/farm.md) |
| Mercury card and cash conventions | [references/cards.md](references/cards.md) |
| every command, flag and `--json` shape (generated from the CLI) | [references/commands.md](references/commands.md) |
| every refusal: code, exit, whose move, recovery (generated from `errors.py`) | [references/refusals.md](references/refusals.md) |

`commands.md` and `refusals.md` are generated (`mise run skill:reference`); `tests/skill` fails
when they drift, when a hand-written `ms` line does not parse against the CLI, and when this
file's tables disagree with the code.

## Ground rules

1. **Never touch the ledger's store.** The live ledger is Milkshake's own Postgres (since
   2026-10-27), named by `$MILKSHAKE_HOME/store.json` (default `~/.local/share/milkshake/`); SQLite
   files are tests, backups and exports. Never `psql`, `sqlite3`, Python or `mise run db:*`
   against it, not to "just look", and never edit `store.json`. Read with `ms` queries, change
   with `ms` commands. A hand edit breaks the hash chain and `ms ledger verify` exits 5.
   Experiments run on a copy (`ms ledger backup --to PATH`, then `MILKSHAKE_HOME` at a directory
   holding it as `ledger.sqlite3`), never on the real ledger.
2. **Run through `mise run ms -- <args>`** so `op run` injects the credentials from
   `.env.vendors.op` (vendor keys, Mercury, Jev, the gateway tokens, the Farm token). Never pass
   a credential as an argument (`SECRET_ON_ARGV`), never write one into a file, never echo one.
3. **Set your own actor** so the ledger shows who acted:
   `export MILKSHAKE_ACTOR=milkshake-pm@agents.automaticai.io`. Without one every write is
   refused (`ACTOR_UNRESOLVED`); never borrow an operator's.
4. **Plan, then apply.** Every command that calls outside the ledger or cannot be undone is a
   plan unless it has `--apply`: it lists what it would do (metered calls marked: AWS Cost
   Explorer, about USD 0.01 each) and writes nothing. Show the plan, get an operator's yes, then
   apply only what the matrix below lets you.
5. **Add `--json`** when you parse: one line, `{"ok": true, "data": ...}` or
   `{"ok": false, "error": {"code", "message", "alternative"}}`, plus `next_command` when one `ms`
   command resolves it. UPPER-CASE words in a command are blanks to fill in.
6. **Agents never issue a Yrd.** Issuing is operator-only. `ms yrd issue` is a plan unless it has
   `--apply`: you may run the plan and report what it would freeze and what would refuse it, but
   you never pass `--apply`, never `--accept-incomplete`, never `--force-reissue` and never apply
   a projection (`--projected`). The same holds for settling one (`yrd true-up`), raising the
   Mercury AR invoice (`yrd deliver`, above all `--send-email`), recording a payment
   (`yrd payment`), publishing to the portal (`farm push`) and writing to Mercury (`tx push`):
   you may run their plans; the apply is a human's decision, never a timer's, a cron job's or an
   agent's.
7. **Money is integer cents** (`--amount-cents 35000` is USD 350.00; `--amount` on a manual boi
   is the vendor's decimal total). Unknown is `null` / "no data", never 0. A vendor amount is
   never edited: a correction is a new revision with `ms boi add --manual`.
8. **A refusal is information, not an obstacle.** Exit 3 means nothing was written. Read the
   `alternative`; take the recovery if [refusals.md](references/refusals.md) says it is yours
   (`you`), otherwise report and stop. Never look for an override, never retry in a loop, never
   reach the same effect another way (another number, the store, a second client).

## Exit codes

| code | meaning |
| --- | --- |
| 0 | ok |
| 1 | unexpected: re-run with `MILKSHAKE_LOG_LEVEL=DEBUG` and report the command |
| 2 | usage error (an unknown flag, a missing option): the message names the allowed flags |
| 3 | refused: validation or a guard; nothing was written; the `alternative` says what to do |
| 4 | blocked: a gate (`ms shakedown` found a blocking item and still printed the report); a normal answer while a month is open |
| 5 | integrity, or an outside write whose outcome is unknown: stop and tell an operator |

## Authority: who runs what

Kept equal to `src/milkshake/domain/authority.py` (the audit and the refusal catalogue use the
same lists) by `tests/skill`. "Approval" means an operator said yes to the plan you showed them;
those writes are recorded under your actor, so give honest reasons.

| noun | you, freely (read-only, appends nothing) | you, with an operator's approval | operator only, never an agent |
| --- | --- | --- | --- |
| client | `client show`, `client list` | - | `client register`, `client set` (contract terms, inference pricing, Mercury identity, tax) |
| vendor | `vendor list`, `vendor check` | - | `vendor register`, `vendor retire` |
| issuer | `issuer show` | - | `issuer set` |
| squeeze | `squeeze` (the plan) | `squeeze --apply` (calls vendors, writes bois) | - |
| boi | `boi list`, `boi show`, `boi fetch` (the plan) | `boi add --manual`, `boi fetch --apply` (drives the operator's browser), `boi review` | - |
| item | `item list`, `item show`, `item resolve` (the plan) | `item resolve --apply` (squeezes one row) | - |
| rule | `rule list` | `rule add` (every kind, and `--from-file`), `rule revoke` | - |
| adjust | - | `adjust item` | - |
| pricing | `pricing policy show`, `pricing simulate`, `pricing suggest` | `pricing policy set` | - |
| yrd | `yrd build`, `yrd show`, `yrd list`, `yrd verify`, `yrd render`, `yrd evidence` | - | `yrd issue --apply` (and `--projected`, `--accept-incomplete`, `--force-reissue`, `--supersedes`), `yrd true-up --apply`, `yrd deliver --apply` (and `--send-email`), `yrd payment --apply` |
| invoice | `invoice create` | - | - |
| shakedown | `shakedown` | - | - |
| tui | `tui --json` | - | - |
| import | - | - | `import legacy --apply` |
| parity | `parity` | - | - |
| reconcile | `reconcile` (reads Mercury) | - | - |
| tx | `tx list`, and the plans of `tx sync`, `tx autotag`, `tx categorize` | `tx sync --apply`, `tx tag`, `tx autotag --apply`, `tx categorize --apply` (asks Jev) | `tx push --apply` (writes Mercury) |
| category | `category list`, `category propose` (the plan) | `category propose --apply` (asks the gateway) | `category accept`, `category reject`, `category retire`, `category add` |
| trend | `trend` | - | - |
| portfolio | `portfolio` | - | - |
| audit | `audit` (deterministic) | `audit feedback`, `audit --record`, `audit --llm` | - |
| farm | `farm export`, `farm invoicer list` | - | `farm push --apply`, `farm invoicer add`, `farm invoicer revoke` |
| ledger | `ledger verify`, `ledger log`, `ledger backup`, `ledger export` | - | `ledger publish --apply`, `ledger migrate --apply`, `ledger reproject` (the rebuild) |

The plans of operator commands only read, so you may run them to report what an operator would
do: `yrd issue`, `yrd true-up`, `yrd deliver` and `yrd payment` (these two read Mercury, GET
only), `farm push`, `tx push`, `import legacy`, `ledger publish`, `ledger migrate` and
`ledger reproject --check`. The commands with no plan (`client register|set`, `vendor register|retire`,
`issuer set`, `category accept|reject|retire|add`, the invoicer grants) are never yours, in any
form. An audit never proposes an operator command.

## The command surface

The closed noun and verb set; `tests/skill` fails when this table and the CLI disagree. Flags and
`--json` shapes: [commands.md](references/commands.md); what each appends:
[behaviour.md](references/behaviour.md).

| noun | verbs | notes |
| --- | --- | --- |
| `client` | `register`, `set` (write); `show`, `list` | the contract guard (`--pass-through-markup forbidden` needs `--contract-clause`), dated flips, `--inference-pricing product`, the Mercury identity, the tax treatment |
| `vendor` | `register` (also `--from-file SEED`), `retire` (write); `list`, `check` | a vendor row is ledger state; `check` says whether each api row's credential is `ready`, `missing` or `invalid` (names only) |
| `issuer` | `set` (write); `show` | AAI's letterhead; `show` lists what is missing |
| `squeeze` | (no verb) | reads the client's api vendors for a period; a plan unless `--apply`; cached reads are `cached` |
| `boi` | `add --manual`, `fetch`, `review` (write); `list`, `show` | a manual boi needs `--reference` and evidence; `fetch` reads an API-less vendor's invoice (Cartesia) through Kapture, a plan unless `--apply` |
| `item` | `list`, `show` (queries); `resolve` (a plan; `--apply` writes) | the cost lines of a client-month with their state and `resolution`; `--project monthly` adds a run-rate estimate; `resolve` squeezes one row |
| `rule` | `add <kind>` (also `--from-file SEED`), `revoke` (write); `list` | kinds `bill_to`, `split`, `margin`, `service_fee`, `discount`, `narrative`, `retainer`; `--timing forward --effective-from DATE` never reaches back |
| `pricing` | `policy show`, `simulate`, `suggest` (queries); `policy set` (write) | the doctrine's markups, bands and sources; simulate prices models over real months; suggest prints forward-dated rules and runs none ([pricing.md](references/pricing.md)) |
| `adjust` | `item` (write) | a one-off rule bound to one boi; recomputes totals; never a vendor amount |
| `yrd` | `build`, `render`, `show`, `list`, `verify`, `evidence` (queries); `issue`, `true-up`, `deliver`, `payment` (plans; `--apply` is an operator's) | `issue --projected` bills an open month at its run-rate and `true-up` settles it after the close; `--supersedes NUMBER` issues the next `-vN`; `deliver` raises the Mercury AR sidecar (`DontSend` unless `--send-email`); `payment` reads Mercury cash |
| `invoice` | `create` | alias of `yrd render --view customer` (identical bytes) |
| `shakedown` | (no verb) | the readiness report, every item with its command; exit 4 when anything blocks |
| `tui` | (no verb) | the operators' dial board; you read it with `--json` only |
| `import` | `legacy` (write, plan by default) | the portal's history as `import` bois: history only, never billed |
| `parity` | (no verb) | imported legacy heads versus Milkshake's per scope; exit 4 when any scope differs |
| `reconcile` | (no verb) | Mercury cash versus accrued bois per vendor; read-only; never sums them |
| `tx` | `sync`, `autotag`, `categorize`, `push` (plans; `--apply` writes); `tag` (write); `list` | the cash books ([cash-books.md](references/cash-books.md)); `list --untagged` gives each transaction its `ms tx tag` command; only `push --apply` writes to Mercury |
| `category` | `list` (query); `propose` (a plan; `--apply` asks the gateway); `accept`, `reject`, `retire`, `add` (write, operator only) | the categories Jev and a manual tag choose from; only `accept` or `add` creates one |
| `trend` | (no verb) | month-over-month client-borne and AAI-borne cents per category; unknown is `-`, never 0 |
| `portfolio` | (no verb) | every client for a month: billed, client-borne and AAI-borne cost, margin, fees, kept, unpaid; totals per currency |
| `audit` | (no verb: a read-only review); `feedback` (write) | findings with evidence and proposed commands it never runs; `--llm` adds a gateway model pass |
| `farm` | `export`; `push` (a plan; `--apply` is an operator's); `invoicer add`, `invoicer revoke` (write, operator only), `invoicer list` | the `milkshake/v1` snapshot for the client portal ([farm.md](references/farm.md)) |
| `ledger` | `verify`, `backup`, `log`, `publish`, `export`, `migrate`, `reproject` | `verify` exits 5 on any mismatch; `export` writes a verified SQLite copy; `migrate` copies between engines (plan; `--apply` operator); `reproject --check` compares the Postgres projections with the fold |

## The month, in one breath

The full cadence, step by step with who runs each line: [month-close.md](references/month-close.md).

1. `ms ledger verify`, then `ms shakedown --client $CLIENT --period YYYY-MM`.
2. `ms squeeze --client $CLIENT --period YYYY-MM` (a plan; `--apply` with approval), again after
   the close so every client-borne reading is an actual.
3. API-less vendors: `ms boi fetch --client $CLIENT --vendor cartesia --period YYYY-MM` (a plan),
   or the prefilled `ms boi add --manual` the shakedown prints.
4. Work every needs-input item through its command; `ms item list --client $CLIENT --period YYYY-MM`
   shows each cost line's state and way out. While the month is open, `ms shakedown` always exits
   4: wait for the close (one hour after the period ends, UTC), do not "fix" it early.
5. `ms yrd build --client $CLIENT --period YYYY-MM`, `ms invoice create --client $CLIENT --period YYYY-MM`,
   `ms trend --client $CLIENT --months 3 --to YYYY-MM`, `ms audit --client $CLIENT --period YYYY-MM`.
6. Post the draft, the open items and the findings for the operators. An operator issues (or, for
   a month issued `--projected`, settles it with `yrd true-up`), delivers, records the payment,
   pushes to the Farm and backs up. You verify (`ms yrd verify NUMBER`) and report.

## Issuing, projections and true-ups (operator only)

Issuing freezes a statement: one `yrd.issued` with the lines, the boi and rule ids, the issuer
snapshot and `content_sha256`. The gate (Q15): a complete issuer, a closed period, no blocking
item, no overlapping active statement, a new number. `--accept-incomplete` is an operator's
override for an immaterial residual only (at most the smaller of USD 1.00 or 1% of the total). A
correction after issue is a superseding `-vN`, never an edit.

A client who needs the month before it closes gets a **projected** statement
(`--projected --reason`): final readings as read, the rest at their monthly run-rate, one plain
note and no vendor on the face. After the close, once every reading is final, `ms shakedown`
raises `projected_unsettled` and an operator settles it with `yrd true-up` (actual minus
projected per label: adjustment lines on the next statement, or a `NUMBER-TU` one-off); later
drift is `settlement_drift`, settled the same way. You may run every one of these plans and
report; you never apply one. Step by step: [month-close.md](references/month-close.md), steps
5 and 6; runbook `docs/runbooks/issue-a-statement.md`.

Delivery is silent by default: `ms yrd deliver NUMBER --rail mercury` is the plan (it reads
Mercury); with `--apply` an operator raises the Mercury AR sidecar with the same number and
`DontSend`, so the client receives only the Milkshake statement. `--send-email` (Mercury emails
the client) is a human's deliberate act, never a timer's, a cron job's or an agent's.

## Farm and Bloodbank

- **Farm push is plan-by-default.** `ms farm push --client $CLIENT --period YYYY-MM` makes no
  network call and appends nothing: the endpoint, the periods, the payload hash and the diff
  against the last push. `--apply` publishes numbers to the client portal: an operator's, through
  `mise run ms --`. `ms farm export --client $CLIENT --period YYYY-MM --out out/` writes the same
  snapshot to a file; it carries each needs-input item's command and each line's state.
- **Farm-originated commands exist, and they are policy-gated.** The Farm's Create Invoice button
  and its command palette (Story 10.3: `squeeze`, `boi review`, `rule revoke`, `yrd payment`,
  `farm push`) send signed commands that the `milkshake-farm-consumer` service runs: Create
  Invoice through the same `yrd issue`, the palette by running the exact `ms` command in a
  subprocess under the actor `farm:<email>/<command_id>`. It is not you. The palette runs
  allow-listed commands under **per-client grants**: the ledger's own grants
  (`ms farm invoicer list`) say who may ask, for which client, which command and whether each is
  plan-only; you never grant (`farm invoicer add|revoke` is an operator's), and you never re-run
  or re-ask a Farm command by hand to retry it (an apply that committed is recorded `applied`
  even if the process then failed, and a metered `squeeze --apply` pays each time). The outcome is
  a `farm.command.handled` or `farm.command.ran` event; read it with `ms ledger log`.
- **Bloodbank announces ledger changes.** The `milkshake-outbox` service publishes a CloudEvent
  after a command commits, plus a `billing.line_item.updated` for each customer line it moved
  (label and cents, never a vendor). You do nothing to make it happen, and a bus outage never
  fails a command.

Everything about the snapshot, the allow-list and the events: [farm.md](references/farm.md).

## Audit, feedback and trend

- `ms trend --client $CLIENT --months 3 --to YYYY-MM` is read-only: per category and month, the
  client-borne and AAI-borne cents apart, with deltas; an unknown month is `-`, never zero.
- `ms audit --client $CLIENT --period YYYY-MM` is a second pair of eyes: findings with a stable id,
  evidence, a rationale and proposed `ms` commands.
  **Proposals are not commands to run blindly.** The audit runs none of them (`executed: false`)
  and never changes billing state; rule changes, adjustments and boi entries are operator
  decisions. Two findings argue AAI's side: `margin_below_policy` and `allowance_mis_sized`
  ([pricing.md](references/pricing.md)).
- `ms audit feedback --finding F-XXXXXXXX --decision accept --reason "REASON" --client $CLIENT --period YYYY-MM`
  records the operator's verdict (one `audit.feedback` under your actor). Accepting runs nothing;
  rejecting suppresses the finding next time.

Every check, the model pass and a replayed walkthrough: [audit-and-trend.md](references/audit-and-trend.md).

## The TUI

`ms tui` is the operators' interactive dial board. **You have no terminal, so you never run it**
(`TUI_NEEDS_TERMINAL`); read what it would draw as data with
`ms tui --client $CLIENT --period YYYY-MM --json` (read-only, works in read-only mode).

## The store, read-only mode, backups

- **Read-only mode.** `MILKSHAKE_READONLY=1` opens the ledger read-only; every write, and the
  plans that open the ledger for writing (`squeeze`, `item resolve`, `yrd issue`, `yrd true-up`,
  `boi fetch`, `import legacy`, `ledger publish`), are refused `LEDGER_READONLY`, while every query works. Unset the variable to leave it (empty is
  `SETTINGS_INVALID`).
- **Backups.** An operator runs `mise run ledger:backup` after every issue and every
  `farm push --apply`; the nightly timer covers the rest. You may make a verified copy with
  `ms ledger backup --to PATH` (a new path outside any git work tree). Restoring is an
  operator's decision.
- **The store.** `ms ledger export --to PATH` (a verified SQLite copy) and
  `ms ledger reproject --check` (the Postgres projections against the fold) only read; migrating
  and rebuilding are an operator's. The read cache (Milkshake's own Redis, six hours) never feeds
  a statement.
- **Installation.** If `ms --help` lacks a command this skill names, the `uv tool` install is
  stale: tell an operator to run `mise run tool:install`.

Detail: [behaviour.md](references/behaviour.md), "The ledger".

## The commonest refusals

Every typed refusal, with its exit code, whose move it is and its recovery, is in
[refusals.md](references/refusals.md); look a code up there when it is not below.

| code | meaning | recovery |
| --- | --- | --- |
| `GUARD_MARKUP_FORBIDDEN` | The client's contract forbids markup on pass-through cost; the message names the clause. | Do not retry the margin. Label the cost neutrally (`ms rule add narrative`) and propose the contract change to an operator ([pricing.md](references/pricing.md)). |
| `CONTRACT_REF_REQUIRED` | A fee, retainer or inference product for a client that forbids markup names no signed instrument. | Ask an operator for the signed clause; with none, record nothing. |
| `ADJUST_AMOUNT_FORBIDDEN` | `adjust item` was given a vendor amount; vendor amounts are immutable. | Record a new revision with `ms boi add --manual`; `adjust item` changes only who bears a cost or the markup. |
| `EVIDENCE_REQUIRED` | A manual boi has no source. | Attach `--evidence-file PATH` or `--excerpt "..."` (not both), plus `--reference`. Never invent evidence. |
| `REASON_REQUIRED` | A fee, a revoke, a tag or a category change has no `--reason`. | Add an honest `--reason`; it is recorded with your actor. |
| `NARRATIVE_LABEL_LEAKS_VENDOR` | A customer label names a registered vendor or reader. | Use a catalog label ([statement-lines.md](references/statement-lines.md)). |
| `CLIENT_UNKNOWN` | No client has that slug. | `ms client list`; registering a client is an operator's. |
| `BOI_ID_AMBIGUOUS` | The boi id prefix matches several bois (8 hex characters at least). | Give more characters; `ms boi list --client $CLIENT --period YYYY-MM --json` prints ids. |
| `BOI_IS_HISTORY` | `adjust item` named an imported legacy reading, which is never billed. | Leave it, or record the vendor's figure with `ms boi add --manual`; it is a question for an operator. |
| `ROW_NOT_SQUEEZABLE` | `item resolve` named a row squeeze cannot read (a manual row, a closed month on a current-state reader). | Its `next_command` is the prefilled `ms boi add --manual`. |
| `ISSUE_BLOCKED` | `yrd issue --apply` found a blocking item (exit 4). | Resolve each item through its command (`ms shakedown`); the override is an operator's. |
| `PERIOD_OPEN` | The period has not closed yet (end plus one hour, UTC; exit 4). | Wait for the close, then squeeze again so every reading is an actual. |
| `TRUE_UP_READINGS_PENDING` | A true-up while a client-borne reading is still provisional or missing (exit 4). | Run each reading's command; the true-up is the operator's after that. |
| `CATEGORY_UNKNOWN` | `tx tag` named a category the catalog does not hold. | `ms category list`; a new category is proposed (`ms category propose`) and accepted by an operator. |
| `CREDENTIAL_INVALID` | A command that needs a vendor or Mercury credential found none. | Run it through `mise run ms --`; `ms vendor check --client $CLIENT` names each credential. Never pass one as an argument. |
| `LEDGER_BUSY` | Another `ms` command held the write lock for 30 s; nothing was written. | Wait for it to finish, then retry the same command once. |
| `LEDGER_READONLY` | `MILKSHAKE_READONLY=1` is set; nothing was written. | Use a query, or run the write where the writable ledger lives with the variable unset. |
| `LEDGER_HASH_MISMATCH` | `ms ledger verify` found an event whose hash does not match (exit 5). | Stop writing. Do not repair it. Tell an operator, who restores the latest verified backup. |
| `PROJECTION_DRIFT` | The Postgres projections differ from the fold (exit 5); the ledger itself is intact. | Stop; tell an operator, who rebuilds them with `ledger reproject`. |
| `MERCURY_WRITE_UNCONFIRMED` | A Mercury write may have been applied (exit 5). | Stop. An operator looks in Mercury before anything is retried. |
| `FARM_MODE_FORBIDDEN` | A Farm command asked to apply for a plan-only invoicer (on the event, never a CLI exit). | An operator decides the grant; do not add it and do not retry the command. |
| `BUS_UNAVAILABLE` | Bloodbank did not confirm a publish; the ledger is unaffected. | Tell an operator; the outbox catches up on its own and a re-run is idempotent. |
| `AUDIT_LLM_UNCONFIGURED` | `ms audit --llm` has no audit token. | Run through `mise run ms --`, or drop `--llm`: the deterministic audit needs no model. |
| `AUDIT_FINDING_UNKNOWN` | `audit feedback` named a finding no run holds. | Use the id an audit printed, with the same `--client` and `--period`. |
| `TUI_NEEDS_TERMINAL` | `ms tui` was run without a terminal. | Use `ms tui --client $CLIENT --period YYYY-MM --json` or `ms shakedown`. |
| `ACTOR_UNRESOLVED` | A write has no actor. | `export MILKSHAKE_ACTOR=milkshake-pm@agents.automaticai.io` (your own address). |

## Walking through a refusal (UJ-2)

`tests/skill/test_uj2_replay.py` replays exactly these lines (placeholders in capitals). You are
preparing a month for `$CLIENT`, whose vendor `$VENDOR` is pass-through, and you try a margin:

```uj2
ms squeeze --client $CLIENT --period $PERIOD
ms rule add margin --client $CLIENT --vendor $VENDOR --bps 500
ms rule add narrative --client $CLIENT --category speech --label "Speech Services"
ms shakedown --client $CLIENT --period $PERIOD
```

1. The squeeze is a **plan**: no call, no event. You show it and wait for approval.
2. The margin is **refused** (`GUARD_MARKUP_FORBIDDEN`, exit 3) and names the clause.
3. You take the recovery step (a neutral narrative label) and it succeeds.
4. You re-run `ms shakedown`, post the draft summary and the open items for the operators, and do
   not issue.
