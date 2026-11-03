---
name: crank-engine
description: Run a crank beat over zellij Workspace tabs; act on stalls.
---

# Crank engine — one beat over the Workspace tabs

A beat is the operator's substitute attention: scan every crank-enabled tab, decide per pane, ACT (don't just report), and log. State persists across beats via `~/.local/state/zcrank/panes.json` + Redis.

## Gate contract — hard-wake vs judgment

The zcrank-gate emits LLM-free attention keys (`poke`, `interrogate<N>`, `long<N>`, `burn<N>`); the beat must obey their class:

- `poke` / `interrogate<N>` — verify liveness (Mechanics step 2) before acting, then act per the safety contract below.
- `long<N>` — streak-based (consecutive `working` beats ≥ LONG_WORKING); Jev triage decides; the beat weighs in when the pane looks stuck.
- `burn<N>` — **wall-clock hard-wake, NOT gated on the extractor verdict.** A pane continuously `working` for >2h wall-clock wakes the beat at each new hour even when it does not *look* stuck. Do not rationalize a burn pane as "healthy mid-flight": a churning-but-busy pane (merge/unmerge/rework loops) looks productive to an extractor. Burn means the beat MUST weigh in this beat — redirect, post one exact ask for the operator, or interrogate why.

Streak and wall-clock are independent: streak counts consecutive beats in the `working` state (cadence-dependent); `working_since` is a wall-clock anchor. A pane with a long per-tab interval can have a low streak but a high wall-clock age — the burn class catches what streak logic misses.

## Safety contract (operator, 2026-10-18, extended same day)

- `waiting`, stale 0-1 → answer on his behalf: **momentum > perfection**. He said explicitly (GreenInBetween, 2026-10-21): "Don't hold on me" — never park a tab waiting for his sign-off if the agent can act or post one exact ask.
- `waiting`/`idle`/`agent_unknown`, stale ≥ 2 → **INTERROGATE** why: technical → restart it; question → weigh in for him; quality-check/browser/manual step → DO IT YOURSELF.
- `working` → leave alone unless long or burning:
  - `long<N>` (streak ≥ 2, ~1h+) → redirect/interrogate.
  - `burn<N>` (wall-clock >2h working) → **hard-wake, the pane MUST be addressed this beat** — weigh in, post one exact ask for the operator, or redirect. A pane spinning >2h is never "healthy mid-flight" by default; that assumption burned 7.5h operator-visible.
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
6. Log every actual tab outcome with a UTC timestamp and read back the exact Redis row. Use an argv list for JSON, never shell-interpolated JSON. A scheduler tick, suppression, arbitrary `skipped` row, or a fresh output file is not verified attendance. For a deliberate safe skip, produce structured attendance after examining fresh captures: `zcrankctl checked <exact-live-tab> --pane-id terminal_N [--pane-id terminal_M ...] --kind safe-skip --action '<decision and reason>'`. Read the captures the command prints, then enter `CHECKED` on stdin; never pre-confirm or backdate. The producer rechecks ownership/enablement and records capture hashes, actual timestamps, pane IDs and Redis readback. It never sends pane input. Keep ordinary sent/working/restarted action logs truthful and verify every send separately.

## Registry

`zcrankctl` (Redis SSOT): `zcrank:tab:<name>` hash {enabled}, `zcrank:pane:<tab>:<terminal>` overrides. Unlisted = OFF. Read `redis-cli LRANGE zcrank:log:<tab> -3 -1` for what previous beats did — never repeat an action a recent beat already took.

Registry pitfalls:
- Tab names contain spaces (e.g. "Pile of Dumb Things") — an unquoted `$k` in a `while read k; redis-cli HGETALL $k` loop splits into multiple args and errors. Always quote "$k" or drive redis-cli from a language runtime with an argv list.
- Append log rows with an argv list (python `subprocess.run(['redis-cli','RPUSH',key,json_str])`), never by interpolating JSON into a shell string — embedded double quotes get eaten by shell quoting and the row silently never lands. Verify by reading the key back.

## Health check (operator asks: is the crank alive?)

Verify the chain top-down; each layer's freshness proves the next:
1. Ticker: `~/.hermes/profiles/33god-pm/cron/ticker_heartbeat` — age in seconds (<60 = alive).
2. Cron jobs: parse `cron/jobs.json` — `crank-watchdog` enabled, `last_status: ok`, `next_run_at` in the future.
3. Scheduler output: newest `*.md` in `cron/output/777c511a009c/` proves only that a scheduled execution produced a file. `no_change`, `skipped before inference`, execution `completed`, and `last_status: ok` do NOT establish healthy projects. Inspect `usage_audit.jsonl` for the last actual agent completion and Redis per-project action/structured checked receipts. Stable monitor output can coexist with unattended work; verify effective enabled live panes and due cadence, not registry-only closed tabs. Monitor acknowledgements must not consume work refused before execution.
4. Live spot-check: use read-only topology and process/log evidence first; `zcrank-scan.sh` mutates pane counters, so run it deliberately, not as a read-only health probe. For apparent waits use Mechanics step 2. A working classifier alone is not proof; inspect actual progress. Compare installed watchdog/source hashes and use `crank-watchdog.sh --dry-run --state-file <scratch-path>` for non-delivering diagnosis.
5. Report separately: scheduler freshness, actual agent execution, per-project verified attendance, and independent burn/host health. Unavailable telemetry is unknown—not recovery. Never declare the crank healthy from output mtime or suppression alone.

## Beat output

End the turn with a one-paragraph circuit summary: per tab, state → action → proof. Evidence over status.
