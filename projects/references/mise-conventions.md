---
pipeline-status:
  - new
---
# mise Integration (every 33god repo)

mise is the mandatory, uniform tooling/env layer. Every repo carries the same contract:
a `mise.toml` and a `.mise/scripts/` directory, AGENTS.md→CLAUDE.md/GEMINI.md linking, and
1Password-injected env on directory enter.

## The standard `mise.toml`

CommonProject renders this (see `template/mise.toml.jinja`); keep new/edited repos in parity:

```toml
[env]
_.path = [".mise/scripts", "agents/hermes/pm"]   # repo scripts + PM hermes wrapper on PATH
_.file = [".env"]                                 # load .env (produced by op inject, below)

[hooks]
enter = [
  "{{config_root}}/.mise/scripts/link-agentfiles.sh",   # refresh AGENTS.md symlinks
  "op inject -i .env.op > .env",                        # materialize secrets from 1Password
]

[[watch_files]]
patterns = ["AGENTS.md"]
task = "link-agentfiles"

[tasks.link-agentfiles]
description = "Symlink all agent files to AGENTS.md"
run = "{{config_root}}/.mise/scripts/link-agentfiles.sh"
```

Notes:
- `{{config_root}}` is rendered to the repo root at copier time; in a live (non-template)
  `mise.toml` it is mise's built-in template var — leave it literal.
- Repos may add `[tools]` (node/python/go/…) — **everything that can be mise-managed must be**.
- pjangler's own `mise.toml` is the dev variant (adds `.venv` + `CODEX_HOME`); it does not
  op-inject because it has no `.env.op`. The CommonProject contract above is the project standard.

## AGENTS.md is the single source; CLAUDE.md / GEMINI.md are symlinks

`.mise/scripts/link-agentfiles.sh`:
```bash
#!/bin/bash
if [ -f AGENTS.md ]; then
  ln -sf AGENTS.md CLAUDE.md
  ln -sf AGENTS.md GEMINI.md
  echo "✅ AI agent symlinks verified"
else
  echo "No AGENTS.md file found. Can't symlink."
fi
```
Runs on `enter` and whenever `AGENTS.md` changes (the `watch_files` trigger). Edit
`AGENTS.md` only; never edit `CLAUDE.md`/`GEMINI.md` directly.

## Secrets: `.env.op` → `op inject` → `.env`

- `.env.op` is committed and holds **only 1Password references**, e.g.
  `PLANE_33GOD_API_KEY=op://DeLoSecrets/Plane33God/api_key`.
- On directory enter, mise runs `op inject -i .env.op > .env`, materializing real values into
  `.env` (gitignored). `_.file = [".env"]` then loads them into the environment.
- This auto-overrides env vars on every enter, so rotated secrets propagate without manual steps.
- **Never commit `.env`.** Ensure `.gitignore` excludes `.env`, `.env.*` (but keep `.env.op`).
  See [[shell-snapshot-secret-leak-recurrence]] for the burn procedure if a secret leaks.

## Agent-hooks / skill fan-out additions (adopted layer, not yet in base template)

A repo that adopts the project-scoped agent layer (see
[project-scoped-hooks.md](project-scoped-hooks.md)) extends the mise contract — these are
**additive** to the standard block above, currently hand-adopted from CAF (not yet rendered by
CommonProject):

```toml
# NOTE: hooks are an array of [[hooks.enter]] tables (NOT enter = [ ... ]).
[[hooks.enter]]
script = "'{{config_root}}/.mise/scripts/link-agentfiles.sh'"
[[hooks.enter]]
# packs[] -> .agents/skills/ (resolve + verify; transactional)
script = "python3 '{{config_root}}/.mise/scripts/provision-packs.py'"
[[hooks.enter]]
# .agents/skills.json (packs[] + skills[]) -> the six supported local CLI skill dirs
script = "python3 '{{config_root}}/.mise/scripts/sync-skills.py' --scope project"
[[hooks.enter]]
script = "'{{config_root}}/.agents/hooks/sync.py' --install --quiet"   # hooks SSOT -> claude/codex/hermes
[[hooks.leave]]
script = "'{{config_root}}/.agents/hooks/sync.py' --uninstall --quiet"

[[watch_files]]
patterns = [".agents/skills.json"]               # re-provision + re-fan-out on manifest change
task = "skills-sync"
[[watch_files]]
patterns = [".agents/hooks/hooks.master.json"]   # re-fan-out on SSOT change
task = "hooks-sync"

[tasks.skills-provision-packs]
description = "Provision every Skillex pack declared in .agents/skills.json"
run = "python3 '{{config_root}}/.mise/scripts/provision-packs.py'"

[tasks.skills-sync]
description = "Sync skills from manifest to local CLI dirs"
depends = ["skills-provision-packs"]             # provision ALWAYS runs before sync
run = "python3 '{{config_root}}/.mise/scripts/sync-skills.py' --scope project"

# other tasks: hooks-sync, hooks-check (CI drift gate), hooks-uninstall,
#              hindsight-setup (op-inject the shared Hindsight key into .env)
```

`skills-provision-packs` replaces the retired `skills-provision-bmad` task, and
`.mise/scripts/provision-packs.py` replaces `provision-bmad-skills.py`. `pj audit` reports either
legacy name; `pj migrate` writes the new script and removes the old one. Pack mechanics
(`packs[]`, `pack.toml`, `SHA256SUMS`, sealing) → **`agent-config-fanout`** →
`references/skill-packs.md`.

`enter`/`leave` hook commands must never hard-fail the shell (the engine exits 0 on internal
error); only `hooks-check` returns nonzero, for CI. `.gitignore` must add `.agents/local.json`
(per-dev opt-out) and `.kimi-code/` (generated mirror) alongside `.env`.

## Common tasks

- `mise trust` — trust the repo's mise config (required once per repo/clone).
- `mise tasks` — list tasks. `mise run <task>` — run one.
- `mise run init-project` — (CommonProject) bootstrap a new project (see project-creation.md).
- `mise run hooks-sync` / `hooks-check` / `skills-sync` / `hindsight-setup` — (adopted layer)
  fan out the hooks SSOT + skills manifest; gate drift; provision the Hindsight key.
