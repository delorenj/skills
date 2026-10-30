# Command behaviour: what each command does to the ledger

Hand-written; the flags and `--json` shapes are generated in [commands.md](commands.md). The
Farm and Bloodbank commands are in [farm.md](farm.md), `audit` and `trend` in
[audit-and-trend.md](audit-and-trend.md), the cash books (`tx`, `category`) in
[cash-books.md](cash-books.md).

## Clients, vendors, rules

- `client register|set`, `vendor register|retire`, `issuer set`: one event per change; an
  identical request appends nothing. `client set` with `--pass-through-markup` or
  `--inference-pricing` is dated (`--effective-from`, default today for `allowed` and for an
  inference change) and never reaches an earlier period ([pricing.md](pricing.md)); with
  `--mercury-customer` / `--revenue-counterparty` it gives the client its own Mercury identity
  ([cash-books.md](cash-books.md)).
- `squeeze`: the plan appends nothing. `--apply` appends `boi.recorded` for each new or changed
  reading and one `squeeze.completed`. A reader that fails produces an `unavailable` boi with the
  error class as the reason, never zero dollars. A non-metered read the cache holds is reported
  `cached` and calls nothing; `--refresh` reads again.
- `boi add --manual`: one `boi.recorded` plus its evidence blob. Needs `--reference` and either
  `--excerpt` or `--evidence-file`. `--like VENDOR` (or a boi id prefix) prefills the row's
  identity. A correction is a new revision; the newest manual revision is the effective head.
- `boi fetch`: a plan (it opens no browser); `--apply` drives Kapture and appends the same manual
  `boi.recorded` that `boi add --manual` would, with the invoice document as evidence (Cartesia
  only; [month-close.md](month-close.md) step 2).
- `boi review`: one `scope.reviewed` (`keep-manual` or `accept-api`) for a reconciliation conflict.
- `rule add`: one `rule.added` per rule (`--from-file` records a seed's rules in one
  transaction). `rule revoke`: one `rule.revoked`; the original stays. `--timing forward` applies
  from today by default; `--effective-from YYYY-MM-DD` dates it explicitly (forward rules only),
  and a forward rule never reaches an earlier period. `one-off` binds a scope or a period.
  `rule add discount --on service_fee --term-months 12 --pay-months 10 --reason ...` (or `--bps`,
  `--flat-cents`) adds a negative Yrd line that reduces the service-fee lines only (never usage,
  never below zero); it is allowed for a client that forbids markup because it only subtracts;
  `--on` anything but `service_fee` is `DISCOUNT_TARGET_UNSUPPORTED`.
- `rule add retainer`: one `rule.added`; the Platform line, the allowance at cost and the
  `Usage above plan` line ([pricing.md](pricing.md)). The default line catalog comes from
  `ms rule add --from-file seeds/_template.rules.json --client $CLIENT`
  ([statement-lines.md](statement-lines.md)).
- `pricing policy set`: one `pricing.policy_set`; the same value appends nothing; outside the band
  it needs `--outside-band` (`PRICING_OUTSIDE_BAND`). It changes no charge. `pricing policy
  show`, `pricing simulate` and `pricing suggest` append nothing: simulate evaluates
  hypothetical models in memory, suggest prints commands it never runs.
- `adjust item`: writes the one-off rule **and** recomputes the boi's and the period's
  client/AAI totals in the same transaction, printing before and after. Flags: `--bill-to`,
  `--split-cap`, `--split-bps`, `--margin` (flat cents), `--margin-bps`. It can never change a
  vendor amount (`ADJUST_AMOUNT_FORBIDDEN`) and refuses imported history (`BOI_IS_HISTORY`).

## Line items and readiness

- `item list` / `item show` (queries, no event): a line item is a view of one boi scope's
  effective head (or of a registered row with no reading yet) plus a state derived from it, never
  stored: `new` (no reading yet), `needs_lookup` (a reading only a person can supply, one with no
  money, or one that cannot reach the statement as read), `conflict` (a newer vendor reading
  disagrees with the manual head), `stale`, `provisional` (an estimate or a partial reading) and
  `final` (actual, complete, fresh). The list is built from shakedown, so the two always agree.
  Each non-final line carries a `resolution` (`run`, `wait_until`, `decide`, `external`;
  [month-close.md](month-close.md) step 3). `--project monthly|weekly` adds a `projection` to the
  lines a projected issue bills at a run rate (an estimate, a partial or a stale api reading of an
  open period; a stale manual invoice is an invoice, never scaled): the amount read so far spread
  over the completed UTC days, extended to the reading's period (monthly) or to seven days
  (weekly), integer math, labelled `estimate`, never recorded.
