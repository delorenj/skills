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

- `waiting`, stale 0-1 → move it forward **as Crank**, with his standing preference as your authority: **momentum > perfection**. He said explicitly (GreenInBetween, 2026-10-21): "Don't hold on me" — never park a tab waiting for his sign-off if the agent can act or post one exact ask.
- `waiting`/`idle`/`agent_unknown`, stale ≥ 2 → **INTERROGATE** why: technical → fix or restart it; a question about the work → give Crank's own recommendation; a question only he can answer (who a person is, a name, a relationship, a preference, money, a client) → park one exact ask, never answer it; quality-check/browser/manual step → DO IT YOURSELF.
- **You are not the operator.** Write as Crank, never first-person as Jarad ("go ahead with option B", not "I want B"). A fact about his life counts only if it is on an untagged operator line in the pane (a `❯` line without `[crank]`) or in a file or registry he owns; never a `[crank]` line, never something the pane agent guessed. When a pane needs one, send `Operator-only fact, I can't answer it. Park it for Jarad and continue with the rest.` and post one exact ask.
- **Loop-breaker:** if a pane replies that a point is operator-only, or that a `[crank]` message did not fit, never answer it again: `zcrankctl log <tab> waiting 'operator-only: <one line>'` and skip the pane until its state changes.
- A Crank "yes" is not his approval for client-visible sends, spending, deleting data, credential or permission changes, or releases: park those with one exact ask.
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
3. Pane input (per-tab terminal_N from scan): type text ONLY with `~/.local/bin/zcrank-send --pane-id <pane> --tab <tab> -- '<msg>'` (or `--message-file -` with a heredoc when the message has an apostrophe). Every message arrives as `[crank] <msg>` so the pane agent can tell Crank from the operator: a Crank-typed `name 707163 Laura` once renamed the operator's wife. The tool reads the box with `dump-screen --ansi`, refuses a shell, a menu or an operator draft (exit 2), checks the tag landed before Enter and that the text left the box after (exit 3 = not submitted, box cleared or draft restored: do not just retry; 1 = zellij failed, nothing typed; 4 = sent but unlogged, do not resend), and logs every call to `~/.local/state/zcrank/sends.jsonl`.
   - An operator draft in the box is his. Submit it with `zcrank-send --pane-id <pane> --tab <tab> --relay-draft` only when it reads as a finished instruction: the tool reads it off the screen and sends `[crank relay] <draft>`; a dim Claude Code suggestion is not a draft and is refused. Otherwise leave it and log `waiting operator draft`.
   - Slash commands: `--control /compact` or `--control /exit` only.
   - Never `write-chars`, `write` or `paste` yourself, in any tool or inline script: the hook-hub `crank-keys-guard` denies it. Bare `send-keys` is for Esc, `"Ctrl c"` and the Esc-Esc abort. Key syntax: `"Ctrl c"` (space, quoted as ONE arg) — `C-c` and unquoted `Ctrl c` both fail.
4. Abort a wedged turn: send `Esc` ONCE (arms "esc interrupt" indicator), wait, send `Esc` AGAIN to confirm — the abort then cascades through subagents; the input box returns minutes later. Text typed after the first Esc queues and submits on its own. Verify the new turn: fresh pane content, CPU ticking, storage writes resuming.
5. Verify every send: dump the pane after ~20s — the message must appear with ❯ prefix (as `❯ [crank] …`) as a SENT line (in history), not sitting in the input box; footer clock advancing.
6. Log every actual tab outcome with a UTC timestamp and read back the exact Redis row. Use an argv list for JSON, never shell-interpolated JSON. A scheduler tick, suppression, arbitrary `skipped` row, or a fresh output file is not verified attendance. For a deliberate safe skip, produce structured attendance after examining fresh captures: `zcrankctl checked <exact-live-tab> --pane-id terminal_N [--pane-id terminal_M ...] --kind safe-skip --action '<decision and reason>'`. Read the captures the command prints, then enter `CHECKED` on stdin; never pre-confirm or backdate. The producer rechecks ownership/enablement and records capture hashes, actual timestamps, pane IDs and Redis readback. It never sends pane input. Keep ordinary sent/working/restarted action logs truthful and verify every send separately.

## Registry

`zcrankctl` (Redis SSOT): `zcrank:tab:<name>` hash {enabled}, `zcrank:pane:<tab>:<terminal>` overrides. Unlisted = OFF. Read `redis-cli LRANGE zcrank:log:<tab> -3 -1` for what previous beats did — never repeat an action a recent beat already took.

Registry pitfalls:
- Tab names contain spaces (e.g. "Pile of Dumb Things") — an unquoted `$k` in a `while read k; redis-cli HGETALL $k` loop splits into multiple args and errors. Always quote "$k" or drive redis-cli from a language runtime with an argv list.
- Append log rows with an argv list (python `subprocess.run(['redis-cli','RPUSH',key,json_str])`), never by interpolating JSON into a shell string — embedded double quotes get eaten by shell quoting and the row silently never lands. Verify by reading the key back.

## Health check (operator asks: is the crank alive?)

Verify the chain top-down; each layer's freshness proves the next. Candybar is the
single clock: the crank fires as candybars `crank-beat` (`*/5`) and `crank-watchdog`
(`*/15`), not from the Hermes ticker.
1. Schedule of record: `cd ~/code/33GOD/candybar && uv run candybar show crank-beat` and
   `... show crank-watchdog` (or `curl -s http://127.0.0.1:8700/candybars`): both registered,
   enabled, and the latest terminal invocation (`GET /candybars/<id>/invocations`) is recent
   with `result: success`. A stale or failing last invocation is the first fault.
2. Hermes job pin: in `~/.hermes/profiles/33god-pm/cron/jobs.json`, confirm only that the
   crank jobs are `scheduler: external`. For external-pinned jobs, `enabled`, `next_run_at`
   and `last_status` are stale ledger fields, not the schedule: `enabled: false` with an old
   `next_run_at` is normal and is NOT a dead crank. Never re-enable a native Hermes schedule to
   "fix" it. `cron/ticker_heartbeat` is not a liveness proof for the crank.
3. Scheduler output: newest `*.md` in `cron/output/777c511a009c/` proves only that a scheduled execution produced a file. `no_change`, `skipped before inference`, execution `completed`, and `last_status: ok` do NOT establish healthy projects. Inspect `usage_audit.jsonl` for the last actual agent completion and Redis per-project action/structured checked receipts. Stable monitor output can coexist with unattended work; verify effective enabled live panes and due cadence, not registry-only closed tabs. Monitor acknowledgements must not consume work refused before execution.
4. Live spot-check: use read-only topology and process/log evidence first; `zcrank-scan.sh` mutates pane counters, so run it deliberately, not as a read-only health probe. For apparent waits use Mechanics step 2. A working classifier alone is not proof; inspect actual progress. Compare installed watchdog/source hashes and use `crank-watchdog.sh --dry-run --state-file <scratch-path>` for non-delivering diagnosis.
5. Report separately: scheduler freshness, actual agent execution, per-project verified attendance, and independent burn/host health. Unavailable telemetry is unknown—not recovery. Never declare the crank healthy from output mtime or suppression alone.

## Beat output

End the turn with a one-paragraph circuit summary: per tab, state → action → proof. Evidence over status.
