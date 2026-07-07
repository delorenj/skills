---
name: hermes-fleet-operations
description: |
  Operate and maintain the Hermes agent fleet: shared install, ~/.hermes/fleet.env, ~/.hermes/config.yaml, ~/.hermes/agents-registry.yaml, hermes-agent-template, role profiles and inherited config, runtime repo provisioning, systemd user units, fleet self-checks, template defaults, and PM/template backfills. Use when updating Hermes core, changing fleet defaults, provisioning agents, debugging fleet-wide MCP failures, running a Hermes fleet self-check, or propagating template changes to existing PM agents. Triggers: Hermes fleet, hermes-agent-template, ~/.hermes/fleet.env, ~/.hermes/config.yaml, ~/.hermes/agents-registry.yaml, inherited profile, fleet self-check, systemd hermes-*, template backfill, runtime repo provisioning. Do NOT use for: project bootstrap decisions or repo-local agent requests (→ 33god-projects); Plane ticket operations (→ managing-tickets-and-tasks-in-plane); Bloodbank event contracts (→ bloodbank-integration); generic SSOT config fan-out mechanics (→ agent-config-fanout).
---

# Hermes Fleet Operations

Route here for anything that touches the shared Hermes fleet, the agent template, or the runtime provisioning contract — not the project that happens to host an agent.

## Operating Principles

- **Fleet truth lives in `~/.hermes/`.** `fleet.env`, `config.yaml`, and `agents-registry.yaml` are the shared sources; repo-local `agents/hermes/<role>/runtime/` contains only overrides and local state.
- **Inherited profiles keep fleet defaults automatic.** New PM/scrum-master agents inherit from the `default` profile with `save_mode: delta`. Change the fleet default once; do not backfill every runtime `config.yaml` for shared settings.
- **Template changes affect future agents; backfills affect existing ones.** Do not backfill for a simple shared default or core update.
- **One board owns the shared fleet/template contract.** Fleet-wide fixes route to the Hermes Agent PM board, not the repo board.
- **Project identity is owned by `33god-projects` / PJangler.** This skill provisions against that identity; it does not create or rename projects.

## Triage Table

| You want to… | Read first | Then |
|---|---|---|
| Update Hermes core, shared config, or future-agent provisioning | [references/hermes-fleet-updates.md](references/hermes-fleet-updates.md) | the matching lane inside it |
| Run a fleet self-check or debug MCP failures that differ across repo-backed daemons | [references/fleet-self-check.md](references/fleet-self-check.md) | hermes-fleet-updates for remediation lanes |
| Capture a governance rule/workflow in the PM template and propagate to existing PM agents | [references/pm-template-maintenance.md](references/pm-template-maintenance.md) | hermes-fleet-updates for backfill vs shared-config classification |
| Provision a new PM or scrum-master agent into a repo | → **33god-projects** `references/project-creation.md` | this skill only for runtime/template details |

## Cross-Cutting Rules

- `~/.hermes/profiles/<repo>-<role>` must point at `agents/hermes/<role>/runtime/`.
- `runtime/profile.yaml` must declare `config.inherit_from: default` and `config.save_mode: delta`.
- `runtime/config.yaml` stays override-only; do not duplicate fleet `mcp_servers` there.
- systemd units set `HERMES_HOME` to the named profile path, not the raw runtime path.
- For Bloodbank lifecycle events emitted by hooks, use v1 names (`bloodbank.v1.agent.*`).

## Out of Scope

- **Project bootstrap / repo-local agent requests** → `33god-projects`.
- **Plane ticket lifecycle** → `managing-tickets-and-tasks-in-plane`.
- **Bloodbank event schemas or naming contract** → `bloodbank-integration`.
- **Generic SSOT config fan-out engine mechanics** → `agent-config-fanout`.