- `item resolve <ref>` (a plan; `--apply` writes): finds the line like `item show`, then runs the
  squeeze command scoped to exactly that row and period. `--apply` records through the squeeze
  path, so an identical reading appends nothing and a changed one is a new `boi.recorded`
  revision, plus one `squeeze.completed`. A row squeeze cannot read (a manual row, a
  current-state reader asked for a closed month or a range) is `ROW_NOT_SQUEEZABLE` with the
  prefilled `ms boi add --manual` as `next_command`; a retired row is `VENDOR_ROW_UNKNOWN`.
- `shakedown`: the one definition of what blocks a statement. Re-run it after every change. It
  exits 4 when any item blocks and still prints the whole report, every item with its command and
  resolution, so for an agent exit 4 is a normal answer: read the items. **While the period is
  open it always blocks** (every reading is an estimate, partial or stale until the month closes
  and is squeezed again), and `ms yrd build` exits 0 with the same items under "needs input".

## Statements

- `yrd build`: computes the draft from effective bois and rules; prints the lines, the total,
  `inputs_sha256` and the needs-input items; exits 0 even when items block. `--operator` shows
  every boi and its arithmetic (internal only: it names vendors and margins).
- `yrd issue`: a plan by default (the number, the total, what would be frozen, the refusal
  `--apply` would hit). With `--apply` (operators only) it appends one `yrd.issued` freezing the
  lines, the boi and rule ids, the issuer snapshot and `content_sha256`, and stores the customer
  HTML as a blob. Gate: complete issuer; period closed (end plus 1 hour, UTC); no blocking item;
  no overlapping active Yrd; a new number (`AAI-2026-10`, `AAI-YYYYMMDD-YYYYMMDD` for ranges, `-v2`
  for a supersede; numbers are unique across clients, so a second client billing a period whose
  bare number is taken uses `--number-tag TAG` for `AAI-TAG-2026-10`). A first issue of
  client-borne estimate, partial, unavailable or stale cost is refused; `--accept-incomplete
  --reason ... --approved-by ...` covers only an immaterial residual (at most the smaller of
  USD 1.00 or 1% of the total, in all) and is recorded on the event. Issue and due dates use the
  issuer's local date. `tax_treatment_unconfirmed` is a loud warning, not a refusal.
- `yrd issue --projected --reason R` (operator only, a plan by default) issues a month that is
  still open: a final reading as read, an estimate, partial or stale vendor reading at its monthly
  run-rate, a row with no usable money at nothing (listed as left for the true-up with its
  command). The gate skips `PERIOD_OPEN` and those readings' blocking items and refuses the rest;
  a closed period is `PROJECTED_PERIOD_INVALID`; it is exclusive with `--accept-incomplete`. The
  document gains `basis: projected`, the customer one plain note (no vendor), and the operator
  manifest the clock instant, every reading's math and what was left. A supersede of a projected
  Yrd without `--projected` keeps the projection it froze.
- `yrd true-up N [--into next|one-off] --reason R` (operator only, a plan by default) settles it
  after the close, once every client-borne reading is final (`TRUE_UP_READINGS_PENDING`
  otherwise): actual minus projected per customer label, appended as one `yrd.trued_up`. `next`
  (default) carries one adjustment line per label into the next statement without one;
  `one-off` also issues `N-TU` with only those lines. A closed, fully final, unsettled projected
  Yrd is the `projected_unsettled` warning in `ms shakedown`, carrying the command. Figures that
  move *after* a settlement are the `settlement_drift` warning, and the same command settles the
  difference on top of everything already billed (`N-TU2` for a second one-off); nothing moved is
  `TRUE_UP_ALREADY_SETTLED`.
- `yrd verify N` replays the issue from the ledger and proves it reproduces `content_sha256`
  (exit 5 `YRD_HASH_MISMATCH` otherwise, also for an unreadable stored payload). It checks the
  frozen HTML as stored; `template_drift` only notes that today's templates would render it
  differently. A projected Yrd is replayed with the instant and readings it froze, and each
  settlement is recomputed. `yrd show N` and `yrd list` read issued Yrds (`superseded` and
  `settled` are derived; `stale` means a rebuild at the head differs, also a `stale_issued`
  warning in `ms shakedown`). `yrd evidence N --out DIR` writes the backing pack (statement,
  operator view, manifest, evidence blobs): the pack is the only artifact that names vendors and
  its `operator.html` is internal, so never send the whole directory to the client.
