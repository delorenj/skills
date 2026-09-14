---
name: systemd-agent-service-diagnostics
description: Diagnose long-running agent or automation services managed by systemd when the unit file looks correct but the live process still behaves as if an old provider, model, binary, or environment override is active.
pipeline-status:
  - new
---

# Systemd Agent Service Diagnostics

Use this when a systemd-managed agent service appears healthy (`active`) but the real behavior says otherwise: stale model/provider, wrong binary, old credentials, repeated task failures, or a backlog that does not drain.

## Trigger signals

- `systemctl --user is-active <service>` says `active` but jobs still fail
- the unit file on disk shows the expected env vars, but logs still mention an old model/provider
- router/downstream systems keep holding work because the upstream service never actually enriched or processed it
- restarting is potentially disruptive, so you need proof before asking for approval

## Core rule

Do not trust the unit file alone. Verify the live process environment.

A long-running systemd service can keep stale env until it is reloaded/restarted. `systemctl cat` tells you what is on disk; `/proc/<pid>/environ` tells you what is actually running.

## Diagnostic sequence

1. Confirm service state.
   - `systemctl --user is-active <service>`
   - `systemctl --user show <service> -p ExecMainPID -p ActiveEnterTimestamp -p FragmentPath -p Environment`

2. Inspect recent journal lines for the real failure shape.
   - `journalctl --user -u <service> --no-pager -n 120`
   - Look for provider/model errors, auth errors, repeated exit=1 loops, or “no ready files” after a failed attempt.

3. Read the live process environment.
   - `tr '\0' '\n' < /proc/<PID>/environ | grep -E '^(HERMES_|OBSIDIAN_|PYTHONUNBUFFERED|OPENROUTER_|ANTHROPIC_|OPENAI_)'`

4. Compare live env vs unit file.
   - especially binary path, provider, model, home/runtime path, and any provider-specific key or override variables

5. If the workload is stateful, inspect state files too.
   - determine whether failures are now abandoned rather than still retrying
   - look for `attempts: 3`, `status: failed`, stale `processed_sha256`, or similar “already handled” markers

## Common pitfall

If the unit file was corrected after the service started, the process may still be running with the old binary/model/provider.

Typical pattern:
- unit file now says “openrouter + deepseek/deepseek-v4-flash”
- live `/proc/<pid>/environ` still says “openai-codex + gpt-5.3-codex”
- journal still shows unsupported-model or auth failures from the old provider

In that case, the right conclusion is not “the unit file is wrong”; it is “the running service has not picked up the override yet.”

## Recovery pattern

After you prove the live env is stale:

1. Update/install the correct unit file if needed.
2. Ask for approval before restart if the project/operator requires it.
3. Reload and restart the service.
4. Re-check the live `/proc/<pid>/environ` after restart.
5. If the service uses state files and prior failures were abandoned, reset the stuck entries too.
6. Re-run a one-shot/backfill pass if the system supports it, then verify backlog movement.

## Verification

You are done only when all of the following are true:
- unit file shows the intended override
- live `/proc/<pid>/environ` matches it
- journal no longer shows the old provider/model failure
- stateful backlog items are retrying or draining again

## Support files

- `references/live-env-mismatch-and-provider-override.md` — concrete example of unit-file-vs-live-env mismatch and the checks to run
