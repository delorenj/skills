---
name: context-self-heal
description: Agent-local context guard and deterministic compaction workflow (GOD-13). Use when context usage is high, when wiring auto-compaction/restart schedules (via Candybar), or when deploying standardized context-monitor hooks across agents.
pipeline-status:
  - new
---

# Context Self-Heal (GOD-13)

## Purpose
Provide a reusable, non-agent-specific package for context monitoring and deterministic compaction artifacts.

## Files
- `files/god-13-context-monitor.sh`
- `files/god-13-lenoon-monitor.service`
- `files/candybar.toml` (Candybar manifest template; the `.timer` that used to ship here was retired)

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
1. Copy the script and the `.service` from `files/` to the target workspace.
2. Parameterize `AGENT_NAME` and workspace path.
3. Schedule it with Candybar, the single clock (`candybar` skill): fill in
   `files/candybar.toml` (runner `systemd` starting the `.service`, or `exec`
   with the script's argv), register it from `~/code/33GOD/candybar`, read the
   registration back, and prove one terminal invocation. Never add a `.timer`,
   a crontab line or an agent-side poll loop.
4. Verify artifact write + restart path on threshold breach.

## Notes
- Prefer Hindsight plugin as canonical memory; artifact is deterministic restart checkpoint.
- Avoid custom per-agent variants unless operationally required.