- `yrd deliver N --rail mercury` (Q6, Q14): the branded statement is the invoice; this raises an
  optional Mercury AR sidecar with the **same number**, one line `Statement N` for the exact
  total, no vendor detail, due date from the Yrd, ACH and card off (the contract says wire) and
  `sendEmailOption: DontSend`, so the client receives only the Milkshake statement. The plan (no
  `--apply`) reads Mercury (GET only), runs the client fence (the client's own Mercury customer,
  or exactly one AR customer no other client claims) and the **live** duplicate-number fence
  (`AR_NUMBER_EXISTS`, cancelled numbers included), and prints the payload; nothing is sent.
  `--apply` POSTs it and appends `yrd.delivered`; a Yrd is delivered once per rail
  (`YRD_ALREADY_DELIVERED`). `--send-email` (alias `--send`) is the one switch to `SendNow`. A
  `-vN` whose earlier version has live AR follows `MILKSHAKE_AR_SUPERSEDE`: `refuse` (default,
  `AR_SUPERSEDE_REFUSED`), `cancel_recreate` (cancels the earlier invoice only while Unpaid, then
  raises the full new total) or `delta` (never cancels; raises only the difference, refused when
  the new total is not higher). Needs `mise run ms --` for `MILKSHAKE_MERCURY_API_KEY`.
- `yrd payment [N] [--client C]` and `yrd list --with-payment` (FR-54): payment status from
  **Mercury cash**, never from the AR invoice's own status: `paid` (a settled incoming credit that
  names the number, or a wire from the client's payer for exactly the total after the issue date),
  `partial` (with the remainder in cents), `overdue` (nothing matched and past the due date),
  `open`, or `unknown` (on `yrd list --with-payment` without a Mercury credential: still exit 0;
  `yrd payment` itself refuses with `CREDENTIAL_INVALID`, so run it through `mise run ms --`, or
  add `--cached` to read the last cached read with no network). Who may be matched by amount is
  the attribution of [cash-books.md](cash-books.md). `yrd payment` is a plan (GET only, appends
  nothing); `--apply` appends `yrd.payment_changed` only for a Yrd whose state differs from the
  last one recorded. `ms shakedown` adds a `payment_overdue` warning for a Yrd past due and not
  recorded paid.
- `yrd render` / `invoice create`: writes one self-contained HTML file; the customer view never
  names a vendor. Send nothing to a client yourself. `yrd render NUMBER` writes an issued
  statement from its frozen HTML (never rebuilt); `--format pdf` makes the PDF from that HTML
  (optional `pdf` extra) and prints its sha256. Only `yrd issue --with-pdf` stores a PDF on the
  ledger (its sha256 is on `yrd.issued`, and `yrd evidence` then includes `statement.pdf`).
- `--out` (on `yrd render`, `invoice create`, `farm export`) is the file to write. A path without
  a suffix is a directory (created if missing) that gets the default name
  (`AAI-2026-10.draft.html`, `farm.json`); omitted, the file goes under `out/`. The write is
  atomic (temp file, then rename), so a failed run never leaves half a statement behind.
- `portfolio --period YYYY-MM` (read-only): one row per registered client for the month, each
  active issued statement overlapping it (the figures frozen at issue; a one-off `N-TU` is its own
  row) or else the draft at the ledger head. Per row: billed, client-borne and AAI-borne cost,
  margin, fees, discount, kept (billed less every vendor cost; negative when AAI subsidises the
  client; an adjustment line is client-borne cost of the period it adjusts, never kept) and
  unpaid (from the last recorded payment check; `None` when never checked, counted in
  `unpaid_unknown`). Totals per currency.

## History and cash

- `parity` (read-only) compares the imported legacy heads with Milkshake's per scope and exits 4
  when a scope differs. `import legacy` is a plan unless `--apply` (operators); imported readings
  are history only: never billed, never a manual or native head, so `adjust item` on one is
  `BOI_IS_HISTORY`.
- `reconcile` compares Mercury cash with accrued bois, never sums them, and needs
  `mise run ms --` for the Mercury key (`CREDENTIAL_INVALID` otherwise).
- `tx sync`, `tx autotag`, `tx categorize`, `category propose` are plans; with `--apply` they
  append `tx.observed`, `tx.tagged` (`source=rule` or `jev`) or `tx.unfit`, and
  `category.proposed`. `tx tag` appends one `tx.tagged` (`source=manual`). `category accept` and
  `category add` append `category.added`, `reject` a `category.rejected`, `retire` a
  `category.retired` (operator only). `tx push --apply` (operator only) writes Mercury and appends
  one `tx.pushed` per confirmed write. None of them changes a charge: [cash-books.md](cash-books.md).

## The ledger: store, read-only mode, backups, cache

