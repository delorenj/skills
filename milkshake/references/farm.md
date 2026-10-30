# Farm, Farm commands and Bloodbank

Hand-written; flags and `--json` shapes are in [commands.md](commands.md). Every refusal named
here is in [refusals.md](refusals.md).

- `farm push` (FR-48): plan by default, and the plan makes no network call and appends nothing:
  it prints the endpoint (`${MILKSHAKE_FARM_URL:-https://www.automaticai.io}/api/milkshake-snapshot`),
  client, periods, `payload_sha256`, byte size and the diff against the last push of this client
  to that endpoint. `--apply` POSTs the snapshot (the canonical JSON `farm export` writes) once with
  `Authorization: Bearer $MILKSHAKE_FARM_TOKEN` and, only when the portal answers
  `{success: true}`, appends one `farm.pushed` (sha, `generated_at`, url, the portal's
  `duplicate` flag and row id; never the token). Operator only: it publishes numbers to the client
  portal. Run through `mise run ms -- farm push --client $CLIENT --period YYYY-MM --apply` so
  `op run` supplies the token (a token on argv is `SECRET_ON_ARGV`). Idempotent: the portal
  returns `duplicate: true` for bytes it holds and the ledger records a push once per client,
  endpoint and `payload_sha256`. A push moves the ledger head, which the snapshot carries, so
  rebuilding with the same `--generated-at` is *different* bytes (portal `409`): to retry,
  re-send the exact file with `ms farm export --client $CLIENT --period YYYY-MM --out FILE` then
  `ms farm push --file FILE --apply`.
- What `milkshake/v1` carries (`ms farm export` and `ms farm push`): only what the Farm shows for
  the requested periods (`--period`, default the previous and current month): each scope's
  **effective** boi head (plus its reconciliation counterpart, the newer vendor reading beside a
  manual head), never legacy imports or superseded revisions; the periods' issued Yrd versions
  and drafts; active rules only. `periods` gives, per month, `bois_total`, `revisions_total`
  and `imports_total`, so the page can say how much history sits behind the view. One month of
  a real client is a few tens of KB; the portal's limit is 512 KB (`FARM_SNAPSHOT_TOO_LARGE`,
  refused before sending: push fewer periods). `generated_at` is always written
  `YYYY-MM-DDTHH:MM:SS.ffffffZ`, whatever spelling `--generated-at` took, and may not be more
  than five minutes ahead of the clock (`FARM_GENERATED_AT_FUTURE`).
- **The snapshot carries the next step** (Story 10.1). Every needs-input item has `command`, the
  exact `ms` command that moves it on (the same text `ms shakedown` prints: a plan
  wherever it reaches outside the ledger, UPPER-CASE words are blanks a person fills), and
  `console_url`, the vendor console page behind its number (`null` for the issuer or a rule).
  Every effective boi row has `state`, its line item's state as `ms item list` derives it
  (`needs_lookup`, `provisional`, `stale`, `conflict`, `final`; a boi row is a reading, so never
  `new`: a row with no reading reaches the Farm only as its needs-input item; `null` on a
  reconciliation counterpart). The Farm shows these; it computes none of them.
