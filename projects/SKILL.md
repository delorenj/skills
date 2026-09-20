---
name: 33god-projects
description: |
  Create, wire, and maintain 33god/DeLoNET projects. Covers PJangler/CommonProject bootstrap, repo-local `.project.json`, what the project side asks Flume to provision, mise/.env.op, BMAD, Hindsight/Bloodbank hook wiring, and project-scoped hook + skill fan-out adoption. Use when running `pj init`, `pj describe`, `pj audit`, or `pj migrate`; asking for a PM on a repo; wiring mise/op inject; installing BMAD; configuring hooks; or adopting `.agents/local.json`, `defer_to_global`, and `hooks.master.json`. Do NOT use for developing pjangler (project-jangler), generic fan-out mechanics (agent-config-fanout), hiring/onboarding/reviewing employees (agent-fleet-operations), live Plane issues, Bloodbank schemas, or host conventions.
---

# 33god Project Creation & Wiring

Every 33god/DeLoNET repo is assembled by **pjangler** out of one copier template it vendors as a submodule at `~/code/33GOD/pjangler/templates/commonproject` — the base skeleton: `.project.json`, `mise.toml`, `.mise/scripts/`, BMAD, the ticket board.

The **PM** that works the repo is a separate concern with its own tool. `flume hire pm` renders `agents/hermes/pm/` from Flume's `templates/hermes-agent` and writes the org-chart row; pjangler only projects the result back into `.project.json`. → **agent-fleet-operations**.

`.project.json` at the repo root is the **single source of truth** for project + board identity. There is **one ticket board per repo**; every agent binds to it.

## Operating Principles

- **`.project.json` is canonical for the project.** Board binding
  (`ticket_provider` block), `repo_path` and `project_slug` are authored there.
  Plane bindings require `state: linked` plus a live identifier/board id; never
  persist `ticket_provider.board_url` or reintroduce a separate `.plane.json`.
- **`agents` is a projection, not a record.** The org chart in
  `~/.hermes/agents-registry.yaml` owns who works here; `.project.json.agents`
  is the one-way `agent_role_directory` projection of it declared in the
  handbook's `projections:` block (`writable_by: project-registry`). `pj init`
  carries an existing entry forward and never authors one.
- **One board per repo.** The PM owns it. Board name = the project name (no role suffix); identifier = `slug[:4]` uppercased.
- **Agent config uses generated base-plus-delta state.** `flume hire` creates a
  real `~/.hermes/profiles/<repo>-pm/` directory. Its generated `config.yaml`
  merges the fleet base with its real, override-only `config.delta.yaml`;
  repo-local `agents/hermes/pm/runtime/` is ignored local state, not a profile
  symlink or nested runtime repository.
- **mise is mandatory and uniform.** Every repo gets the same `mise.toml` contract.
- **Repository ignores stay small and portable.** CommonProject preserves an
  existing `.gitignore` and adds only repo-owned secret/local-projection rules.
  Machine-wide backup, editor, and client-CLI patterns stay in the effective
  global ignore; `.agents/` is the only canonical agent-config tree in Git.
- **Agents are memory- and event-wired by default.** Hindsight recall/retain + Bloodbank emit/consume are part of provisioning. Machine-global Hindsight scripts live in one folder (`~/.agents/hooks/hindsight`), and machine-global Bloodbank lifecycle hooks invoke one publisher (`~/.agents/hooks/bloodbank/publish.py --client <agent> --hook <event>`).
- **Hooks and skills fan out from the repo, per-dev.** A repo that adopts the project-scoped agent layer commits one hooks SSOT + one skill manifest (`.agents/skills.json`, declaring `packs[]` and/or `skills[]`) and lets `mise enter` run `provision-packs.py` then `sync-skills.py` to securely install them into each dev's six supported local CLIs (see [references/project-scoped-hooks.md](references/project-scoped-hooks.md); pack mechanics → **agent-config-fanout** `references/skill-packs.md`).
- **Templates are version-locked.** pjangler runs its vendored `templates/commonproject` submodule; the employee template is version-locked inside Flume.

## Route by intent

