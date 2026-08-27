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
> engine these are built on lives in the **`agent-config-fanout`** skill
> (`references/ssot-fanout-engine.md`, `references/ssot-fanout-reference.md`,
> `references/ssot-fanout-gotchas.md`). Templatizing this layer into CommonProject/pjangler stays
> in **`project-jangler`** only when the task requires editing pjangler implementation code.

This is the per-dev, committed *fan-out* of the same Hindsight hooks described in
[agent-hooks.md](agent-hooks.md) — that file covers the harness/global Hindsight+Bloodbank
wiring; this one covers shipping them to teammates and to each CLI dialect.

Do not vendor a Bloodbank publisher into this project-scoped layer. Bloodbank lifecycle
events are machine-global and generated from `~/code/33GOD/bloodbank/services/agent-hooks/`;
project configs should invoke `~/.agents/hooks/bloodbank/publish.py --client <agent> --hook <event>`.

## Two SSOTs in a project's agent layer

| SSOT (hand-edited) | Fans out to | Engine |
|---|---|---|
| `.agents/hooks/hooks.master.json` | Claude (committed settings) · Codex (injected) · Hermes (adapter) | `.agents/hooks/sync.py` |
| `.agents/skills.json` (project skill manifest — `packs[]` + `skills[]`) | The six supported agent CLI skill dirs in the project (`.claude/skills`, `.codex/skills`, `.gemini/skills`, `.copilot/skills`, `.opencode/skills`, `.kimi-code/skills`) | `provision-packs.py` then `sync-skills.py --scope project` |

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

Two scripts, always in this order — `skills-provision-packs` **then** `skills-sync` (the mise task
`skills-sync` `depends` on `skills-provision-packs`, and the `mise enter` hooks run in the same
order):

1. **`provision-packs.py`** resolves and verifies every entry in the manifest's `packs[]` and
   materializes each member into `.agents/skills/`. It is transactional: a failure at any point
   rolls the project back to its exact prior state.
2. **`sync-skills.py --scope project`** projects `packs[]` members **and** `skills[]` entries into
   the project's local agent CLI folders. Skills resolve from Git repositories or local project
   paths, with global skills cached in `~/.agents/.cache/skills`.

`inherit_global: true` pulls in the developer's global `skills.json` loadout out of the box;
project entries safely shadow global ones of the same name. Precedence, lowest to highest:
global `packs[]` → global `skills[]` → project `packs[]` → project `skills[]`. An explicit
`skills[]` entry always overrides a pack member of the same name.

**Exactly six agent CLIs are supported.** For `--scope project` the targets are `.claude/skills`,
`.codex/skills`, `.gemini/skills`, `.copilot/skills`, `.opencode/skills`, `.kimi-code/skills`
(global scope is identical except opencode, which is `~/.config/opencode/skills`).
`.augment/skills`, `.hermes/skills`, `.openclaw/skills`, `.kimi/skills`, `.crush/skills`, and
`.cursor/skills` are **RETIRED** — never written to. They are never auto-deleted either;
`sync-skills.py --prune-retired` opts in to removing only managed symlinks left behind in them.
`~/.hermes/skills` is a writable Hermes runtime **overlay**, not a projection of the manifest, and
is never touched.

Pack mechanics — `pack.toml`, `SHA256SUMS`, sealing, payload verification, version resolution,
`include`/`exclude` — live in **`agent-config-fanout`** → `references/skill-packs.md`.

## Per-dev experience (this is the point)

- **A teammate** clones, `cd`s in, and their Claude/Codex/Hermes/Kimi get the project's hooks +
  curated skills automatically. They configure nothing.
- **You (running a machine-global `~/.agents` system)** add a gitignored `.agents/local.json`:
  - `hooks.disabled_agents: ["codex"]` (or `CAF_HOOKS_SKIP_CODEX=1`) if you already run these
    hooks globally and don't want them firing twice.
  - `hooks.disabled` for per-item opt-out.
  *(Note: Skill duplication and inheritance is now managed safely by `sync-skills.py` via `inherit_global: true` in the project's `skills.json`.)*

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
2. Copy `hindsight-setup.sh` and `.agents/local.example.json`. Also ensure `.agents/skills.json` exists for your project's skill dependencies.
3. Wire `mise.toml` (see [mise-conventions.md](mise-conventions.md) → agent-hooks additions):
   `enter` runs `provision-packs.py`, then `sync-skills.py --scope project`, then
   `sync.py --install --quiet`; `leave` runs `sync.py --uninstall --quiet`; `watch_files` on
   `hooks.master.json` → `hooks-sync` and on `.agents/skills.json` → `skills-sync`; tasks
   `hooks-sync` / `hooks-check` (CI gate) / `hooks-uninstall` / `skills-provision-packs` /
   `skills-sync` (`depends = ["skills-provision-packs"]`) / `hindsight-setup`.
4. `.gitignore`: `.agents/local.json`, `.kimi-code/`, `.env`.
5. Run `mise run hooks-sync` and commit the generated `.claude/settings.json` alongside the master.
6. CI runs `mise run hooks-check` (fails on committed-Claude drift).
