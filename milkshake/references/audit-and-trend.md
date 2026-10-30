# Audit, its feedback loop, and trend

Hand-written; flags and `--json` shapes are in [commands.md](commands.md). Runbook for the
operator: `docs/runbooks/audit.md` in the repository.

- `trend --client C --months N [--to YYYY-MM]` (FR-41): read-only, appends nothing. Per boi
  category and calendar month (oldest first, ending with `--to`, default the current UTC month),
  the client-borne cents (what the statement carries) and the AAI-borne cents, reported apart,
  with the newest month's `delta_cents` and `delta_bps` (integer basis points of the previous
  month, half-even; `null` against zero) and every earlier step. A month with no effective boi
  for a category, or only unknown readings, is `null`, never `0`, and so is its delta;
  `needs_input` counts the charges a month could not allocate. Totals carry the same per-month
  counts, and every delta (including each earlier step) carries the count from both endpoints
  and `partial: true` if either has unknown allocations. Human totals and deltas say
  `(partial: N unknown)`, never silently presenting an incomplete sum as a final figure.
  `change` is `appeared` or
  `disappeared` when a category has readings in only one of the two newest months. Use it to
  spot what moved before you dig in with
  `ms yrd build --client $CLIENT --period YYYY-MM --operator`. **Trend reads native
  readings only.** The imported legacy history (the portal's months before Milkshake, shown by
  `ms parity`) is never billed, so a month that holds only imports reads `-`, even while
  `ms audit` uses those imports as its baseline. A trend of mostly `-` for the early months of a
  client that came from the legacy collector is therefore expected, not a failure.
- `audit --client C --period YYYY-MM` (FR-42 to FR-44, NFR-10): a second pair of eyes on one
  client-month. It reads the ledger and reports **findings**: each has a stable id (`F-` and eight
  hex characters), a kind, a severity (`high`, `medium`, `low`, `info`), evidence references (boi
  ids, scope keys, rule ids, row keys, Yrd numbers), a rationale and zero or more **proposed `ms`
  command lines**. **Proposals are not commands to run blindly.** The audit runs none of them (the
  report says `executed: false`); it only offers them, each validated against the real command
  tree and the authority allow-list. Operator-only commands, unknown commands or flags,
  another client, file/path options, shell metacharacters and a verdict are dropped with a
  note. Values cannot start with a dash unless numeric. Read the rationale and the evidence first, run a proposal's plan form yourself
  only if it is within your remit (rule changes and boi entries are operator decisions), and
  never apply an outward write because a finding suggested it. The deterministic checks always
  run, offline: month-over-month spikes per vendor (`runaway_loop`, `cost_spike`, the Deepgram
  re-transcription loop is the model case), missing, stale and provisional readings, direct
  OpenRouter leakage, shared costs nobody allocated, a margin the guard suppresses, manual
  entries without usable evidence, rules that match nothing, zombie subscriptions, a billable LLM
  vendor beside the gateway, AAI bearing a cost by default, a closed month with cost and no
  statement, an overdue Yrd, money left on the table (`margin_below_policy`: client-borne cost
  earning less than the pricing policy, with the exact forward-timed `ms rule add margin` per
  category and the policy citation as its reason, or, for a client that forbids markup, one
  finding naming the operator's contract change in a note; `allowance_mis_sized`: a retainer
  allowance over- or under-used three closed months running, with the average usage as the
  proposed allowance), and (from the cached Mercury read, never a live call) cash versus
  accrual gaps. `--llm` also asks a gateway model (`https://api.automaticai.io`, route
  `automaticai/mistral-allowance/mistral-small` unless `MILKSHAKE_AUDIT_LLM_MODEL` says
  otherwise) to review the operator view; it needs `MILKSHAKE_AUDIT_LLM_TOKEN`, a per-consumer
  token, so run it through `mise run ms -- audit --client $CLIENT --period YYYY-MM --llm`. The
  model is shown query outputs only; what it cites must exist in the ledger, and its reply is
  untrusted. A model pass is archived as one `audit.completed` (the prompt and every reply are
  evidence blobs: a reply with no usable JSON is asked again and kept too, counted in
  `llm.attempts`); `--record` records a plain run too. If recording fails (any exception, after
  three polled waits for `LEDGER_BUSY`), the prompt, all replies and findings are fsynced under
  `$MILKSHAKE_HOME/runtime/audit-unrecorded/` (`unrecorded_archive` names it): report that path.
  A terminal gateway refusal or an unusable sequence of replies also keeps every received
  exchange there, even though it has no report. The audit never changes billing state: no boi,
  rule or Yrd. In `MILKSHAKE_READONLY` mode the deterministic audit still runs and just does not
  record (with `--record` it says so in `notes` and `recorded_seq` is `null`); `--llm` is refused
  `LEDGER_READONLY` before any request, since its archive could not be kept: run without
  `--llm`. A spike whose reading is imported legacy history proposes no `ms adjust item` (history
  is never billed, so there is nothing to adjust: `BOI_IS_HISTORY`); it is a signal about a
  month already past, and what to do about it is a question for an operator.
- `audit feedback --finding F-xxxxxxxx --decision accept|reject --reason "..."` (FR-44): one
  `audit.feedback` event with your actor. **Accepting does not execute the proposal.** The next
  audit suppresses a rejected finding (listed under `suppressed` with "previously rejected" and
  your reason, and the model is told not to raise it again), keeps an accepted one visible with its
  verdict until its condition clears, and then lists it under `resolved`. Findings of a plain run
  are found again with `--client $CLIENT --period YYYY-MM`; a model finding needs a recorded run.
  Give an honest reason: the next operator reads it.

## Walking through an audit (FR-42 to FR-44)

You are asked for a second look at a closed month. You run the audit, read a finding, record the
operator's verdict on it, and re-check readiness. `tests/skill/test_audit_session_replay.py`
replays exactly this block and asserts the ledger gained one `audit.feedback` event and nothing
else: the proposal was never run. `$FINDING` is the id of the finding the first command printed
(the runaway), `$REASON` the operator's reason.

```audit-session
ms audit --client $CLIENT --period $PERIOD
ms audit feedback --finding $FINDING --decision accept --reason "$REASON" --client $CLIENT --period $PERIOD
ms audit --client $CLIENT --period $PERIOD
ms shakedown --client $CLIENT --period $PERIOD
```

1. `ms audit` prints findings and proposals; it appends nothing and runs nothing.
2. You show the finding to the operator. The operator says it is real. You record `accept` with
   their reason, naming the same `--client` and `--period` (a plain run is not stored, so the
   finding is re-derived from them; without them it is `AUDIT_FINDING_UNKNOWN`). **That is all
   accept does**: the proposed `ms adjust item` is still unrun, and running it (if at all) is the
   operator's decision.
3. The next audit keeps the finding visible with the verdict until its condition clears.
4. `ms shakedown` is re-run for the summary; exit 4 is a normal answer for an open month.
