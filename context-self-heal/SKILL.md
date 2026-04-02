---
name: context-self-heal
description: Agent-local context guard and deterministic compaction workflow (GOD-13). Use when context usage is high, when wiring auto-compaction/restart timers, or when deploying standardized context-monitor hooks across agents.
pipeline-status:
  - new
---

# Context Self-Heal (GOD-13)

## Purpose
Provide a reusable, non-agent-specific package for context monitoring and deterministic compaction artifacts.

## Files
- `files/god-13-context-monitor.sh`
- `files/god-13-lenoon-monitor.service`
- `files/god-13-lenoon-monitor.timer`

## Standard Behavior
- Warning zone: >=80% context
- Hard threshold: >=90% context
- Before restart, write deterministic artifact:
  - `memory/context-compaction-latest.md`
  - Sections required:
    1) Active tasks
    2) Decisions made
    3) Open blockers
    4) Next 3 actions on resume
    5) Handoff context

## Deployment Pattern
1. Copy script + units from `files/` to target workspace.
2. Parameterize `AGENT_NAME` and workspace path.
3. Enable systemd timer (`--user`).
4. Verify artifact write + restart path on threshold breach.

## Notes
- Prefer Hindsight plugin as canonical memory; artifact is deterministic restart checkpoint.
- Avoid custom per-agent variants unless operationally required.
