# BMAD Initialization (default for every project)

Every 33god project ships with BMAD installed. CommonProject's `init-project.sh` installs it
automatically as the final bootstrap step; the same command re-installs/repairs it.

## Standard install

```bash
npx -y bmad-method@latest install \
  --yes \
  --directory "$OUTPUT_DIR" \
  --modules "${BMAD_MODULES:-bmm,bmb,cis}" \
  --tools   "${BMAD_TOOLS:-claude-code,codex,gemini,opencode,crush,auggie}" \
  --user-name "${BMAD_USER_NAME:-Jarad}" \
  --communication-language English \
  --document-output-language English
```

- **Modules (default):** `bmm` (method), `bmb` (builder), `cis` (creative). Add `tea`/`gds`
  if a project needs them — override via `BMAD_MODULES`.
- **Tools (default):** all six CLI coders this ecosystem renders configs for —
  `claude-code, codex, gemini, opencode, crush, auggie`. Override via `BMAD_TOOLS`.
- `--yes` makes it fully non-interactive.

After install, CommonProject makes an empty initial commit `chore: install bmad-method`.

## What lands in the repo

- `_bmad/` — the methodology install (modules, config, agents, workflows).
- `_bmad-output/` — generated artifacts.
- BMAD agents/commands surface as `bmad-*` skills/slash-commands in the harness.

## When BMAD is missing

Per the global convention: if `_bmad` / `_bmad-output` are absent in a repo, initialize before
doing methodology work:

```bash
npx bmad-method@latest install --yes --modules bmm,bmb,cis \
  --tools claude-code,codex,gemini,opencode,crush,auggie --user-name Jarad
```

## Out of scope

Running BMAD *workflows* (PRD, create-story, dev-story, sprint-planning, retrospective, …) is
handled by the `bmad-*` skills/agents, not this hub. This topic covers **installation/parity
only**. Project-specific BMAD guardrails may exist as their own skills (e.g.
`drumjangler-project-bmad`).