| You want to… | Read |
|---|---|
| Create a new project / bootstrap CommonProject | [references/project-creation.md](references/project-creation.md) |
| Set up or fix mise (mise.toml, .mise/scripts, AGENTS.md linking, `op inject .env.op`) | [references/mise-conventions.md](references/mise-conventions.md) |
| Install / re-install BMAD with the standard modules + tools | [references/bmad-init.md](references/bmad-init.md) |
| Wire an agent's Hindsight memory and Bloodbank emit/consume hooks (harness/global layer) | [references/agent-hooks.md](references/agent-hooks.md) |
| Adopt the per-dev, committed project-scoped hook + skill fan-out layer (Claude/Codex/Hermes/Kimi, `.agents/local.json` opt-out, `hindsight-setup`) | [references/project-scoped-hooks.md](references/project-scoped-hooks.md) → [references/project-scoped-internals.md](references/project-scoped-internals.md) |
| Understand what the project side asks Flume to provision | [references/hermes-project-agent-request.md](references/hermes-project-agent-request.md) |
| Hire/onboard a PM, review the workforce, update shared Hermes fleet defaults, or backfill existing agents | → **agent-fleet-operations** |
| Build or operate the generic master→multi-dialect fan-out engine | → **agent-config-fanout** |
| Simplify `.gitignore` or reconcile files already tracked despite the effective ignore stack | → **gitignore-maintenance** |
| Develop pjangler itself (Commands/Recipes/MCP) | → **project-jangler** |

## The standard lifecycle (at a glance)

```
1. pj init --apply                                # .project.json + CommonProject scaffold + ticket board + BMAD + registry index
2. flume hire pm                                  # one PM, real profile, bound to the board step 1 created
3. mise trust && direnv-style `enter`             # links AGENTS.md, op-injects .env.op → .env
```

Two commands, two tools. pjangler owns the repo; Flume owns who works in it.

## Cross-cutting rules

- `AGENTS.md` is the source of truth; `CLAUDE.md` and `GEMINI.md` are symlinks to it.
- Secrets live in `.env.op` (1Password references); `mise enter` runs `op inject -i .env.op > .env`. Never commit `.env`.
- Client-specific roots such as `.claude/` and `.codex/` are generated local
  projections, not canonical project state. Never add repo unignore rules for
  them; edit `.agents/` and regenerate.
- No code changes in a hermes-managed repo without an active ticket on the repo board (`ALLOW_NO_TICKET=1` is the emergency bypass).
- **Do not run `sot.project-json` migration from a Git worktree.** The current
  migration derives `repo_path` and `project_slug` from `targetDir`; a worktree
  therefore rewrites both to the worktree path/branch slug and may canonicalize
  away provider metadata. Run it only against the canonical checkout, inspect
  the full `.project.json` diff, and deliberately transplant a reviewed result
  to a branch if the canonical checkout cannot be committed directly.
- Board creation is outward-facing — confirm before running provisioning that hits a live workspace.
- The board **schema** is a second live-workspace write, larger than creation:
  the `board.schema` parity rule applies states, labels, modules and project
  feature toggles via Pilot (`px schema import`). `pj audit` only ever reads
  (`--dry-run`); `pj migrate board.schema` writes. Two guarantees make the
  automated path safe, and both matter:
  - it **adds and aligns only** — `--prune` (which deletes) is never passed;
  - it **never moves the default state on a board that already holds tickets**,
    because Plane routes new work items there and moving it silently re-homes
    everything created afterwards. Such a change is reported as held back.

  A board pjangler creates carries Plane's bare defaults (five seeded states, no
  labels, no modules, `module_view`/`cycle_view` off), so without this step every
  new board needs ~10 minutes of clicking.
- Manifest mutation is transactional: malformed `.project.json` aborts
  byte-unchanged, and one lock spans read/validate/live board check-or-create
  through atomic replacement.
- Seal target/nested-repo, fleet-registry, profile, and systemd state before a
  hire; verify them directly afterward and require the rerun to converge. The
  full evidence contract is in **agent-fleet-operations**
  `references/pm-deployment.md`.

## Out of Scope

- **Developing pjangler itself** → `project-jangler`.
- **Generic agent-config fan-out engine** (master/lock/dialect renderers) → `agent-config-fanout`.
- **Hiring, onboarding, reviews, fleet-wide updates, template backfills, fleet self-checks** → `agent-fleet-operations`.
- **Plane live issue operations** → `project-lifecycle`.
- **Bloodbank event schema naming / topology** → `bloodbank-integration`.
- **General DeLoNET host conventions** → `delonet-conventions`.
- **Gitignore simplification and tracked-ignored parity** → `gitignore-maintenance`.
- **Hindsight API usage / bank routing mechanics beyond agent-hook wiring** → `hindsight`.
- **BMAD workflow execution** (PRD, stories, dev-story, sprint) → the `bmad-*` skills/agents.
