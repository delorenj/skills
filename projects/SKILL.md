---
name: 33god-projects
description: |
  Create, wire, and maintain 33god/DeLoNET projects. Covers PJangler/CommonProject bootstrap, repo-local `.project.json`, Hermes PM provisioning requests (sentinel duties fold into the PM heartbeat), mise/.env.op, BMAD, Hindsight/Bloodbank hook wiring, and project-scoped hook + skill fan-out adoption. Use when running `pj init`, `pj hermes-agent --yes`, or `mise run init-project`; adding a PM; wiring mise/op inject; installing BMAD; configuring hooks; or adopting `.agents/local.json`, `defer_to_global`, and `hooks.master.json`. Do NOT use for developing pjangler (project-jangler), generic fan-out mechanics (agent-config-fanout), fleet updates/backfills (agent-fleet-operations), live Plane issues, Bloodbank schemas, or host conventions.
---

# 33god Project Creation & Wiring

Every 33god/DeLoNET repo is assembled by **pjangler** out of two copier templates it vendors as submodules under `~/code/33GOD/pjangler/templates/`:

- **CommonProject** (`templates/commonproject`) — the base skeleton: `.project.json`, `mise.toml`, `.mise/scripts/`, BMAD, the ticket board.
- **hermes-agent-template** (`templates/hermes-agent`) — the Hermes **PM** role provisioned into `agents/hermes/pm/` (unified single-PM model — the retired scrum-master's sentinel duties run on the PM heartbeat).

`.project.json` at the repo root is the **single source of truth** for project + board identity. There is **one ticket board per repo**; every agent binds to it.

## Operating Principles

- **`.project.json` is canonical.** Board binding (`ticket_provider` block), `repo_path`, `project_slug`, and the `agents` map live there. Never reintroduce a separate `.plane.json`.
- **One board per repo.** The PM owns it; the sentinel pass on the PM's heartbeat watches the same board. Board name = the project name (no role suffix); identifier = `slug[:4]` uppercased.
- **Agent config uses generated base-plus-delta state.** PJangler creates a real
  `~/.hermes/profiles/<repo>-pm/` directory. Its generated `config.yaml` merges
  the fleet base with its real, override-only `config.delta.yaml`; repo-local
  `agents/hermes/pm/runtime/` is ignored local state, not a profile symlink or
  nested runtime repository.
- **mise is mandatory and uniform.** Every repo gets the same `mise.toml` contract.
- **Agents are memory- and event-wired by default.** Hindsight recall/retain + Bloodbank emit/consume are part of provisioning. Machine-global Hindsight scripts live in one folder (`~/.agents/hooks/hindsight`), and machine-global Bloodbank lifecycle hooks invoke one publisher (`~/.agents/hooks/bloodbank/publish.py --client <agent> --hook <event>`).
- **Hooks and skills fan out from the repo, per-dev.** A repo that adopts the project-scoped agent layer commits one hooks SSOT + one skill manifest (`.agents/skills.json`, declaring `packs[]` and/or `skills[]`) and lets `mise enter` run `provision-packs.py` then `sync-skills.py` to securely install them into each dev's six supported local CLIs (see [references/project-scoped-hooks.md](references/project-scoped-hooks.md); pack mechanics → **agent-config-fanout** `references/skill-packs.md`).
- **Templates are version-locked.** pjangler runs the vendored submodule unless `PJANGLER_HERMES_TEMPLATE` overrides it for template development.

## Route by intent

| You want to… | Read |
|---|---|
| Create a new project / bootstrap CommonProject / deploy the PM | [references/project-creation.md](references/project-creation.md) |
| Set up or fix mise (mise.toml, .mise/scripts, AGENTS.md linking, `op inject .env.op`) | [references/mise-conventions.md](references/mise-conventions.md) |
| Install / re-install BMAD with the standard modules + tools | [references/bmad-init.md](references/bmad-init.md) |
| Wire an agent's Hindsight memory and Bloodbank emit/consume hooks (harness/global layer) | [references/agent-hooks.md](references/agent-hooks.md) |
| Adopt the per-dev, committed project-scoped hook + skill fan-out layer (Claude/Codex/Hermes/Kimi, `.agents/local.json` opt-out, `hindsight-setup`) | [references/project-scoped-hooks.md](references/project-scoped-hooks.md) → [references/project-scoped-internals.md](references/project-scoped-internals.md) |
| Understand what the project side asks Hermes to provision | [references/hermes-project-agent-request.md](references/hermes-project-agent-request.md) |
| Update shared Hermes fleet defaults, run a fleet self-check, or backfill existing PM agents | → **agent-fleet-operations** |
| Build or operate the generic master→multi-dialect fan-out engine | → **agent-config-fanout** |
| Develop pjangler itself (Commands/Recipes/MCP) | → **project-jangler** |

## The standard lifecycle (at a glance)

```
1. CommonProject  →  mise run init-project        # repo skeleton + Plane board + .project.json + BMAD
2. pj hermes-agent --yes                          # one PM, real profile, repo board
   └─ sentinel duties ride the PM heartbeat timer (no separate scrum-master)
3. mise trust && direnv-style `enter`             # links AGENTS.md, op-injects .env.op → .env
```

## Cross-cutting rules

- `AGENTS.md` is the source of truth; `CLAUDE.md` and `GEMINI.md` are symlinks to it.
- Secrets live in `.env.op` (1Password references); `mise enter` runs `op inject -i .env.op > .env`. Never commit `.env`.
- No code changes in a hermes-managed repo without an active ticket on the repo board (`ALLOW_NO_TICKET=1` is the emergency bypass).
- Board creation is outward-facing — confirm before running provisioning that hits a live workspace.
- Seal target/nested-repo, fleet-registry, profile, and systemd state before a
  PM deploy; verify them directly afterward and require the rerun to converge.
  The full evidence contract is in **agent-fleet-operations**
  `references/pm-deployment.md`.

## Out of Scope

- **Developing pjangler itself** → `project-jangler`.
- **Generic agent-config fan-out engine** (master/lock/dialect renderers) → `agent-config-fanout`.
- **Hermes fleet-wide updates, template backfills, fleet self-checks** → `agent-fleet-operations`.
- **Plane live issue operations** → `project-lifecycle`.
- **Bloodbank event schema naming / topology** → `bloodbank-integration`.
- **General DeLoNET host conventions** → `delonet-conventions`.
- **Hindsight API usage / bank routing mechanics beyond agent-hook wiring** → `hindsight`.
- **BMAD workflow execution** (PRD, stories, dev-story, sprint) → the `bmad-*` skills/agents.