- **Cash and inference travel with it** (Story 10.4). Two more keys, always written, read
  purely from the ledger (no Mercury or gateway call at build time), shown on the account's
  **Cash** and **Inference** tabs, operator-only like the rest of the snapshot:
  - `cash.receivables`: every active issued statement of the client (any period, `NUMBER-TU`
    included, newest first, 36 listed) with its recorded payment state, and the outstanding and
    overdue totals, `null` while any statement's payment was never checked; its command is
    `ms yrd payment --client $CLIENT` whenever something is unchecked or overdue.
  - `cash.periods[]`, one per requested period: `applied` (the credits the payment checks matched
    to each statement, whatever their tag; a credit counts once, under the statement of the
    newest record that lists it) and `book`, `null` until `ms tx sync` has written a
    transaction (`sync_command` is `ms tx sync --since YYYY-MM-DD`, the first day shown). In the
    book: `unapplied` (cash tagged as the client's revenue that no payment check matched; command
    `ms yrd payment --client $CLIENT`), `out` (the client's tagged cash by doctrine line,
    category, kind and vendor, with `out_lines` subtotals and `net_cents`), and for the whole
    book `untagged_in`/`untagged_out` (command `ms tx autotag --period YYYY-MM`) and `declined`
    (refused attempts and distinct debts; command `ms tx list --period YYYY-MM`). `covered` is
    false until a sync wrote after the period ended ("so far").
  - `inference.periods[]`: the period's llm charges at the ledger head (cost, AAI-borne, COGS,
    allowance, margin, price, and `pricing` `product`, `pass_through` or `mixed`), `null` while a
    billable llm line has no usable money; `pending` lists those lines with their command (a
    squeeze or a manual boi). Usage counts (`requests`, tokens) are `null` until Story 10.5.
  Nothing here is a statement: the price is what the charges say now; the issued statement's
  Inference line is what was invoiced. You read these figures; every count carries its own `ms`
  plan, and none of them is a reason to apply anything.
- **Farm-originated commands exist, and they are policy-gated.** The Farm's Create Invoice button
  sends a signed command (Bloodbank `bloodbank.cmd.billing.invoice.generate`) that the
  `milkshake-farm-consumer` service executes on big-chungus through the same `yrd issue` as the
  CLI (the Q15 issue gate, number rules and `--accept-incomplete` policy are unchanged). It is
  *not* you and it is *not* an agent. What that means for you:
  - The ledger holds its own grants: `ms farm invoicer list --client $CLIENT`. A grant is **per
    client and per command**, `plan` or `apply` each (`yrd issue`, `squeeze`, `boi review`,
    `rule revoke`, `yrd payment`, `farm push`); only those emails may ask, and each is **plan
    only** unless an operator granted that command's `apply`. A grant from before Story 10.3 has
    no client (`scope: legacy`): Create Invoice for every client, until it is revoked. The portal
    cannot widen any of it. You never run `ms farm invoicer add` or `ms farm invoicer revoke`:
    that is an operator's decision, recorded with a reason. An agent address
    (`@agents.automaticai.io`) can never be granted `apply` on an operator command.
  - A Farm command appears on the ledger as `farm.command.handled` (Create Invoice: status
    `planned`, `issued`, `refused` or `failed`, with the code) under the actor `farm:<email>`, and
    an issue it makes is a `yrd.issued` whose actor is `farm:<email>`. A palette command (below)
    appears as `farm.command.ran` (status `planned`, `applied`, `refused` or `failed`, with
    `appended`, the number of ledger events the run wrote). Unsigned, expired, malformed and
    unknown-actor commands write nothing. A repeat of the same command id is a no-op, never a
    second statement and never a second run.
  - `ms farm export` and `ms farm push` then carry a `commands` list (the client's last twenty outcomes,
    newest first, left out while empty) so the Farm can show what happened. Read the outcome there
    or with `ms ledger log`; never re-run a Farm command by hand to "retry" it.
  - Refusals (`FARM_MODE_FORBIDDEN`, `FARM_APPROVER_INVALID`, `FARM_COMMAND_STALE`,
    `FARM_ACTOR_UNKNOWN`, `FARM_COMMAND_NOT_GRANTED`, `FARM_CLIENT_MISMATCH`, ...) are in the table
    below and in the consumer's result events; none of them is yours to override.
