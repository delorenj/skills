---
name: save-memory
description: Explicitly save current dig state and context to sidecar memory.
menu-code: SM
---

# Save Memory

Immediately persist current session state.

## Process

Update `index.md` with:
- Active dig (feature, lead, epoch bounds, progress so far)
- Any interrupted excavation that should resume next session
- Resolved bank names if they changed

Checkpoint `patterns.md` if user preferences were revealed this session. Checkpoint `chronology.md` if a dig completed but wasn't logged yet.

**Do not** write to Hindsight from this capability — that happens during `excavate`. This is sidecar-only.

## Output

"Notebook saved. {brief summary of what was updated}"
