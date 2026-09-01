# Review and closure

Clearing the review lane is the **normal per-pass path**, not an escape hatch. Momo runs an
independent adversarial review against the operator's locked intent and acts on the verdict
autonomously — it does not wait for the operator's first right of refusal. The operator's QA
is *deferred* to an end-of-product sweep over the review lane, backed by a queryable decision
trail; a downstream regression rollback is the safety valve.

These scripts live in the repo's `<role_dir>/.scripts/sentinel/bin/` and are provider-
agnostic. A manual session calls them directly.

## 1. Close gate (evidence completeness) — a hard automated lock

```bash
<role_dir>/.scripts/sentinel/bin/issue-close-gate.sh <ISSUE> [REPO_ROOT]
# exit 0 = PASS, 1 = FAIL (missing/incomplete evidence), 2 = bad usage
```

It validates the evidence file `_bmad-output/implementation-artifacts/issue-evidence/<ISSUE>.md`.
Requirements (see `templates/issue-evidence.md`, which matches exactly):

- Must contain these `##` headings: **Issue, Acceptance Criteria, Repo Changes,
  Verification, Ledger Update, Known Gaps, Close Recommendation**.
- Must contain the literal lines `Ledger updated: yes` and `Close recommendation: ready`.
- Must NOT contain (case-insensitive, anywhere) the placeholder words `TBD`, `TODO`,
  `not run`, `pending`, `unknown`. **Gotcha:** these trip on narrative prose too — write
  "no gaps" not "none pending", "did not execute" not "not run".

The close gate does **not** check for a worker-attribution line. Still, always include a
`- Worker:` (or `- Implemented by:`) line in the evidence (the template does): it is what
the autonomous review's **independence check** reads to confirm reviewer ≠ implementer. That
check only HOLDs when a parsed implementer *equals* the reviewer — a missing worker line
fails neither gate, but then independence is unproven, so write it.

## 2. Autonomous adversarial review — the decision engine

```bash
<role_dir>/.scripts/sentinel/bin/issue-autonomous-review.sh <ISSUE> <ISSUE>.review.md
# exit 0 = accepted, 3 = held (or disabled), 2 = missing inputs, 1 = adapter transition failed (--close only)
```

It chains, accumulating HOLD reasons: report structure → **reviewer independence** (reviewer
agent ≠ the implementer named in evidence) → drift rubric → adversarial findings → reviewer
decision → the close gate. The verdict is the exit code plus what it prints; the script
publishes no event (the old `…issue.*` family was never consumed and was retired
2026-08-28). You author the review report at `<ISSUE>.review.md` (shape in
`templates/review-report.md`) — that report, the issue evidence file, and the ticket comment
ARE the accountability trail. Record the judgment call itself with `record-decision.py` when
it is worth a durable decision event.

**Drift rubric** — accept only `none`/`minor` with no unresolved critical/high finding:
- `significant` (HOLD): an AC unmet; capability added/removed beyond the ACs/milestone;
  contradicts a locked decision/north star or locked architecture; pulls later work into
  now; introduces a new external dependency/credential/paid action.
- `minor` (accept allowed): internal refactors, extra tests, naming, cosmetics, docs.
- `none`: matches locked intent and ACs.

The close gate stays a HARD lock: the script will not emit `accepted` while the gate fails,
drift is `significant`, a critical/high finding stands, or independence isn't satisfied.
Run WITHOUT `--close`.

## 3. Act on the verdict (autonomously — no grace wait)

- **accepted** (exit 0): treat the ticket as **done for dependents and flow**, but **leave
  it in the review lane** — that lane is the operator's deferred-QA queue. Do NOT
  auto-transition to `completed` (`--close` is an optional operator QA-sweep flag the loop
  omits). Post ONE ticket comment stating the autonomous acceptance with a pointer to the
  report — never a "waiting on you" comment. Record a Momo decision event
  (`record-decision.py`, basis `evidence-over-status`, `bias-to-reversible-action`). A
  dependent blocked only on this feature is now unblocked.
- **held** (exit 3 with a real finding): move the ticket back to active (`started` if a
  worker takes it now, else `unstarted`); record the hold reasons; emit the decision event.
  When in doubt, hold.
- Distinguish **held-by-finding** from **disabled-by-config**: a run disabled via
  `reconcile.auto_review=false` / `RECONCILE_AUTO_REVIEW=off` also exits 3 but emits NO
  decision event — read the stderr message.

### Stable findings ledger (33GPM-6)

Findings are tracked in a per-issue JSON ledger, not re-enumerated in prose comments:

```bash
python3 momo/skill/scripts/momo-findings-ledger.py --issue <ISSUE> add \
  --severity critical --category security --description "Cross-tenant data leak"
python3 momo/skill/scripts/momo-findings-ledger.py --issue <ISSUE> resolve --id F-001
python3 momo/skill/scripts/momo-findings-ledger.py --issue <ISSUE> show
python3 momo/skill/scripts/momo-findings-ledger.py --issue <ISSUE> markdown
```

The ledger lives at `_bmad-output/implementation-artifacts/findings/<ISSUE>.findings.json`.
Finding IDs are stable (F001, F002, ...) and survive across comments. The `markdown`
subcommand renders a table for ticket comments. Momo reads/writes the ledger instead of
re-enumerating findings in prose.

### Gated lane transitions (33GPM-7)

Lane transitions are precondition-checked, not repaired later:

```bash
python3 momo/skill/scripts/momo-lane-gate.py --issue <ISSUE> --target completed [--review-file <FILE> | --no-review]
# exit 0 = allowed (and transitioned), 1 = blocked (JSON on stdout), 2 = error
```

Gates checked before `in_review`: tree lock (not locked by another session), close gate
(evidence file complete). Gates before `completed`: all of the above plus autonomous
review (if `--no-review` is not set). The gate returns structured JSON with per-gate
pass/fail details. A failed transition is a structured error, not a later audit.

### Reporting discipline (33GPM-5)

One comment per event. Each comment contains delta + current state + asks only.
Post-mortems go to the decision trail (`bloodbank-events.jsonl`) with a link, not
duplicated in the ticket. The reporter deduplicates by content hash before posting:

```bash
python3 momo/skill/scripts/momo-reporter.py --issue <ISSUE> \
  --event impl-complete --delta "All ACs met" --state "ready for review" [--dry-run]
```

Use `--dry-run` to preview the comment body and hash without posting. The dedupe guard
prevents the same content from being posted twice (the 10:36/10:38 duplicate scenario).

## 4. Downstream regression rollback (the safety valve)

If a later dependent proves a review-accepted feature is ACTUALLY BROKEN: move the accepted
ticket back to active as a **prerequisite** of the dependent (`tp transition`); comment
naming the dependent + symptom; record the rollback (issue, surfaced_by, reason) in the
issue evidence file, and record a Momo decision event with `record-decision.py`. This is
expected and healthy — the trade for deferring operator QA, not a failure.

## Out-of-scope blockers (review does NOT clear these)

Record and wait, exactly as before: external credentials / third-party access / paid
actions; an undecided product decision; ACs not actually satisfied by evidence; a dependency
on another open, unblocked issue.

## Anti-stall (repeat, because it matters)

For any review-lane ticket there are exactly three legitimate outcomes: **accepted** (move
on), **held** (back to active), or a genuine **out-of-scope blocker** (recorded + waited on).
There is no fourth "waiting for the operator's sign-off" state.