- **The command allow-list** (Story 10.2). What the Farm may ask for is generated from the `ms`
  command tree into `src/milkshake/farm/schema/ms-commands-v1.json` (`ms-commands/v1`, beside the
  snapshot schema, for the portal to vendor): per command its name, its Bloodbank subject
  (`bloodbank.cmd.billing.<entity>.<verb>`), its arguments as a JSON Schema with their flags (and,
  for the palette, their positionals, the span rule and the owner check), its mode (`plan`: writes
  nothing unless `--apply`; `apply`: writes as it runs), the modes the Farm may ask for, its
  authority (`you` or `operator`, the matrix in SKILL.md) and the grant an apply needs. It holds
  six commands: `yrd issue` (Create Invoice, handler `invoice`) and the palette's `squeeze`,
  `boi review`, `rule revoke`, `yrd payment` and `farm push` (handler `run`). Never from the Farm:
  `boi add`, `boi fetch`, `client register|set`, `issuer set`, `vendor register|retire`,
  `yrd deliver`, the grants themselves and the store's own commands. The consumer accepts exactly
  these, on registered subjects, with their listed arguments, and refuses everything else
  (`FARM_COMMAND_NOT_ALLOWED`); an apply needs the grant its entry names, and an operator-authority
  command is never applied without it. You never edit the file: `mise run farm:commands`
  regenerates it from the table in `domain/farm_allowlist.py`, and a test fails when it drifts.
- **The palette** (Story 10.3). The Farm's Commands tab sends a signed v2 command for one of the
  five; the consumer's handler `run` checks the sender's grant for that client, then that the
  scope, rule or statement named belongs to that client (`FARM_CLIENT_MISMATCH` otherwise), then
  runs the exact `ms` argv (always ending in `--json`) in a subprocess whose ledger events carry the actor
  `farm:<email>/<command_id>`. It counts those events: an apply that committed is **`applied`**
  even if the process then failed (the record carries the code, `applied, then <code>`), so a
  failed-looking row with `appended > 0` means the ledger changed. Read it with `ms ledger log`;
  **never re-run a Farm command by hand**, and never re-ask for it: a metered `squeeze --apply`
  pays for its vendor calls every time. The snapshot's needs-input items and non-final line items
  carry `actions` (the structured form of their resolver commands), and `grants` says what each
  email may do for the client.
- **Bloodbank announces ledger changes** (Story 5.5). After a command commits, the
  `milkshake-outbox` service publishes a CloudEvent for it within seconds: `rule.added` and
  `rule.revoked` (`bloodbank.billing.rule.recorded` and `.revoked`), `boi.recorded`
  (`billing.cost.recorded`; legacy imports are never announced), `yrd.issued` and `yrd.delivered`
  (`billing.invoice.issued` and `.delivered`) and `farm.pushed` (`billing.snapshot.sent`). The
  event carries the seq, hash, client and actor and the few fields a partner needs (a rule id and
  reason, a number and total), never evidence or the frozen statement. After it, one
  `billing.line_item.updated` per customer line the commit moved (Story 6.5): the client, the
  period, the customer label, `previous_cents` and `amount_cents` (`null`: the line appeared or
  went), `state` (`open`: no statement covers the period yet, the month of the commit or the one
  before it; `issued`: an active statement does, and `number` names it, so it is now stale) and
  `as_of_seq`. Never a vendor, a rule or a boi; a legacy import moves nothing. The ntfy router
  posts each one to both partners (Q12). You do nothing to make this happen, and a Bloodbank outage never
  fails or loses a command: the outbox catches up from its cursor. `ms ledger publish` with
  `--since-seq` and the first seq to resend is a plan (`--apply` republishes, idempotently); do
  not run `--apply` unless an operator asks.
  A `BUS_NOT_CONFIGURED` or `BUS_UNAVAILABLE` refusal only means nothing was published; the ledger
  is unaffected. `OUTBOX_CURSOR_LOST` (the outbox's cursor went missing, corrupt or stale) and
  `OUTBOX_NOT_INITIALIZED` stop announcements until an operator resends with `ms ledger publish`
  (`--since-seq`, `--apply`) or starts it with `--init --apply`: report them, never touch the
  cursor.
