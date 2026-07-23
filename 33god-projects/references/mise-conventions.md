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

## Common tasks

- `mise trust` — trust the repo's mise config (required once per repo/clone).
- `mise tasks` — list tasks. `mise run <task>` — run one.
- `mise run init-project` — (CommonProject) bootstrap a new project (see project-creation.md).
