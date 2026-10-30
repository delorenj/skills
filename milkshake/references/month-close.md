# Month close: the monthly cadence for any client

Hand-written; checked by `tests/skill` (every `ms` line below parses against the CLI). The same
steps for every client: `$CLIENT` is its slug, `YYYY-MM` the month, `NUMBER` the statement
number (`AAI-YYYY-MM`; `AAI-TAG-YYYY-MM` with `--number-tag`, `-v2` for a supersede, `-TU` for a
one-off true-up). Run every line through `mise run ms -- ...` (dropped below) so `op run`
supplies credentials, with `MILKSHAKE_ACTOR` set to your own address.

**Who** says whose move it is (the authority matrix in [SKILL.md](../SKILL.md)):

- **you**: read-only, or a plan. Run it, read it, report it.
- **you, approved**: it writes the ledger under your actor. Show the plan to an operator, and
  apply only after they say yes.
- **operator**: never an agent. You may run its plan (it only reads) and report what the
  operator would do; you never add `--apply`, `--accept-incomplete`, `--force-reissue` or
  `--send-email`.

A month **closes one hour after its last day ends, UTC** (October closes 2026-11-01 01:00Z).
While it is open every reading is an estimate, a partial or stale, so `ms shakedown` exits 4:
that is the normal answer for an open month, not something to clear early.

## The month at a glance

| when | step | command | who |
| --- | --- | --- | --- |
| any day | 0. chain and credentials | `ms ledger verify`, `ms vendor check --client $CLIENT` | you |
| during the month | 1. read the vendors | `ms squeeze --client $CLIENT --period YYYY-MM` | you (plan), you approved (`--apply`) |
| during the month | 8. cash books | `ms tx sync` | you (plan), you approved (`--apply`) |
| client asks early | 5. projected statement | `ms yrd issue --client $CLIENT --period YYYY-MM --projected --reason "REASON"` | operator (you plan) |
| after the close | 1. squeeze again: actuals | `ms squeeze --client $CLIENT --period YYYY-MM --apply` | you approved |
| after the close | 2. API-less vendors | `ms boi fetch --client $CLIENT --vendor cartesia --period YYYY-MM` | you (plan), you approved (`--apply`) |
| after the close | 3. shakedown to exit 0 | `ms shakedown --client $CLIENT --period YYYY-MM` | you, then whoever each item names |
| after the close | 4. draft, trend, audit | `ms audit --client $CLIENT --period YYYY-MM` | you |
| after the close | 6. true-up or issue | `ms yrd true-up NUMBER --reason "REASON"` or `ms yrd issue --client $CLIENT --period YYYY-MM` | operator (you plan) |
| after the issue | 7. render, deliver silently, payment | `ms yrd render NUMBER --out out/` | you; deliver and payment `--apply` are the operator's |
| after the issue | 9. portal and backup | `ms farm push --client $CLIENT --period YYYY-MM` | operator (you plan) |

## 0. Before you start

1. `ms ledger verify` exits 0 (exit 5 is integrity: stop and tell an operator).
2. `ms vendor check --client $CLIENT`: every api row's credential is `ready` (`missing` or
   `invalid` is an operator's fix in `.env.vendors.op`; names only, never a value).
3. `ms shakedown --client $CLIENT --period YYYY-MM`: what is missing and what blocks.

## 1. Read the vendors (squeeze)

- `ms squeeze --client $CLIENT --period YYYY-MM` is a plan: the calls it would make, metered ones
  marked (AWS Cost Explorer, about USD 0.01 each), rows the read cache already holds marked
  `cached`. It calls nothing and writes nothing. **you**
- `ms squeeze --client $CLIENT --period YYYY-MM --apply` calls the vendors and appends a
  `boi.recorded` per new or changed reading and one `squeeze.completed`. **you, approved**
  Add `--vendor VENDOR` for one vendor, `--refresh` to re-read what the cache or the metered
  window holds.
- One line only: `ms item resolve ROW_KEY --client $CLIENT --period YYYY-MM` plans the squeeze of
  that row (**you**); add `--apply` to read it (**you, approved**). A manual row is
  `ROW_NOT_SQUEEZABLE`, whose `next_command` is the prefilled manual entry.
