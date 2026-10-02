---
name: detached-worker-completion
description: Use when a delegated worker outlives the launching session.
---

# Detached worker completion routing

## Why this exists

A one-shot runner — `hermes -z`, a cron job, a Kanban worker, a stateless HTTP
endpoint, a Bloodbank-command invocation — **cannot receive terminal
notifications for background processes it starts**. The tooling states this at
launch ("it cannot receive an async completion after the turn ends"). Anything
still running when the turn ends is unsupervised: nobody learns it finished,
nobody learns it died.

Not hypothetical. On 2026-10-02, two detached Codex implementers on the
holocene board (HOLOC-9, HOLOC-10) died silently mid-run — no terminal marker,
no final report, clean git tree. In both cases the only reason the death was
noticed same-minute is durable completion routing built **before** dispatch.
Silent worker death is a supervision problem to engineer for, not a verdict on
any particular worker CLI.

## When this skill applies

Dispatch any long-running worker (implementer, build, emulator run, reviewer,
watcher) when ALL of these hold:

- the orchestrating session ends when its turn ends (one-shot context), or may
  end before the worker does;
- the result of the worker must be reported or acted on;
- no human is watching the process.

If the session CAN await the result (interactive foreground with
`process(action='wait')` or a synchronous subagent), ordinary await supervision
is simpler — use that instead.

## Workflow (in order — routing is built before the session exits)

1. **Dispatch with a durable spool.** One ignored directory per ticket under
   the role runtime (e.g. `agents/hermes/pm/runtime/workers/<TICKET>/`):
   `task.md` (full self-contained worker prompt — ACs verbatim, allowed and
   forbidden writes, output contract), `dispatch.json` (identity, PIDs,
   session ids, paths), worker stdout JSONL + stderr files, a designated
   final-message file, and an initialized handback bundle.
2. **Prove the worker actually started before claiming anything.** The process
   exists with its cwd inside the assigned worktree. For Codex: the native
   session id from the JSONL `thread.started` matches completed gateway usage
   rows — `gateway-proof.py session --session-id <id>`. A launched wrapper is
   not a started worker.
3. **Pin exact process identity.** Record PID **and** `/proc/<pid>/stat`
   field 22 (starttime) at dispatch. Parse by splitting after the LAST `)` —
   comm can contain spaces and parens — and take token index 19 past the comm
   field. The start-tick defeats PID reuse; a PID alone does not.
4. **Write progress-first discipline into the worker prompt.** The worker
   writes a progress skeleton (identity, base SHA, unproven AC matrix) BEFORE
   long exploration or builds, and heartbeats the handback bundle. A silent
   death must still leave evidence on disk.
5. **Launch a completion watcher before the session exits.** The watcher polls
   the pinned identity (PID + start-tick), and on exit (or timeout) inspects
   the worker's own artifacts — never the watcher's assumptions.
6. **Classify honestly.** Terminal JSONL markers (`turn.completed` /
   `turn.failed` / `turn.aborted`) plus a nonempty final-message file.
   `worker_exited_incomplete` is a legitimate outcome. A handback bundle that
   passes `validate` is **structural evidence only** — a dead worker's bundle
   validates too. It can never manufacture DONE.
7. **Route exactly ONE deterministic completion command.** Canonical
   `bloodbank.agent.invocation.start` (existing type — never invent a new
   event type, never emit an invocation-completed fact) back to the owning PM
   agent for handback/review or recovery:
   - `command_id` / `idempotency_key` derived `uuid5` from the worker session
     → a watcher restart re-publishes identical bytes, and the gateway
     deduplicates on redelivery;
   - the exact envelope is persisted to disk BEFORE the first publish attempt;
   - bounded transport retries resend identical bytes and NEVER retrigger,
     restart, or signal the worker;
   - `data.context` carries `{reason: worker-handback, repo, ticket_key,
     ticket_id, board_id, workspace, worker_session, watcher_outcome,
     watcher_evidence}` — the recovery turn gets everything without guessing.
   - Note: `reason: worker-handback` does not match the n8n Ticket Pickup
     Chip's `ticket-grooming|ticket-delegation` reasons, so the recovery turn
     does not fight the pipeline over `agent:working`. Keep it that way.
8. **Verify before walking away.** Watcher unit tests green (including the
   fake-process fixture), watcher state files 0600 / dir 0700, envelope on
   disk equals published bytes, and a restart is an idempotent no-op.

## Pitfalls

- **Fake `/proc` fixtures put the tick in the wrong field.** Real
  `/proc/<pid>/stat` has starttime at field 22; a naive test fixture writing
  it at field 5 makes the parser correctly report "exited" and the whole suite
  fails. Fixture must emit the state token plus 18 filler fields, then the
  tick (see references for the exact recipe).
- **`notify_on_complete=true` is silently ignored in one-shot contexts.** The
  launch output says so — read it, and never rely on a completion ping you
  were told you cannot receive.
- **A delegated tooling subagent may die before its final report** (API
  failure after its file writes succeeded). Its artifacts are
  unverified-but-present: stat, read, and test them yourself. A missing
  self-report is not missing work; re-dispatching duplicates effort. In the
  HOLOC-10 session the watcher subagent died pre-report with a correct script
  and a broken fixture on disk — the parent fixed the fixture in minutes.
- **Retries are transport-only.** A retry loop that re-runs the worker or
  mints a second command id breaks the exactly-once property.
- **Don't conflate outcomes.** success / worker_failed /
  worker_exited_incomplete / watch_timeout are four different facts; publish
   the one that is true, and let the recovery turn decide.

## Verification steps

1. Watcher test suite passes locally (fake proc tree + fake bus — no live
   command is ever sent from tests).
2. `ps` confirms the pinned PID is the intended process; the recorded
   start-tick matches a live read of `/proc/<pid>/stat`.
3. Gateway receipts prove the worker's first real inference (Codex: session id
   match in usage rows).
4. After the worker exits: watcher-notification.json shows exactly one
   published command; watcher-envelope.json equals the published body; exit
   code reflects the honest outcome (0 success / 1 failure / 2 could-not-publish).

## Support files

- `references/detached-completion-routing.md` — full watcher design contract,
  the `/proc` stat parsing recipe, envelope determinism details, and both
  2026-10-02 incident walkthroughs (HOLOC-9, HOLOC-10).
- `templates/watcher-config.json` — the proven watcher configuration shape,
  parameterized.
