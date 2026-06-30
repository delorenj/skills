---
pipeline-status:
  - new
---
# Project-scoped agent hooks & skill fan-out (per-dev, committed)

The layer that gives **every dev who clones the repo** — and each of their agent CLIs
(Claude Code, Codex, Hermes, Kimi) — the *same* hooks and skills, without anyone hand-wiring
their machine. It is **committed to the repo** and driven by `mise enter/leave`.

> **Status:** pioneered and live in **CoachingAgentFramework**
> (`~/code/CoachingAgentFramework/.agents/hooks/` + `.mise/scripts/`), which is the **reference
> implementation**. It is **not yet in the CommonProject template** — adopt it per-repo with the
> checklist below. The deep per-CLI dialect mechanics (guard wrapper, `mise enter/leave`,
> `defer_to_global`, the Codex/Hermes/Kimi specifics) live alongside this file in
> [project-scoped-internals.md](project-scoped-internals.md). The generic master→dialect fan-out
> engine these are built on — and templatizing this layer into CommonProject/pjangler — lives in
> the **`pjangler-dev`** skill (`references/ssot-fanout-engine.md`, the `AgentHooksRecipe`
> follow-up).

This is the per-dev, committed *fan-out* of the same Hindsight hooks described in
[agent-hooks.md](agent-hooks.md) — that file covers the harness/global Hindsight+Bloodbank
wiring; this one covers shipping them to teammates and to each CLI dialect.

## Two SSOTs in a project's agent layer

| SSOT (hand-edited) | Fans out to | Engine |
|---|---|---|
| `.agents/hooks/hooks.master.json` | Claude (committed settings) · Codex (injected) · Hermes (adapter) | `.agents/hooks/sync.py` |
| `.agents/skills/` (committed inherited skills + on-enter `./skills/*` app-skill links) | Codex `~/.codex/skills` · Kimi `./.kimi-code/skills` | `.mise/scripts/link-project-skills-to-clis.sh` |

Both follow the same rules: **one source → generated per-CLI dialects, idempotent (zero bytes
when unchanged), reversible, with a per-dev `.agents/local.json` opt-out.** Never hand-edit a
generated config; edit the SSOT and re-run.

## How each agent gets wired (hooks)

| Agent | Target | Scope | When |
|---|---|---|---|
| Claude Code | committed `.claude/settings.json` `hooks` (uses `$CLAUDE_PROJECT_DIR`) | project, committed | nothing to do — every clone has it |
| Codex | `~/.codex/hooks.json` (absolute-path entries, marker = repo path) | per-user, injected | `enter` injects, `leave` removes, `*.caf-bak` |
| Hermes | runtime `config.yaml` `hooks:` + `shell-hooks-allowlist.json`, via an **adapter** | per-deployment | `enter` merges (pyyaml, idempotent, backed up) |

Hermes runs hooks `shell=False` with the payload on stdin and has no user-prompt event, so it
uses an **adapter** (`.agents/hooks/hermes/hindsight-hook.sh <event>`) that translates the
payload and **pins the bank** (bank-resolve from the runtime cwd hits the PM submodule, not the
repo). Claude's committed command is a **guard wrapper**
(`lib/hook-guard.sh <id> <real-hook>`) so a dev can disable even a committed hook at runtime.

## How skills fan out

`link-project-skills-to-clis.sh` fans `.agents/skills/*` to a `SKILL_TARGETS` table, each with a
scope: **global** (`~/.codex/skills` — link ours, never clobber foreign, unlink on leave) or
**local** (`./.kimi-code/skills` — a fully-managed project mirror; Kimi's real copies are
replaced with symlinks). Adding a CLI = one `dir|scope` line.

## Per-dev experience (this is the point)

- **A teammate** clones, `cd`s in, and their Claude/Codex/Hermes/Kimi get the project's hooks +
  curated skills automatically. They configure nothing.
- **You (running a machine-global `~/.agents` system)** add a gitignored `.agents/local.json`:
  - `skills.defer_to_global: true` → the linker skips (and yields the CLI slot for) any project
    skill that also exists in your global `~/.agents/skills`, so your global copy wins — **zero
    duplicates/conflicts**. Teammates omit it and inherit the full set.
  - `hooks.disabled_agents: ["codex"]` (or `CAF_HOOKS_SKIP_CODEX=1`) if you already run these
    hooks globally and don't want them firing twice.
  - `hooks.disabled` / `skills.disabled` for per-item opt-out.

This is the general answer to *"share a curated set with someone whose environment is a strict
superset of it."*

## Hindsight credentials

`mise run hindsight-setup` op-injects a shared, project-scoped Hindsight key from 1Password into
the gitignored `.env` (`HINDSIGHT_API_URL` + `HINDSIGHT_API_KEY`; env outranks
`~/.hindsight/config`). Hooks **no-op gracefully** without a key, so a teammate without access
isn't blocked.

## Adopting it in a repo (checklist)

1. Copy `.agents/hooks/` from CAF: `hooks.master.json`, `sync.py`, `lib/` (`local-config.sh`,
   `hook-guard.sh`), `hindsight/`, `hermes/hindsight-hook.sh`, `README.md`. Adjust the pinned
   bank in `hermes/hindsight-hook.sh` and any project-name references.
2. Copy `.mise/scripts/link-project-skills-to-clis.sh` + `unlink-project-skills-from-clis.sh`
   and `hindsight-setup.sh`. Copy `.agents/local.example.json`.
3. Wire `mise.toml` (see [mise-conventions.md](mise-conventions.md) → agent-hooks additions):
   `enter` runs the skill linker + `sync.py --install --quiet`; `leave` runs the unlinker +
   `sync.py --uninstall --quiet`; `watch_files` on `hooks.master.json` → `hooks-sync`; tasks
   `hooks-sync` / `hooks-check` (CI gate) / `hooks-uninstall` / `skills-relink` / `hindsight-setup`.
4. `.gitignore`: `.agents/local.json`, `.kimi-code/`, `.env`.
5. Run `mise run hooks-sync` and commit the generated `.claude/settings.json` alongside the master.
6. CI runs `mise run hooks-check` (fails on committed-Claude drift).
