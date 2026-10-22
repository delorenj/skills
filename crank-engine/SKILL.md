---
name: crank-engine
description: Run a crank beat over zellij Workspace tabs; act on stalls.
---

# Crank engine — one beat over the Workspace tabs

A beat is the operator's substitute attention: scan every crank-enabled tab, decide per pane, ACT (don't just report), and log. State persists across beats via `~/.local/state/zcrank/panes.json` + Redis.

## Safety contract (operator, 2026-10-18, extended same day)

- `waiting`, stale 0-1 → answer on his behalf: **momentum > perfection**. He said explicitly (GreenInBetween, 2026-10-21): "Don't hold on me" — never park a tab waiting for his sign-off if the agent can act or post one exact ask.
- `waiting`/`idle`/`agent_unknown`, stale ≥ 2 → **INTERROGATE** why: technical → restart it; question → weigh in for him; quality-check/browser/manual step → DO IT YOURSELF.
- `working` → leave alone unless looping (streak ≥ 4 → redirect).
- `shell` → NEVER type into it.

## Mechanics

1. Scan: `/home/delorenj/.hermes/profiles/33god-pm/scripts/zcrank-scan.sh` (wraps `~/.local/bin/zcrank.py`; emits tab|pane|state|stale|streak|flags + full 200-line response tails — READ THEM ALL, that context is the operator's eyes).
2. Verify waits before trusting them — two failure classes seen repeatedly:
   - **Wedged turn**: viewport hash frozen + ZERO CPU-tick growth (sample `/proc/<pid>/stat` fields 14+15 twice ~12s apart) + no writes under `~/.local/share/opencode/storage` (or `~/.claude`) for the turn window. A "working" spinner with 0 CPU and 0 bytes is DEAD.
   - **Phantom workflow wait**: pane says "Waiting for 1 dynamic workflow to finish" but the background chain/processes are alive and advancing (check chain logs, governor scripts) — the pane wait is cosmetic; do not touch.
        Verify liveness by CPU ticks AND storage writes AND pane-hash change together; any single signal can lie (a frozen viewport with ticking CPU was a healthy turn waiting on a slow subagent).
3. Pane input (per-tab terminal_N from scan): `env -u ZELLIJ -u ZELLIJ_SESSION_NAME zellij -s Workspace action write-chars -p <pane> '<msg>'` then `send-keys -p <pane> Enter`. Key syntax: `"Ctrl c"` (space, quoted as ONE arg) — `C-c` and unquoted `Ctrl c` both fail.
4. Abort a wedged turn: send `Esc` ONCE (arms "esc interrupt" indicator), wait, send `Esc` AGAIN to confirm — the abort then cascades through subagents; the input box returns minutes later. Text typed after the first Esc queues and submits on its own. Verify the new turn: fresh pane content, CPU ticking, storage writes resuming.
5. Verify every send: dump the pane after ~20s — the message must appear with ❯ prefix as a SENT line (in history), not sitting in the input box; footer clock advancing.
6. Log every tab (Redis is reliable; `zcrankctl log` hangs): `redis-cli RPUSH zcrank:log:<tab> '{"ts": "<UTC>", "state": "sent|working|skipped|restarted", "action": "<what+why>"}'` — one row per tab, including honest skips.

## Registry

`zcrankctl` (Redis SSOT): `zcrank:tab:<name>` hash {enabled}, `zcrank:pane:<tab>:<terminal>` overrides. Unlisted = OFF. Read `redis-cli LRANGE zcrank:log:<tab> -3 -1` for what previous beats did — never repeat an action a recent beat already took.

## Beat output

End the turn with a one-paragraph circuit summary: per tab, state → action → proof. Evidence over status.