- Squeeze during the month to keep the close from being a surprise, and **again after the
  close** so every client-borne reading becomes an actual (October: 2026-11-02, again
  2026-11-04 if AWS still reports an estimate). Before the close a squeeze can only record
  another estimate.

## 2. Vendors without an API

Their bill is entered by hand, with the source document as evidence; the ledger never invents a
figure, and a month with no entry is `missing_manual`. Runbook: `docs/runbooks/manual-vendors.md`.

- A vendor with a fetcher (Cartesia today): `ms boi fetch --client $CLIENT --vendor cartesia --period YYYY-MM`
  plans the browser steps (**you**); with `--apply` it drives the operator's signed-in Chrome
  through Kapture, downloads the invoice and records it as a manual boi with the document as
  evidence (**you, approved**; an operator starts Kapture and signs in). It never guesses or
  records a zero: whatever it cannot read is reported with its prefilled manual command.
- Any vendor by hand (**you, approved**, once you hold the real invoice):
  `ms boi add --manual --like VENDOR --client $CLIENT --period YYYY-MM --amount AMOUNT --reference INVOICE_NUMBER --evidence-file INVOICE_FILE`
  (`--excerpt "QUOTE"` instead of a file; `--resource-id RESOURCE` for a vendor with more than one
  row, or `LIKE_AMBIGUOUS`). `--amount` is the vendor's decimal total, never cents.
- Cartesia has two rows: `billing-coverage` (the plan) and `overage` (one row for every overage
  invoice, each a boi on its own monthly period). A manual overage entry is
  `ms boi add --manual --like cartesia --client $CLIENT --resource-id overage --period YYYY-MM --amount AMOUNT --reference INVOICE_NUMBER --evidence-file INVOICE_FILE`.
- A month with no invoice for a row that expects one is a real zero with its reason:
  `ms boi add --manual --like VENDOR --client $CLIENT --resource-id RESOURCE --period YYYY-MM --amount 0.00 --reference NO-INVOICE-YYYY-MM --excerpt "QUOTE"`.
- A shared plan is recorded at the full vendor figure; who bears what share is a rule
  (`ms rule add split` or `ms adjust item`), never a lowered amount. A correction is a new
  revision, never an edit.

## 3. Shakedown and its resolver commands

`ms shakedown --client $CLIENT --period YYYY-MM` is the one definition of what blocks a statement.
It prints every needs-input item with its `command` and its `resolution`, and exits 4 while any
item blocks. `ms item list --client $CLIENT --period YYYY-MM` shows the same month per cost line,
with its state (`new`, `needs_lookup`, `provisional`, `stale`, `conflict`, `final`) and the same
resolution; `ms item show ROW_KEY --client $CLIENT --period YYYY-MM` gives one line in full.

| resolution | what to do |
| --- | --- |
| `run` | run the command. It is a plan wherever it reaches outside the ledger; take an apply to an operator if the matrix says so |
| `wait_until` | the period is still open: after `not_before` (the close), run the command it names |
| `decide` | an operator picks one of `choices`; you present them with the evidence |
| `external` | a person supplies the UPPER-CASE blanks (an invoice, a label, a name), then the command runs |

There is no dead end: an item, state or refusal with no command is a bug to report. The items
you will meet most:

| item | its command | who |
| --- | --- | --- |
| `estimate`, `partial` | wait for the close, then the squeeze (a current-state reader such as Cloudflare: the manual entry) | you, after the close |
| `stale`, `unavailable`, `money_unknown` | the squeeze of that vendor (`--refresh` for stale), or a manual revision when squeeze cannot read it | you, approved |
| `missing_manual` | `ms boi fetch` (Cartesia) or the prefilled `ms boi add --manual` | you, approved |
| `reconciliation_conflict` | `ms boi review --scope SCOPE_KEY --decision keep-manual --reason "REASON"` or `accept-api` | operator decides, you record |
| `unattributed` | a `bill_to` or `split` rule pinned to the vendor or scope | operator decides |
| `paid_by_unknown` | the boi again with `--paid-by aai` or `--paid-by client`: a new revision, same reference and evidence (`ms boi add --manual --like BOI --paid-by aai` plus the original flags). Who paid the vendor decides whether the cost is ever billed, which a `bill_to` rule cannot express | operator decides, you record |
| `unmapped_narrative` | `ms rule add narrative` with a neutral label ([statement-lines.md](statement-lines.md)) | operator picks the label |
| `margin_suppressed_by_guard` | revoke the margin, or the contract change ([pricing.md](pricing.md)) | operator |
| `issuer_incomplete`, `tax_treatment_unconfirmed` | `ms issuer set`, `ms client set $CLIENT --tax-treatment confirmed --tax-confirmed-by NAME` | operator |
| `stale_issued` | a superseding issue, or accept the sent statement | operator |
| `projected_unsettled`, `settlement_drift` | `ms yrd true-up NUMBER` (step 6) | operator |
| `payment_overdue` | `ms yrd payment NUMBER` (step 7) | you (plan), operator (`--apply`) |

