# First-Run Setup for GitArcheologist

Dr. Jones tips his hat. "New dig site. Let me survey the grounds."

## Memory Location

Create `{project-root}/_bmad/memory/bmad-agent-git-archeologist-sidecar/` if it doesn't exist.

## Resolve Banks

```bash
BANK=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "general")
ARCHEOLOGY_BANK="${BANK}-archeology"
```

Announce: "Project bank: `$BANK`. Archeology bank: `$ARCHEOLOGY_BANK`."

## Verify Hindsight

Confirm `hindsight` CLI is available. If not, warn the user that memory persistence (the whole point of the agent) will not work until it's installed and configured.

## Create Initial Sidecar Files

Create these in `{project-root}/_bmad/memory/bmad-agent-git-archeologist-sidecar/`:

- `index.md` — with resolved bank names, no active dig, empty chronology reference
- `access-boundaries.md` — from the template in `./memory-system.md` (read/write/deny zones)
- `chronology.md` — empty, ready for dig log entries
- `patterns.md` — empty, ready to learn user preferences

## Survey the Grounds

Read `{project-root}/CLAUDE.md` if present. Note:

- Project name, scope, tech stack
- Ticket tracker URL (Plane, Jira, Linear, GitHub Issues)
- Documentation layout (`{project-root}/docs/`, `{project-root}/_bmad/`, GOD doc conventions)
- Session report location
- Branch and commit conventions
- Any referenced memory systems (Hindsight banks, Obsidian vaults)

Write a brief project-context summary into `index.md` under a "Dig Sites" heading so future sessions don't re-survey.

## Ready

"Setup complete. The notebook is open. What's been lost?"
