---
name: tflo-setup
description: Idempotent setup workflow for the tflo (Intelliforia Trello Flow) module. Validates env vars, fetches the initial Trello board snapshot, scaffolds the memory bank skeleton, auto-detects the bot user, and (optionally) updates the project's commit-msg hook to accept tflo-prefixed commits. Re-runnable for re-config.
---

# tflo-setup — Initialize the module

## Overview

One-shot (idempotent) setup that prepares the local environment so the orchestrator can run cleanly. Skips any step that's already in place. Designed to be safe to re-run.

## When to invoke

- First time using the tflo module on this machine
- After `_bmad/memory/tflo/` was wiped or moved
- After board structure changed (list rename, new label conventions)
- To re-fetch the board snapshot

## Capabilities

### Validate env

Check that these env vars are exported in the current shell:
- `TRELLO_API_KEY`
- `TRELLO_TOKEN`
- `TRELLO_BOARD_ID` (defaults to `jLl1NE0Z` for the Intelliforia board if unset, but report which board is being used)

If any are missing:
- Check `~/.config/zshyzsh/secrets.zsh` (per the user's convention)
- Check 1Password DeLoSecrets vault
- Surface to user with a precise instruction (export X, source Y)

### Auto-detect "me"

```bash
mise run tflo:whoami
```

Capture the member ID. Store in `_bmad/memory/tflo/index.md` and (optionally) update `_bmad/config.user.yaml` with `tflo_default_assignee_id`.

### Fetch board snapshot

```bash
mise run tflo:board-snapshot > _bmad/memory/tflo/board-snapshot.json
```

(Or the markdown form via the planned `board-snapshot.md` writer.) Caches list IDs, label IDs, and member IDs so workflows don't have to round-trip the API for static metadata.

Record `last_refreshed` timestamp. Refresh weekly or on-demand.

### Scaffold memory bank

Create the directory skeleton (idempotent):
```
_bmad/memory/tflo/
├── index.md
├── tickets/
└── daily/
```

Write a starter `index.md` with a brief description of the module + last_refreshed timestamp. Don't overwrite if it already exists (preserve hand-curated additions).

### Verify list-name configuration matches the board

After fetching the snapshot, compare configured list names (`tflo_triage_list`, `tflo_in_progress_list`, `tflo_review_list`, `tflo_done_list`) against actual board lists. Surface any mismatches as a config update prompt.

Default expectations (verified 2026-05-06):
- Triage: `To-Do`
- In-Progress: `In-Progress`
- Review: `In Review`
- Done: `Done`

### Optional: update commit-msg hook

Project's `.githooks/commit-msg` requires `[A-Z]{2,10}-[0-9]+|int-[0-9]+` in commit messages by default. tflo commits use `tflo({idShort}): summary`.

If the user opts in, append a regex alternative to the hook so `tflo({idShort})` passes natively without `ALLOW_NO_TICKET=1`.

This step is **opt-in only** because it has cross-project blast radius — every other commit on the repo is also subject to the hook. Default behavior: skip. Document the workaround (`ALLOW_NO_TICKET=1 git commit ...`) in the user's runbook.

### Report

Print a summary:
- Auth status (✓ / ✗)
- Board snapshot status (✓ / outdated)
- Memory bank status (✓ / scaffolded)
- List name match status (✓ / mismatch with details)
- Hook status (✓ / opt-in deferred)
- Next action recommendation

## Failure modes

| Symptom | Action |
|---|---|
| Env vars missing | Specific export instruction; do not proceed silently |
| Trello API returns 401 | Token regeneration instructions |
| Board snapshot fetch fails | Network / rate-limit — retry with backoff once, then surface |
| Memory bank dir cannot be created | Permission / disk error — surface with full path |
| List names don't match board | Print exact mismatch, suggest the corrected config |

## Inputs

- (none) — reads from env, user config, and Trello API

## Outputs

- `_bmad/memory/tflo/index.md` (created if missing)
- `_bmad/memory/tflo/board-snapshot.{md,json}` (created or refreshed)
- (Optional) `_bmad/config.user.yaml` updated with auto-detected values
- (Optional) `.githooks/commit-msg` updated with tflo-aware regex
- Console report

## Handoff

After successful setup, the orchestrator is ready to be invoked. User runs `/tflo-agent-orchestrator` and uses `start` / `dry-run` / etc.