## 4. Draft, trend, audit and feedback

- `ms yrd build --client $CLIENT --period YYYY-MM`: the draft lines, total and `inputs_sha256`;
  exits 0 even while items block. Add `--operator` for every boi and its arithmetic (internal:
  it names vendors and margins). **you**
- `ms invoice create --client $CLIENT --period YYYY-MM`: the draft statement as one HTML file, as
  the client would read it. **you**
- `ms trend --client $CLIENT --months 3 --to YYYY-MM`: what moved, per category. **you**
- `ms audit --client $CLIENT --period YYYY-MM`: findings with evidence and proposed commands the
  audit never runs, including `margin_below_policy` and `allowance_mis_sized`. **you**
  Add `--llm` for the gateway model pass (**you, approved**: it archives an `audit.completed`).
- The operator's verdict on a finding:
  `ms audit feedback --finding F-XXXXXXXX --decision accept --reason "REASON" --client $CLIENT --period YYYY-MM`.
  Accepting runs nothing. **you, approved**
- `ms pricing suggest --client $CLIENT`: the forward-dated rules the pricing policy implies
  ([pricing.md](pricing.md)); it runs none. **you**

Post the draft total, the open items with their commands, the findings and the proposals for the
operators. That is where an agent's close ends.

## 5. A projected statement while the month is open (only when the client asks)

A client who needs the month before it closes gets a projection (D23). Operator only.

- `ms yrd issue --client $CLIENT --period YYYY-MM --projected --reason "REASON"` is the plan (you
  may run it): a final reading is billed as read; an estimate, a partial or a stale vendor reading
  at its monthly run-rate (the amount read over the completed UTC days, extended to the month);
  a stale manual invoice as read (an invoice is never scaled); a row with no usable money bills
  nothing now and is listed as left for the true-up with its command. The rules, the margins and
  the guard act on the projected amount exactly as on a reading, and inference sold at list is
  billed at the list of the projected amount.
