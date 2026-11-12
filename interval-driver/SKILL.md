---
name: interval-driver
description: Run an LLM agent on an interval (hourly groomer, Launch Director, crank beat, any "poke and prod" pass) for tens of thousands of tokens instead of ~1M. Use when creating, auditing or slimming a Hermes job that Candybar fires on a schedule, when a scheduled agent pass costs too much, or when building a new interval-triggered groomer for a project board. Also use when the question is "why does this pass cost so much", "how do I keep a PM from tunnelling", "how does a recurring agent remember between runs", or "how do a PM and an EM hand off on a schedule". This is the house pattern for every recurring agent pass on every project.
---

# Interval driver: cheap scheduled agent passes

An interval agent wakes on a clock, looks at what changed, prods the work forward and goes back to
sleep. Done naively each wake rebuilds the world: re-reads the board, loads skills, runs session
hooks, carries every tool schema. Gruvato's Launch Director measured **~1M tokens per pass** that
way (2026-11-12), and so does the 33GOD crank beat (600k-1.1M per non-skipped beat).

The fix is to make the driver hold the context, not the agent's turn:

| Part | What it is | Why |
|---|---|---|
| **Clock** | Candybar `hermes` runner firing a job pinned `--scheduler external` | single clock (`candybar` skill) |
| **Gate** | job `monitor_script`: prints a stable snapshot; Hermes hashes it | unchanged = agent never starts, 0 tokens |
| **Work list** | the monitor diff Hermes injects | the agent works the delta, not the board |
| **Roadmap** | job `script` (brief): stdout injected every run; the agent's own terse state file + the pass contract | the agent's cached context; no re-orienting |
| **Lazy load** | a compact reader (`scripts/px-brief.mjs`) for anything not in the roadmap | 1k tokens per ticket instead of 12k |
| **Lean context** | per-job `enabled_toolsets` allowlist + `no_mcp`, no preloaded skills | every LLM call resends tool schemas and skills |
| **Finish** | agent rewrites its roadmap file, writes a short pass note | next wake starts warm |

## Where the tokens go (measured, Hermes 2026-11-12)

- Cost of a pass ≈ (number of LLM calls) × (context size at each call). Context = system prompt +
  tool schemas + skills + every tool result so far. 12 calls growing to 106k context = 964k tokens.
- Default toolsets: a bare "reply OK" cost 236k tokens (7 calls). With `-t terminal,file`: 12k, one call.
- `px show REF --json` on a busy ticket is ~50 KB (~12k tokens) of comment HTML; `px-brief.mjs`
  prints the same ticket in ~3 KB.
- Provider caching (cache_read) does not reduce the counted tokens; through the AutomaticAI gateway
  it reports 0 anyway. Only fewer calls and smaller context help.

## Recipe

1. **Snapshot** (monitor): a script that prints one stable line per thing the agent cares about.
   No timestamps; sort; bucket ages coarsely (12h) and counts (by 5) so aging alone does not wake
   it. Unreadable sources print one fixed `UNAVAILABLE` line. Example:
   `~/code/gruvato/scripts/launch/groom-snapshot.mjs`.
2. **Brief** (script): `cat` the pass-contract prompt file from the repo, then the agent's
   roadmap file (or `NO ROADMAP YET: build it from your newest pass note`). Example:
   `~/.hermes/profiles/gruvato-launch-director/scripts/gruvato-launch-brief.sh`.
3. Both scripts must be **real files** in `~/.hermes/profiles/<profile>/scripts/` (Hermes refuses
   symlinks); have them exec/cat the repo's source of truth.
4. **Prompt** (repo file): say the diff is the work list and the roadmap is the context; give a
   tool-call budget (~6) and a board-write budget; mandate the compact reader; forbid skills,
   session hooks, tests and "session evidence"/heartbeat comments; quiet diff = no write; finish by
   rewriting the roadmap (<40 lines) and a pass note (<20 lines).
   The job's own prompt is one line: "Follow the pass contract in the brief above."
5. **Lean the job** (does not touch schedule, scheduler pin, monitor or prompt):
   ```bash
   ~/.hermes/hermes-agent/.venv/bin/python ~/.agents/skills/interval-driver/scripts/lean-job.py \
     --profile <profile> --job <hex id> --brief <brief.sh> --max-iterations 10 --dry-run
   ```
   then without `--dry-run`. Adds `no_mcp` (a per-job toolset list otherwise merges every enabled
   MCP server back in), clears skills, sets the brief, caps iterations.
6. **Prove**: `candybar run <name> --wait` twice. First: a real pass, read `TOKENS` in
   `candybar history <name>` and the pass note. Second (nothing changed): `success ... tokens 0`.
   Check a skip by hand with `printf '%s' "$(snapshot)" | sha256sum` against
   `monitor_state.last_output_hash` in the profile's `cron/jobs.json` (Hermes strips the trailing
   newline before hashing).

## Pitfalls

- Every comment the agent posts changes the board it watches. A "session evidence" comment on a
  quiet pass is pure cost and can wake the next pass.
