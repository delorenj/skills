---
name: delodocs-vault-pipeline
description: Understand, diagnose, and repair the DeLoDocs vault automation pipeline (Inbox triage, cleanup, watchdog, router, wiki curator). Use when the Inbox is not draining, the router has stopped moving files, the watchdog is failing, or you need to understand how the vault's automated knowledge pipeline works.
pipeline-status:
  - new
---

# DeLoDocs Vault Automation Pipeline

## Pipeline Architecture

The vault runs a three-stage Inbox triage pipeline plus downstream wiki passes:

```
Inbox/  →  cleanup (timer, 10m)  →  watchdog (service) + Hermes enrichment
        →  router (timer, 10m)   →  {Category}/_triage/{file}.md
                                  →  (no secondary pass — known gap)
```

### Stage 1: Cleanup — `delodocs-inbox-cleanup.timer`

Script: `_vault/scripts/inbox_cleanup.py`

Deletes deterministic junk (sync-conflicts, empty files, duplicates).
Uploads non-markdown attachments to MinIO. Runs first, before enrichment.

### Stage 2: Watchdog + Enrichment — `delodocs-inbox-watchdog.service`

Script: `_vault/scripts/inbox_watchdog.py`
Prompt: `_vault/Workflows/prompts/inbox-frontmatter-watchdog.md`

Continuous poller. Spots new/changed `.md` files in `Inbox/` recursively.
Waits 20s for file stability, then wakes Delodocs PM Hermes profile with
a manifest. Hermes adds YAML frontmatter (source, captured, category,
tags, route-path, route-confidence) and sets `pipeline-status: [ready]`.

State: `~/.local/state/delodocs/inbox-watchdog/state.json`

### Stage 3: Router — `delodocs-inbox-router.timer`

Script: `_vault/scripts/inbox_router.py`

Deterministic mover. Scans for `pipeline-status: [ready]` +
`route-confidence: high` + valid `route-path`. Moves files to destination.
Holds files that don't qualify with reason logged.

State: `~/.local/state/delodocs/inbox-router/state.json`
Logs: `_vault/Workflows/logs/inbox-router-YYYY-MM.md`

### Downstream

- `delodocs-wiki-curator-daily.timer` — reviews routed notes for wiki growth
- `delodocs-wiki-self-tuning-weekly.timer` — routing quality review

## Diagnostic Playbook

When the pipeline appears stalled:

### 1. Check service status

```bash
systemctl --user is-active delodocs-inbox-watchdog.service
systemctl --user is-active delodocs-inbox-router.timer
systemctl --user is-active delodocs-inbox-cleanup.timer
```

### 2. Check watchdog journal for errors

```bash
journalctl --user -u delodocs-inbox-watchdog.service --no-pager -n 80
```

Key patterns and what they mean:

| Pattern | Meaning |
|---|---|
| `"no ready files"` | Normal — nothing to do right now |
| `"hermes failed: exit=1"` | Hermes enrichment is failing |
| `FileNotFoundError` for hermes | Wrong binary path in service file |

### 3. Check router logs

```bash
cat _vault/Workflows/logs/inbox-router-YYYY-MM.md
```

Held reasons and what they mean:

| Reason | Meaning |
|---|---|
| `pipeline-status is new` | Enrichment never ran on this file |
| `pipeline-status is hitl` | Needs human decision on category |
| `category X maps to Y, not route-path Z` | Frontmatter inconsistency |

### 4. Check watchdog state for failed files

```bash
cat ~/.local/state/delodocs/inbox-watchdog/state.json
```

Look for `"status": "failed"` entries. The `"last_error"` field shows the
Hermes error. Files with `"attempts": 3` and `"status": "failed"` are
abandoned — they need manual reset after fixing the root cause.

### 5. Count stuck Inbox files

```bash
grep -rl "pipeline-status:" Inbox/ | xargs grep -l "new" | wc -l
```

### 6. Count files held in router

```bash
python3 -c "
import json
state = json.load(open('$HOME/.local/state/delodocs/inbox-router/state.json'))
held = sum(1 for f in state.get('files',{}).values() if f.get('status')=='held')
print(held)
"
```

## Common Failure Modes

### Model/provider deprecated

**Symptom:** `"hermes failed: exit=1"` repeatedly; `last_error` contains
"model is not supported" or "Error code: 400".

**Root cause:** The watchdog unit file hardcodes `HERMES_PROVIDER` and
`HERMES_MODEL` environment variables. When the provider deprecates the
model, all enrichment calls fail silently (watchdog loops, router holds).

**Fix:**
1. Update the env vars in `_vault/Workflows/systemd/delodocs-inbox-watchdog.service`
2. Reinstall: `install -Dm644 _vault/Workflows/systemd/delodocs-inbox-watchdog.service ~/.config/systemd/user/delodocs-inbox-watchdog.service`
3. Reload + restart: `systemctl --user daemon-reload && systemctl --user restart delodocs-inbox-watchdog`
4. Reset failed files in watchdog state.json (delete entries or set attempts to 0)

### Hermes binary path wrong

**Symptom:** `FileNotFoundError` for hermes binary, service crash.

**Fix:** Update `HERMES_BIN` in the unit file to the output of `which hermes`.

### Files stuck after enrichment fix

After fixing the model, files with `"attempts": 3, "status": "failed"` won't
retry automatically. Options:
- Delete those entries from `state.json` to force re-baseline
- Set `"attempts"` to 0
- Run a one-shot backfill: `python3 _vault/scripts/inbox_watchdog.py --vault "$PWD" --scan-existing --once`

### _triage folders accumulating (no secondary pass)

Known gap: the pipeline routes to `{Category}/_triage/` but nothing moves
files from `_triage/` to their final home. Solution: a secondary triage
Hermes job scanning `_triage/` directories and routing to final destinations.

## Key File Paths

| Path | Purpose |
|---|---|
| `_vault/Workflows/systemd/delodocs-inbox-watchdog.service` | Watchdog unit |
| `_vault/Workflows/systemd/delodocs-inbox-router.service` | Router unit |
| `_vault/Workflows/systemd/delodocs-inbox-router.timer` | Router timer |
| `_vault/scripts/inbox_watchdog.py` | Watchdog script |
| `_vault/scripts/inbox_router.py` | Router script |
| `_vault/scripts/inbox_cleanup.py` | Cleanup script |
| `_vault/Workflows/prompts/inbox-frontmatter-watchdog.md` | Enrichment prompt |
| `~/.local/state/delodocs/inbox-watchdog/state.json` | Watchdog state |
| `~/.local/state/delodocs/inbox-router/state.json` | Router state |
| `_vault/Workflows/logs/inbox-router-YYYY-MM.md` | Router move log |