- **The store.** Since 2026-10-27 the live ledger is Milkshake's own Postgres
  (`milkshake-postgres`, 127.0.0.1:5441), named by `$MILKSHAKE_HOME/store.json` (default
  `~/.local/share/milkshake/`) together with a 1Password reference to its password (read with
  `op read` when a store opens, so `OP_SERVICE_ACCOUNT_TOKEN` must be set) and Milkshake's Redis.
  Every `ms` on the host uses it, so there is one ledger. The old SQLite file sits beside it,
  read-only, as `ledger.sqlite3.pre-pg-20261027`: history, never a store. An explicit
  `MILKSHAKE_LEDGER_URL` (never with a password: that is `MILKSHAKE_LEDGER_PASSWORD`) or a
  `MILKSHAKE_HOME` without a `store.json` points `ms` elsewhere, which is how copies and
  rehearsals work. Never edit `store.json` or the database: changing the store is an operator's
  decision. Runbook: `docs/runbooks/postgres-store.md`.
- **Export, migrate, reproject.** `ms ledger export --to FILE` copies whichever ledger is open
  into a new, verified SQLite file (the backup and rollback format; you may run it).
  `ms ledger migrate --from URL --to URL` is a plan that verifies the source and reads the
  target; `--apply` (operator only) copies the chain verbatim into an empty database and proves
  it (`LEDGER_TARGET_NOT_EMPTY` otherwise). On Postgres the `money` tables (clients, line items,
  statements, payments, transactions, tags, categories) are projections kept equal to the fold
  in every append transaction, for the Farm, trend and the explorer to read fast; nothing that
  issues or verifies reads them. `ms ledger reproject --check` proves them equal (exit 5
  `PROJECTION_DRIFT` otherwise; you may run it); the rebuild without `--check` is an operator's.
  On SQLite there are no projections and `reproject` does nothing.
- **Read-only mode.** `MILKSHAKE_READONLY=1` opens the ledger read-only (`mode=ro` on SQLite,
  the `milkshake_ro` role on Postgres) for inspecting a restored backup, or when you must be
  certain nothing is written. Unset the variable to leave it; an empty `MILKSHAKE_READONLY=` is
  `SETTINGS_INVALID`. Every writing command, and the plans of the commands that open the ledger
  for writing (`squeeze`, `item resolve`, `yrd issue`, `yrd true-up`, `boi fetch`, `import legacy`,
  `ledger publish`), are refused with `LEDGER_READONLY`.
  These still work: `shakedown`, `item list|show`, `yrd build|show|list|verify|render|evidence`,
  `invoice create`, `boi list|show`, `rule list`, `pricing policy show|simulate|suggest`,
  `trend`, `portfolio`, `audit` (it simply does not record; `--llm` is refused, run without it),
  `parity`, `tui --json`, `tx list`, `category list`, `farm export`, `farm push` (the plan),
  `farm invoicer list`, `ledger verify|log|backup|export`, `ledger migrate` (the plan),
  `ledger reproject --check`. A
  month-close dry run in read-only mode therefore covers shakedown, build, trend and audit, and
  skips the squeeze plan.
- **Backups.** The nightly timer exports the ledger to a verified SQLite copy plus an offsite
  restic snapshot (`docs/runbooks/ledger-backup.md`). An operator runs `mise run ledger:backup`
  after every `yrd issue --apply` and `farm push --apply`. You may make a copy yourself with
  `ms ledger backup --to PATH` (a new path, outside any git work tree): it is verified when
  written, and it works in read-only mode. **Restoring is an operator's decision.** To inspect a
  copy, put it in an empty directory as `ledger.sqlite3` (no `store.json`), then
  `MILKSHAKE_HOME=DIR MILKSHAKE_READONLY=1 ms ledger verify`. Never try an experiment (an
  `adjust`, a rule) on the real ledger: do it on such a copy, with `MILKSHAKE_HOME` pointing at
  it, and delete the copy.
- **The read cache.** With `MILKSHAKE_REDIS_URL` set (Milkshake's own Redis, never the shared
  one), a non-metered vendor read is cached for six hours (`MILKSHAKE_CACHE_TTL_S`): a repeat
  `ms squeeze` reports that row `cached` and calls nothing; `--refresh` reads it again. Any change
  to a client makes its cached reads unreachable, a Redis failure is just a miss, and nothing
  that builds, shakes down, issues or verifies ever reads the cache. Unset, nothing changes.
- **Installation.** `ms` on `PATH` is an editable `uv tool` install of the main checkout
  (`mise run tool:install`, an operator step, with every extra: `pg`, `cache`, `fetch`, `pdf`,
  `bus`, `tui`, `aws`). If `ms --help` lacks a command this skill names, the install is a stale
  snapshot: tell an operator to run `mise run tool:install` after pulling, and to restart
  `milkshake-farm-consumer` and `milkshake-outbox`.