- Hermes economics default `max_iterations` is 12 and `max_daily_tokens` 1M unless the profile's
  `cron.economics` overrides it; set per-job caps with `lean-job.py`.
- Do not seed the monitor baseline by hand to dodge the first run; the first run is the proof.
- `context_from: self` (`--continuity`) injects only the previous final answer, clipped to 8k: it
  is not a warm session. The roadmap file is the durable context.
- A warm resumed session (`hermes chat --continue <name> --create-if-missing`) remembers, but it
  resends the whole transcript every call and grows all day; prefer fresh + roadmap.

## Questions that lead here (mental models)

If you are asking one of these, the answer is this skill.

- **"Why did one scheduled pass cost a million tokens?"** The pass cost is LLM calls times the
  context at each call. A pass that reads the board, loads skills and runs hooks makes many calls
  over a growing context. Shrink both: one or two calls over a small brief.
- **"How does a recurring agent remember what it knew last hour?"** It doesn't, and its session
  shouldn't. A roadmap file that it rewrites at the end of each pass, injected by the brief at the
  start of the next one, is its memory. `--continuity` is an 8k-clipped final answer, not memory.
  A warm resumed session resends the whole day every call.
- **"How do I stop it running when nothing happened?"** A monitor script with a stable snapshot.
  The hash is unchanged, so the agent never starts and the run costs 0 tokens. Anything that ages
  on its own (timestamps, raw counts) belongs in the brief, not the snapshot.
- **"What should the agent look at this pass?"** The monitor diff. It's the work list. The
  agent never lists the board itself.
- **"It needs a detail the roadmap doesn't have."** It lazy-loads that one thing with a compact
  reader (`px-brief.mjs` for Plane tickets), by ref, in one call. It never uses a full JSON dump.
- **"How do I keep a PM from tunnelling on one ticket for hours?"** Don't give it hours. Give it
  a clock, a delta and a budget of about 4 tool calls. Pair it with a Launch Director pass that
  only ranks and flags (next section). Tunnel vision is what an unbounded turn does.
- **"Where do the clock and the agent meet?"** Candybar fires a Hermes job pinned
  `--scheduler external`. That's one clock (`candybar` skill). The job's `script`/`monitor_script`
  are the driver, and the agent is only the judgement in the middle.
- **"Should this be a long-running daemon agent, a crank beat or an hourly pass?"** If its job
  is to look at what changed and prod it, it's an interval pass. Use this recipe.

## PM/EM pair on two clocks (TOLT, 2026-11-12)

Two interval passes split decide from do, so neither one tunnels:

| | Launch Director (decides) | EM (applies) |
|---|---|---|
| Profile / job | `tolt-launch-director` / `76ebcd4d652f` | `tolt-pm` / `334a9363d4d1` |
| Candybar | `tolt-launch-director-pass`, `30 8-22 * * *` | `tolt-em-pass`, `0 8-22 * * *` |
| Monitor | open tickets' lanes + date line | lane, `ld-waiting:<n>` (LD comments newer than the last `[em]` one), `agent:working` |
| Writes | `[launch-director]` comments only: rank, focus flag, QA verdict, path-label rec, date ask, one launch-gap ticket | `[em]` comments, lane moves, `px release`, close on an ACCEPTED verdict, under the board-driver lease |
| Roadmap | `agents/hermes/launch-director/runtime/roadmap.md` | `agents/hermes/pm/runtime/em-roadmap.md` |

- The comment tag is the handshake. The EM's monitor counts LD comments newer than its last
  `[em]` comment, so an LD decision wakes the EM within 30 minutes, and the EM answering clears it.
- Each side's writes wake the other once, and its own once (the "own echo"). The contract tells
  the agent to answer `quiet: own echo` with no tool calls when the diff is only its own writes.
- The EM never dispatches workers in the pass. It orders and unblocks Todo, and workers pull from
  there. The LD never moves lanes. Keep that split: the role that ranks is never the role that moves.
- Source: `~/code/tolt/agents/hermes/{launch-director,pm}/` (`launch-brief.py`,
  `em-pass.py --monitor|--brief`, `*-pass.prompt.md`) and `~/code/tolt/.candybars/`.
  Flume role templates: `~/code/33GOD/flume/roles/{paired-launch-director,em}.md`.

## Measured

TOLT Launch Director, same board, 2026-11-12:

| Pass | Tokens | What changed |
|---|---|---|
| Naive first pass | 1,318,444 | read every ticket with full comment HTML |
| Contract + flags | 436,727 | still 12 calls, memory/hindsight upkeep, `px show --json` |
| Lean toolsets | 362,378 | `terminal,file,no_mcp`; still re-reading |
| Roadmap + diff + px-brief | 72,938 | interval-driver recipe, `max_iterations 8` |
| Unchanged board | 0 | monitor hash matched; the agent never started |

Gruvato's Launch Director and the 33GOD crank beat measured the same ~1M naive baseline.
