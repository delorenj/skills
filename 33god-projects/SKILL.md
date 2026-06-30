---
name: 33god-projects
description: |
  Create, wire, and maintain 33god/DeLoNET projects. Covers pjangler/CommonProject bootstrap, Hermes PM and scrum-master/Ticket Sentinel provisioning with inherited profile config, mandatory mise/.env.op wiring, BMAD, Hindsight/Bloodbank hooks, and shared Hermes fleet updates. Use when running `pjangler init`, `pjangler hermes-agent`, or `mise run init-project`; adding a PM or ticket sentinel; updating Hermes for the fleet; changing the fleet default model/config; touching hermes-agent-template or pjangler provisioning; wiring mise/op inject; installing BMAD; configuring agent hooks; or wiring the per-dev, committed project-scoped hook + skill fan-out so teammates and every agent CLI (Claude/Codex/Hermes/Kimi) inherit the same hooks and skills. Keywords: pjangler, CommonProject, hermes-agent-template, .project.json, Ticket Sentinel, inherited profile config, Hermes update, BMAD, Hindsight, Bloodbank, project-scoped hooks, skill fan-out, .agents/local.json, defer_to_global, hindsight-setup, hooks.master.json.
pipeline-status:
  - new
---

# 33god Project Creation & Wiring

Every 33god/DeLoNET repo is assembled by **pjangler** (the installed deployer CLI) out of
two copier templates it vendors as submodules under `~/code/pjangler/templates/`:

- **CommonProject** (`templates/commonproject`) — the base skeleton: `.project.json`,
  `mise.toml`, `.mise/scripts/`, BMAD, the ticket board.
- **hermes-agent-template** (`templates/hermes-agent`) — Hermes agent roles (PM,
  scrum-master/Ticket Sentinel, dev, …) provisioned into `agents/hermes/<role>/`.

`.project.json` at the repo root is the **single source of truth** for project + board
identity. There is **one ticket board per repo**; every agent binds to it.

## Operating Principles

- **`.project.json` is canonical.** Board binding (`ticket_provider` block), `repo_path`,
  `project_slug`, and the `agents` map live there. Never reintroduce a separate `.plane.json`.
- **One board per repo.** The PM owns it; the Scrum Master sentinel watches the same board.
  Board name = the project name (no role suffix); identifier = `slug[:4]` uppercased.
- **Agent config is inherited by default for new fleet agents.** pjangler creates
  `~/.hermes/profiles/<repo>-<role>` as a named profile that points at the
  role's `agents/hermes/<role>/runtime/` repo and opts `config.yaml` into
  inheriting from the fleet default profile. Local agent `config.yaml` files
  contain only overrides, such as `terminal.cwd`; `.env`, SOUL, memories,
  sessions, skills, gateway state, cron, and runtime files stay local.
- **mise is mandatory and uniform.** Every repo gets the same `mise.toml` contract (below).
- **Agents are memory- and event-wired by default.** Hindsight recall/retain + Bloodbank
  emit/consume are part of provisioning, not an afterthought.
- **Hooks and skills fan out from the repo, per-dev.** A repo that adopts the project-scoped
  agent layer commits one hooks SSOT + one skill set and lets `mise enter/leave` install them
  into each dev's CLIs, so teammates inherit them with zero setup (see
  [references/project-scoped-hooks.md](references/project-scoped-hooks.md)). Reference impl: CAF.
- **Templates are version-locked.** pjangler runs the vendored submodule, not an ad-hoc
  checkout, unless `PJANGLER_HERMES_TEMPLATE` overrides it for template development.

## Route by intent

| You want to… | Read |
|---|---|
| Create a new project / bootstrap CommonProject / add a PM or Ticket Sentinel | [references/project-creation.md](references/project-creation.md) |
| Update shared Hermes, inherited config, or future-agent template defaults | [references/hermes-fleet-updates.md](references/hermes-fleet-updates.md) |
| Set up or fix mise (mise.toml, .mise/scripts, AGENTS.md linking, `op inject .env.op`) | [references/mise-conventions.md](references/mise-conventions.md) |
| Install / re-install BMAD with the standard modules + tools | [references/bmad-init.md](references/bmad-init.md) |
| Wire an agent's Hindsight memory and Bloodbank emit/consume hooks (harness/global layer) | [references/agent-hooks.md](references/agent-hooks.md) |
| Wire the **per-dev, committed** project-scoped hook + skill fan-out (Claude/Codex/Hermes/Kimi, `.agents/local.json` opt-out, `hindsight-setup`) — adoption checklist, then per-CLI dialect mechanics | [references/project-scoped-hooks.md](references/project-scoped-hooks.md) → [references/project-scoped-internals.md](references/project-scoped-internals.md) |

Read only the topic you need. Most tasks touch exactly one.

## The standard lifecycle (at a glance)

```
1. CommonProject  →  mise run init-project        # repo skeleton + Plane board + .project.json + BMAD
2. pjangler hermes-agent (role: pm, +companion)   # PM agent, inherited profile, repo board
   └─ companion provisions the scrum-master (Ticket Sentinel) on the SAME board
3. mise trust && direnv-style `enter`             # links AGENTS.md, op-injects .env.op → .env
```

Steps 1–2 are detailed in [references/project-creation.md](references/project-creation.md);
the mise `enter` behavior in [references/mise-conventions.md](references/mise-conventions.md).

## Cross-cutting rules (apply to every 33god repo)

- `AGENTS.md` is the source of truth; `CLAUDE.md` and `GEMINI.md` are symlinks to it
  (kept current by the `link-agentfiles` mise task + a `watch_files` trigger).
- Secrets live in `.env.op` (1Password references); `mise` `enter` runs
  `op inject -i .env.op > .env`. Never commit `.env`; `.env.op` holds only `op://` refs.
- Shared non-secret Hermes settings live in the fleet default
  `~/.hermes/config.yaml`. New PM and scrum-master profiles inherit that config
  through `profile.yaml`:
  `config.inherit_from: default` and `config.save_mode: delta`. When the fleet
  default model changes, the repo agents follow automatically unless their local
  profile has an intentional override.
- No code changes in a hermes-managed repo without an active ticket on the repo board
  (`ALLOW_NO_TICKET=1` is the emergency bypass).
- Board creation is outward-facing (creates a real Plane/Linear/Trello board) — confirm
  before running provisioning that hits a live workspace.

## Out of scope

- **Developing pjangler itself** (new Commands/Recipes, the Command/Recipe pattern) →
  the `pjangler-dev` skill in the pjangler repo (`~/code/pjangler/skills/pjangler-dev`).
- **General DeLoNET host conventions** (paths, zshyzsh, Docker/Traefik, vault) →
  `delonet-conventions`.
- **Hindsight API usage / bank routing mechanics** (beyond the agent-hook wiring) →
  the `hindsight` skill.
- **Hermes PM template governance / propagating rules to existing agents** →
  `hermes-pm-template-maintenance`.
- **BMAD workflow execution** (PRD, stories, dev-story, sprint) → the `bmad-*` skills/agents.
- **Migrating a stale/split-brain repo** (e.g. an old PM board + separate SM board) is a
  deliberate manual reconciliation, not covered by the standard recipe.
