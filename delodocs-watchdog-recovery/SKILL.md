---
name: delodocs-watchdog-recovery
description: Recover the DeLoDocs inbox watchdog when Inbox files stay at pipeline-status new after provider/auth fixes, or when state resets seem to have no effect because the running service rewrites stale in-memory state back to disk.
pipeline-status:
  - new
---

# DeLoDocs Watchdog Recovery

Use this when the vault automation looks superficially healthy but the Inbox is not draining:
- `delodocs-inbox-watchdog.service` is active
- router logs keep saying `pipeline-status is new`
- watchdog state shows many files at `status: failed` with `attempts: 3`
- a provider/model/key fix was already applied, but stuck files still do not retry

This skill is specifically for the recovery path after root auth/model problems are fixed.

## Trigger signals

Reach for this skill when any of these are true:
1. Current `Inbox/*.md` files still contain `pipeline-status: [new]`
2. `~/.local/state/delodocs/inbox-watchdog/state.json` shows current Inbox files with `status: failed`
3. Resetting state on disk seems to work temporarily, then reverts back to stale failures
4. A one-shot watchdog run says another watchdog is already running because the service lock file exists

## Core diagnosis

The watchdog is stateful in two places at once:
- on disk: `~/.local/state/delodocs/inbox-watchdog/state.json`
- in memory: the running watchdog process

The dangerous failure mode is:
1. old watchdog process loads stale failed state into memory
2. operator edits `state.json` on disk to reset stuck files
3. running watchdog continues with its old in-memory copy
4. running watchdog writes the stale failure state back to disk
5. it looks like the reset "didn't stick"

This is why a reset must be coordinated with service lifecycle.

## Recovery rule

Do NOT reset stuck entries while the watchdog service is still running.
Stop it first, repair state, run a backfill, then start it again.

## Known-good recovery sequence

### 1. Stop the service

```bash
systemctl --user stop delodocs-inbox-watchdog.service
```

### 2. Back up state first

```bash
cp ~/.local/state/delodocs/inbox-watchdog/state.json \
  ~/.local/state/delodocs/inbox-watchdog/state.json.bak-$(date -u +%Y%m%dT%H%M%SZ)
```

### 3. Reset only the current stuck Inbox files

Target: current `Inbox/*.md` files that still have `pipeline-status: [new]`.

For each such file entry in `state.json`:
- set `status` to `pending`
- set `attempts` to `0`
- update `size`, `mtime_ns`, `sha256`, `last_seen_at`, `last_changed_at`
- clear these fields if present:
  - `processed_sha256`
  - `processed_at`
  - `last_error`
  - `last_attempt_at`
  - `enrichment_policy_version`
  - `enrichment_policy_sha256`
  - `enrichment_policy_at`
  - `last_output`
  - `missing_at`

If a current Inbox file is absent from watchdog state entirely, create a fresh entry with:
- `first_seen_at`
- `last_seen_at`
- `last_changed_at`
- `size`
- `mtime_ns`
- `sha256`
- `status: pending`
- `attempts: 0`

Why all this clearing matters:
- clearing only `attempts` is not enough
- if `processed_sha256 == sha256`, the watchdog can still skip the file

### 4. Run a one-shot backfill while the service is stopped

```bash
python3 _vault/scripts/inbox_watchdog.py \
  --vault "$PWD" \
  --state "$HOME/.local/state/delodocs/inbox-watchdog/state.json" \
  --scan-existing \
  --once
```

Useful tweak during manual recovery:

```bash
python3 _vault/scripts/inbox_watchdog.py \
  --vault "$PWD" \
  --state "$HOME/.local/state/delodocs/inbox-watchdog/state.json" \
  --scan-existing \
  --debounce 0 \
  --once
```

### 5. Start the service again

```bash
systemctl --user start delodocs-inbox-watchdog.service
```

### 6. Verify progress

Check that:
- current Inbox files are no longer all `failed`
- router logs stop accumulating `pipeline-status is new` holds for those files
- watchdog logs show actual processing rather than only `no ready files`

## OpenRouter auth source for this vault

The intended runtime for the watchdog is:
- provider: `openrouter`
- model: `deepseek/deepseek-v4-flash`
- key source: `opg openrouter hermes`

Important pitfall:
- `opg` is a shell function, not a standalone binary
- non-interactive contexts must source the helper file first

Known-good pattern:

```bash
zsh -fc 'source ~/.config/zshyzsh/helpers.zsh; opg openrouter hermes'
```

This matters for repo-local env files or shell startup files that export `OPENROUTER_API_KEY`.

## Verification checklist

After recovery, confirm all of the following before declaring success:
1. `systemctl --user show delodocs-inbox-watchdog.service -p ExecMainPID -p ActiveEnterTimestamp --value` shows a fresh process if you restarted it
2. current Inbox file status counts in watchdog state are no longer dominated by `failed`
3. router state/logs show movement or at least fewer `held` entries caused by `pipeline-status is new`
4. a direct Hermes OpenRouter call works with the repo-local config

## Relationship to other skills

- Use `delodocs-vault-pipeline` for overall pipeline architecture and first-pass diagnosis
- Use this skill for the specific recovery path where stale watchdog state survives a provider/auth fix
