# Next-Ticket Triage

BMAD story: `PLC-E2-S5: Add next-ticket triage workflow` (Plane `CAF-121`).

## Purpose

This workflow lets a non-technical operator say "continue" or "what ticket
next" and still get a defensible implementation choice. It prevents work from
starting before its prerequisites are ready.

## Inputs

- BMAD lifecycle epics:
  `_bmad_output/planning-artifacts/project-lifecycle-workflow-stack-epics.md`
- Lifecycle status ledger:
  `_bmad_output/planning-artifacts/lifecycle-status-ledger.json`
- Local Git branch evidence from `git branch -a --list '*CAF-*'`
- Plane parity evidence from the mirror and drift tools

BMAD owns requirements. The ledger owns execution state. Plane mirrors the
ledger for team visibility.

## Command

```bash
# Print the current dependency order and selected next ticket
python3 skills/project-lifecycle/scripts/triage_next_ticket.py

# Write the handoff report
python3 skills/project-lifecycle/scripts/triage_next_ticket.py --write-report

# Machine-readable form for future orchestrators
python3 skills/project-lifecycle/scripts/triage_next_ticket.py --format json
```

Default mode is read-only. `--write-report` creates:

```text
_bmad_output/planning-artifacts/lifecycle-next-ticket-triage-report.md
```

## Selection Rules

The triage script:

1. Parses the lifecycle BMAD stories.
2. Applies ledger status for each CAF ticket.
3. Builds the dependency graph.
4. Skips `done`, `review`, and `blocked` stories.
5. Skips stories whose dependencies are not `done`.
6. Chooses the first available story by lifecycle priority.

`review` is deliberately skipped because it means a human/code-review gate is
already active. The orchestrator should move useful work elsewhere instead of
duplicating review work.

## Dependency Rails

The operating layer comes first:

```text
CAF-119 -> CAF-120 -> CAF-121
```

Then the dev-team rails:

```text
CAF-137, CAF-139
```

Then the runtime shape:

```text
CAF-122 -> CAF-123 -> CAF-133
```

Then generic backend/MCP tools:

```text
CAF-131 -> CAF-132 -> CAF-134
```

Then Hermes router work:

```text
CAF-127 -> CAF-128 -> CAF-130 -> CAF-129
```

Then migration and artifact review/generation:

```text
CAF-124 -> CAF-125 -> CAF-126
```

Observability (`CAF-135`) depends on the guided-action/tool surface enough to
tag useful routing decisions.

## Verification

```bash
python3 skills/project-lifecycle/scripts/test_triage_next_ticket.py
```

For a full lifecycle check:

```bash
python3 skills/project-lifecycle/scripts/sync_plane_from_bmad.py
python3 skills/project-lifecycle/scripts/detect_plane_drift.py --ignore-plane-only-status
python3 skills/project-lifecycle/scripts/reconcile_status.py
python3 skills/project-lifecycle/scripts/triage_next_ticket.py --write-report
```