- `ms yrd issue --client $CLIENT --period YYYY-MM --projected --reason "REASON" --apply` freezes it
  (**operator**). The statement keeps its normal number; the client reads one plain note
  ("Projected for the full month from usage to DATE; any difference is settled on your next
  statement") and no vendor. Refused after the close (`PROJECTED_PERIOD_INVALID`) and with
  `--accept-incomplete`.
- `ms item list --client $CLIENT --period YYYY-MM --project monthly` shows the same run-rate per
  line, recording nothing. **you**
- A mid-month `ms invoice create` draft is internal (estimate lines, no projection note). The
  artifact a client can be sent is the operator-issued projected statement: plan it, never apply
  it, and the operator sends it.
- A fresher projection while the month is still open is a supersede (**operator**):
  `ms yrd issue --client $CLIENT --period YYYY-MM --projected --reason "REASON" --supersedes NUMBER --force-reissue "REASON" --apply`.
- `ms yrd verify NUMBER` replays it with the instant and readings it froze. **you**

## 6. After the close: settle the projection, or issue

Squeeze again (step 1) and enter the manual invoices (step 2) until `ms shakedown` exits 0 on
actuals (`stale_issued` and `tax_treatment_unconfirmed` warn, they do not block).

**A projected month is settled, not issued again.** Shakedown raises `projected_unsettled` with
the command once every client-borne reading is final:

- `ms yrd true-up NUMBER --reason "REASON"`: the plan, actual minus projected per customer label
  (a negative line is a credit). **you** may run it.
- `ms yrd true-up NUMBER --into next --reason "REASON" --apply` records it and carries one
  adjustment line per label into the next statement (**operator**); `--into one-off` issues
  `NUMBER-TU` with only those lines. Until every reading is final it is
  `TRUE_UP_READINGS_PENDING` (exit 4), naming each reading and its command.
- Figures that move after a settlement (a late reading, a retroactive rule) raise
  `settlement_drift`; the same command settles the difference (`NUMBER-TU2` for a one-off).
  Nothing moved is `TRUE_UP_ALREADY_SETTLED`.

**A month that was not projected is issued** (operator only, the Q15 gate: complete letterhead,
closed period, no blocking item, no overlapping active statement, a new number):

- `ms yrd issue --client $CLIENT --period YYYY-MM`: the plan, the number, the total, what would
  be frozen and the refusal `--apply` would hit. **you** may run it and report.
- `ms yrd issue --client $CLIENT --period YYYY-MM --apply` appends `yrd.issued`. **operator**
  `--accept-incomplete --reason "REASON" --approved-by NAME` covers only an immaterial residual
  (at most the smaller of USD 1.00 or 1% of the total) and is the operator's alone.
- `ms yrd verify NUMBER` proves the statement reproduces its `content_sha256`. **you**
- A correction after the issue is the next version, never an edit:
  `ms yrd issue --client $CLIENT --period YYYY-MM --supersedes NUMBER --apply` (**operator**).

## 7. Render, deliver silently, record the payment

- `ms yrd render NUMBER --out out/` writes the issued statement from its frozen HTML;
  `ms yrd render NUMBER --format pdf --out out/` makes the PDF (the `pdf` extra). **you** You never
  send anything to a client: the operator sends the statement.
- `ms yrd evidence NUMBER --out DIR` only when the contract asks for the backing pack; its
  `operator.html` is internal, so never send the whole directory. **you**
- `ms yrd deliver NUMBER --rail mercury` is the plan of the Mercury AR sidecar (it reads Mercury
  and runs the live duplicate-number fence). **you** may run it.
  `ms yrd deliver NUMBER --rail mercury --apply` raises the AR invoice with the same number, one
  line for the total, **`DontSend`**: delivered silently, so the client receives only the
  Milkshake statement (**operator**). `--send-email` lets Mercury email the client: a human's
  deliberate decision, never a timer, a cron job or an agent.
- `ms yrd payment NUMBER` reads Mercury cash (never the AR invoice's status) and says `paid`,
  `partial`, `open` or `overdue`, naming the matching transactions (**you** may run the plan;
  `--cached` reads the last cached Mercury read). `ms yrd payment NUMBER --apply` records a change
  (**operator**). `ms yrd list --client $CLIENT --with-payment` shows every statement's status.

## 8. Cash books for the month

`ms tx sync`, `ms tx autotag --period YYYY-MM`, `ms tx categorize --period YYYY-MM` (Jev),
`ms tx list --period YYYY-MM --untagged` and the `ms tx tag` commands it prints, then
`ms reconcile --client $CLIENT --period YYYY-MM`; an operator pushes the tags with
`ms tx push --period YYYY-MM --apply`. The order, the thresholds and who runs what:
[cash-books.md](cash-books.md). Cash never changes a statement.

## 9. The portal, the portfolio and the backup

- `ms farm push --client $CLIENT --period YYYY-MM` is the plan: no network call, the payload hash
  and the diff against the last push. **you** `--apply` publishes the snapshot to the client
  portal (**operator**). `ms farm export --client $CLIENT --period YYYY-MM --out out/` writes the
  same snapshot to a file. **you** Details: [farm.md](farm.md).
- `ms portfolio --period YYYY-MM`: every client's billed, client-borne and AAI-borne cost,
  margin, fees, kept and unpaid for the month, from each active issued statement or else the
  draft. **you**
- An operator runs `mise run ledger:backup` after every `yrd issue --apply` and every
  `farm push --apply` (the nightly timer covers the rest). You may make a verified copy yourself:
  `ms ledger backup --to PATH` (a new path, outside any git work tree). **you**
