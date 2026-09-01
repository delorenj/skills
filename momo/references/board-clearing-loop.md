# The board-clearing loop

When the goal is "just clear the board" (no single named ticket), Momo runs a loop that
triages, orchestrates implementation, and holds the result to a high standard — until it is
legitimately done. This mirrors the codified BMAD `ticket-lifecycle` state machine and the
Hermes sentinel's continuous-orchestration protocol. **Do not invent a different machine.**

## Invariant

If a ready ticket exists, exactly one implementation worker is actively moving it, or Momo
records why none can. One live thread beats a quiet backlog (pillar
`keep-the-pipeline-unblocked`). WIP = 1, shared with Hermes via the driver lease
(`scripts/momo-wip-lock.py`; see *One loop pass* → Coexistence lock).

## State machine (mirror of the one versioned Lifecycle spec)

Normalized (adapter) ↔ Plane labels. **SSOT = `krebs/spec/lifecycle.v1.yaml`** (the one
versioned machine); provider label names come from the `tp` adapter, and the repo's
`ticket-lifecycle/workflow.yaml` only overrides knobs. The canonical **unstarted band** is
Triage / Refining / Ready. A literal "To&nbsp;Do" column is *not* in that map — it is Plane's
**default** unstarted group, present only on boards that keep the Plane defaults. Resolve the
board's actual state names via `momo-board.sh` (`list_issues` shows each ticket's `state`)
rather than assuming labels.
`backlog`→Backlog · `unstarted`→Triage / Refining / Ready (or Plane's default "To&nbsp;Do") ·
`started`→In&nbsp;Progress · `in_review`→Review / QA · `completed`→Done. Also: Blocked.

Transitions per ticket: acquired → **triage**; triage → ready (AC 4/4) | refining (any
fail); refining → ready (re-eval passes) | blocked (still insufficient); ready →
**in_progress** (worker spawned); in_progress → **review** then **qa** (gates pass) |
in_progress (gate fails, retry) | blocked (AC ambiguity); qa → **done** (all AC pass) |
in_progress (fail, retries left) | blocked (retries exhausted). done/blocked terminal.

Knobs default from `krebs/spec/lifecycle.v1.yaml` (the SSOT); the repo's
`_bmad/custom/workflows/ticket-lifecycle/workflow.yaml` may override them (do not hardcode):
- **AC rubric** (all 4, no short-circuit): `non_empty ∧ testable ∧ enumerated ∧ fr_coverage`.
- **QA retries**: `qa.max_retries` (default 3); on retry re-verify only previously-failed AC.
- **Staleness (minutes)**: triage 10, refining 30, in_progress 120, review 15, qa 60.

Fix the known gotchas in the codified workflow rather than replicating them: explicitly set
the ticket to Review before the review gate; route ALL blocked paths through a single
completion/summary step; and run the staleness watchdog yourself (no step file enforces it).

## One loop pass

**Coexistence lock (WIP=1, shared with Hermes).** Before driving, acquire the shared driver
lease so you and the Hermes sentinel never double-drive one board:
`python3 scripts/momo-wip-lock.py acquire <runtime>/wip-driver.lock momo` (`<runtime>` =
`<role_dir>/runtime`). **Exit 1** = Hermes holds it fresh → **do not drive** this pass;
monitor its work and back off. **Exit 0** = you hold it → drive, `refresh` it during a long
pass (heartbeat < ttl), and `release` it when the pass ends or on any exit. A crashed
holder's lease expires after its ttl (default 300s), so the board is never wedged.

1. **Awareness** (see `board-awareness.md`): active milestone, `list_issues`, Hermes state,
   evidence dir, event trail, live workers/worktrees.
2. **Is a worker already active and healthy?** (yours or Hermes'). Yes → monitor it, record
   state, and go to step 6 (this pass adds no new worker). WIP=1 (you already hold the lease).
3. **Clear the review lane first.** For any `in_review` ticket with complete evidence and an
   available independent reviewer, run the autonomous adversarial review
   (`review-and-closure.md`) and act on the verdict immediately — accept (treat as done) or
   hold (back to active). A ticket blocked *only* on human review is NOT a stop.
4. **If no worker is active, pick exactly one ticket** (selection policy below), move it to
   `started`, create/refresh its evidence file, and delegate one implementer
   (`delegation.md`). Never self-accept a review in the same pass you implemented it.
5. **Advance the picked ticket** through the per-ticket pipeline (triage→…→gates→review).
6. **Staleness sweep** — any ticket past its state's threshold: record it, emit a stale
   signal, and either re-drive or flag as a blocker. Nothing rots silently.
7. **Update your read of the world** and decide: continue, wait (timer), or stop. On
   stop/exit, `release` the WIP lease (or let it expire) so Hermes can resume.

## Selection policy (when no worker is active)

Pick the first that applies:

1. A `blocked`/`in_review` ticket needing only agent-doable evidence/AC repair.
2. An **unblocked ticket in the active milestone** that is `ready`/`unstarted`.
3. A **To&nbsp;Do** ticket (the board's unstarted/triaged lane — Plane's default "To Do", or
   Triage/Refining/Ready on a ticket-lifecycle board; see the state-machine note) — pull it
   **on your own judgment** only when ALL hold: it is a clear value-add, it is unambiguous,
   and it has enough data to start without guessing.
   Recording this pull as a decision event (basis `keep-the-pipeline-unblocked`,
   `smallest-safe-increment`) is **mandatory** — it is you spending the operator's trust.
4. A small, high-priority **Backlog** ticket — pull ONLY if your judgment says it is clearly
   valuable AND ready. Otherwise **backlog is a stop signal, not a queue.**

If picking would require guessing intent, do not pick — refine first, or leave it and record
why.

## Stop conditions (end the loop cleanly — do not spin)

Stop and report when **any** of these hold:

- **Three consecutive intervals with zero activity.** Track `idle_intervals`. An interval
  counts as activity if a ticket changed state, a worker started/finished, a review
  resolved, or evidence changed. A pass that only re-observes the same state increments
  `idle_intervals`; any activity resets it to 0. At `idle_intervals == 3`, stop.
- **Only backlog remains** (nothing in triage/ready/in_progress/review, and no To&nbsp;Do
  ticket clears the step-3 judgment bar). Backlog is the operator's queue, not yours to
  drain by default.
- **Every remaining candidate is an out-of-scope blocker** — external credentials,
  third-party access, paid actions, or an undecided product decision. Record each and wait.
- The next action needs **destructive git ops / production credentials / a paid action** —
  stop and surface it for the operator.

**Never** stop merely because reviewed work "looks good, waiting on the operator." That is
not a resting state (pillar `keep-the-pipeline-unblocked`). Run the review and act.

Always **record a decision event** when you stop, naming which condition fired and why.

## Waiting on CI / workers — the 10-minute timer

When the only thing to do is wait (CI running, a delegated worker still executing, an
external agent's PR pending), **do not busy-spin and do not end the session** — set a
re-check timer so the pipeline keeps moving:

- Preferred: run the loop under the **`loop`** skill at a 10-minute cadence, e.g.
  `/loop 10m be Momo and take one board-clearing pass`. Each firing is one pass; the loop's
  `idle_intervals` counter applies across firings.
- Or self-pace with a ~600s wake-up (ScheduleWakeup) carrying the same "take one pass"
  intent.
- On each wake: re-read worker/CI state. If the awaited thing finished, resume the pipeline
  and reset `idle_intervals`. If still pending, increment `idle_intervals` and re-arm the
  timer — until a stop condition fires.

Ten minutes is the default heartbeat for a waiting operator session; shorten only if you are
polling something that changes faster, lengthen if you are genuinely idle.

## End-of-run report

When you stop, report: board snapshot (counts per state), tickets touched, evidence
touched, the active worker/blocker (if any), the decision events you emitted, the stop
condition that fired, and the single next recommended action.
