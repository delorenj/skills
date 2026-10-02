# Detached completion routing — design contract and incident detail

Companion to `detached-worker-completion/SKILL.md`. Session-proven on the
holocene board 2026-10-02 (HOLOC-9 and HOLOC-10 pickups).

## The watcher design contract (what to build)

A watcher is a small Python script, launched detached via
`terminal(background=true, notify_on_complete=false)` as the LAST act before
the session ends. It must:

1. **Poll exact identity, not PID alone.**

   ```python
   def read_start_tick(proc_root, pid):
       raw = (proc_root / str(pid) / "stat").read_text()   # OSError -> exited
       after_comm = raw[raw.rindex(")") + 2:]              # comm may hold "()" and spaces
       return int(after_comm.split()[19])                  # field 22 overall
   ```

   `alive` = tick matches recorded; `reused` = tick differs (treat as exit of
   the original); `exited` = no /proc entry.

2. **Classify from the worker's own artifacts.**
   - Scan the worker stdout JSONL; count only lines that parse as JSON with a
     `type` string among `turn.completed` / `turn.failed` / `turn.aborted`.
   - `success` = turn.completed AND final-message file exists nonempty.
   - `worker_failed` = turn.failed/aborted present.
   - `worker_exited_incomplete` = process gone, no terminal marker or no
     final message. **This is the honest outcome for a silent death.**
   - `watch_timeout` = poll deadline reached while alive.
   - A handback bundle's `validate` == VALID is structural only. A dead
     worker's initialized bundle validates too. It never upgrades the outcome.

3. **Publish exactly one command, deterministically.**
   - Type `bloodbank.agent.invocation.start` (command), subject
     `bloodbank.cmd.agent.invocation.start`, built through Bloodbank's
     canonical `core/envelope.py:build_envelope(..., validate=True)` and
     `core/validate.py:assert_contract` — never hand-rolled JSON.
   - `command_id = uuid5(NS, f"<ticket>:<session>:command")`,
     `correlationid`/`causationid` likewise; `idempotency_key` derived from
     `command_id`. A restart with lost state re-derives identical bytes.
   - Check registry eligibility first (`~/.hermes/agents-registry.yaml`:
     `profile_name` nonblank, `bloodbank.gateway_scope == fleet`,
     `target_agent_id` match, `enabled` absent-or-`true`; absent means
     enabled). Read-only — never print or mutate registry contents.
   - Persist the exact envelope to disk BEFORE the first publish attempt;
     publish via `core/nats_publish.py` with bounded transport retries
     (identical bytes; never re-invoke anything about the worker).
   - Watcher-owned state under `<spool>/watcher-state/`: dir 0700, files 0600
     (`watcher-state.json` with `published` marker for idempotent restart,
     `watcher-envelope.json`, `watcher-notification.json`,
     `watcher-progress.jsonl`).
   - Exit codes: 0 = success outcome published (or idempotent no-op restart);
     1 = honest failure/timeout outcome published; 2 = could not publish /
     ineligible / bad config.

## The /proc fixture pitfall (cost ~3 test runs to find)

Real `/proc/<pid>/stat`: field 1 pid, field 2 comm (may contain spaces and
parens), field 3 state, …, **field 22 starttime**. The parser indexes token 19
counting from after the comm's closing paren, which lands on field 22. A test
fixture that writes the tick a few fields after the comm makes the parser see
a *different* field as the tick, mismatch, and report `exited` for a process
the test just added — every identity-dependent test fails. Correct fixture:

```python
fillers = " ".join(["0"] * 18)                       # fields 4..21
(stat_file).write_text(f"{pid} ((codex) s) {fillers} {tick}\n")
```

Verify the parser against a REAL `/proc/<pid>/stat` once (read the live tick
of the actual worker PID) before trusting the fixture.

## Incident walkthroughs (2026-10-02, holocene board)

**HOLOC-9 (first occurrence, diagnosed post-hoc).** Detached Codex implementer
exited 1 after five AutomaticAI streaming reconnect failures; branch clean at
base, no result.md, no handback completion. The handback bundle validated
(structural) while the work had not happened — the origin of the
"validate is not completion" rule. Recorded in hindsight bank `holocene`,
doc `holocene-pm-holoc9-worker-failure-20261002`.

**HOLOC-10 (second occurrence, caught live).** PM built routing BEFORE
dispatch: durable spool + progress-first worker prompt + PID/tick-pinned
watcher (unit-tested, PM-repaired fixture) launched before session end. The
implementer died ~14 minutes in, mid emulator phase (second emulator launch),
no terminal marker, no final message. The watcher classified
`worker_exited_incomplete` and published exactly one deterministic recovery
command (`63cffece…`) to `holocene-pm`; its state files proved the sequence.
Two compounding subagent lessons the same hour: the tooling subagent that
authored the watcher died before its final report (API 404 after its writes),
leaving a correct script with a broken fixture — verified by the parent
running the suite, fixing the fixture, and only then launching.

## Envelope determinism details

- Deterministic namespace per ticket+watcher, e.g.
  `uuid.uuid5(uuid.NAMESPACE_URL, "https://33god.dev/<repo>/<ticket>/watcher")`.
- Same session → same `command_id` across runs and across lost state dirs;
  the gateway's journal deduplicates on `command_id`/`idempotency_key`, so a
  crash between persist and publish is safe to retry.
- `data.context.reason: worker-handback` is deliberately NOT
  `ticket-grooming`/`ticket-delegation`, so the n8n Ticket Pickup Chip does
  not add/remove `agent:working` for the recovery turn — the pipeline keeps
  owning that label without contention.
