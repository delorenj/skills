---
name: 33god
description: "Unified 33GOD master skill and router. Use for any 33GOD request: architecture context, project creation, task execution, coding workflow, service development, workflow generation, and platform-level orchestration. This skill routes to focused references/workflows/scripts for incremental discovery."
pipeline-status:
  - new
---

# 33GOD Master Router

This is the **single root skill** for 33GOD.

Load this file first, then follow the router below. Do not load every reference at once.

## 33GOD in 30 seconds

33GOD is an event-driven software factory:

1. **Holyfields** defines contracts
2. **Bloodbank** transports events/commands
3. **Candystore** persists history
4. **Holocene** provides observability
5. **Agents/services** consume events and act

If it didn’t emit an event, it didn’t happen.

## Router (Incremental Discovery)

Read exactly one target unless the task genuinely spans multiple concerns.

- **Start here for map + conventions** → `references/index.md`
- **New project / repo bootstrap** → `workflows/project-bootstrap-pjangler.md` (automated) or `references/project-creation.md` (concepts)
- **Task intake + execution flow** → `references/task-execution.md`
- **Coding delivery protocol** → `references/coding-workflow.md`
- **Create/register services** → `references/service-development.md`
- **Generate end-to-end workflows** → `references/workflow-generation.md`
- **Add/change/prune events or commands** → `references/event-command-lifecycle.md`
- **Add events Claude Code itself emits (agent.*)** → `references/claude-code-event-publishing.md`
- **Cross-component/platform orchestration** → `references/platform-lifecycle.md`
- **Infrastructure, deployment, external access** → `references/infrastructure-deployment.md`
- **GOD-doc behavior + drift policy** → `references/god-doc-policy.md`

## Deterministic Runbooks

Use these when you need low-variance execution:

- `workflows/project-bootstrap-pjangler.md` — **PREFERRED**: Automated project setup via pjangler
- `workflows/project-bootstrap.md` — Manual fallback for custom cases
- `workflows/task-intake.md`
- `workflows/coding-delivery.md`
- `workflows/event-contract-rollout.md`

## Deterministic Utility Scripts

- `scripts/skill_audit.py` — verify structure and required files
- `scripts/task_router_check.py` — validate router targets in `SKILL.md`

## Non-Negotiables

1. Schema-first contracts before producer/consumer code.
2. Events are immutable facts; commands are mutable requests.
3. Ticketed work only; no rogue implementation.
4. Keep GOD docs aligned with actual architecture.
5. Prefer incremental loading over giant context dumps.
