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
| **Apply** | agent writes ONE plan file (JSON writes + new roadmap); `scripts/px-apply.py` executes it | the agent decides, the driver acts: lease, tag, verbs, cap, no repeats are code, not prompt |
| **Finish** | the applier writes the roadmap; the agent returns a short pass note | next wake starts warm |

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
   Fix the pass to **three tool calls**: an optional `px-brief.mjs` read, one `write_file` of a plan
   JSON, one terminal call to the applier. Give the plan shape in the contract.
   **Applier**: a `--apply` mode in your pass script that execs `scripts/px-apply.py PLAN --cwd
   <repo> --tag "[role]" --ops comment,move,... --max N [--lease LOCK --owner O] --roadmap PATH`.
   It archives the plan first (`PLAN.applied.json` plus `passes/<UTC stamp>.json` history; never
   applied twice, and the next `write_file` is a new file; an optional `"note"` rides along), takes
   and always releases the lease (`scripts/board-lease.py`, shipped beside the applier; the applier
   exits 2 if it is missing), adds the tag, refuses other verbs/lanes/bad refs, skips a comment
   already posted, writes the roadmap and prints one line per write (the agent's read-back).
   Example: `~/code/tolt/agents/hermes/pm/em-pass.py --apply`.
5. **Lean the job** (does not touch schedule, scheduler pin, monitor or prompt):
   ```bash
   ~/.hermes/hermes-agent/.venv/bin/python ~/.agents/skills/interval-driver/scripts/lean-job.py \
     --profile <profile> --job <hex id> --brief <brief.sh> --max-iterations 10 --dry-run
   ```
   then without `--dry-run`. Adds `no_mcp` (a per-job toolset list otherwise merges every enabled
   MCP server back in), clears skills, sets the brief, caps iterations. Then
   `hermes -p <profile> cron edit <id> --reasoning-effort medium --no-continuity`: profiles default
   to xhigh (50k reasoning tokens on one EM pass), and the roadmap replaces continuity. Use `low`
   when the pass only applies decisions (the EM). Reasoning is replayed into every later call of
   the pass: one 17k-token first-call reasoning made the TOLT EM's 4 calls cost 133k.
   Clear the job's workdir (`--workdir ""`) and use absolute paths in the contract: with a
   workdir, Hermes injects that repo's AGENTS.md/CLAUDE.md into every call (TOLT: +4k tokens
   per call, 11.8k -> 7.8k base).
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
- **Cron blocks heredocs** ("shell execution via heredoc" needs an approver) and `write_file`
  **refuses to overwrite a file the session hasn't read in full**. So an agent can't rewrite its
  roadmap in place cheaply: the plan file + applier writes it instead.
- Prompt rules a model can drop will be dropped. Seen on one EM pass: took the board-driver lease
  and never released it, listed the board four ways, ran `px --help` twice, re-posted releases its
  stale roadmap still listed as owed. Move every such rule into the applier.
- **The snapshot outranks the roadmap.** Say so in the contract; the roadmap lists only what is
  still open, never what a pass did, or the next pass repeats it.
- **Monitor only what this role acts on.** The EM first watched `agent:working`; live workers flip
  it all day and woke the EM for nothing. It now watches `stale-claim` (working and idle 48h).
- Say in the contract that `write_file` takes `path` plus `content` **as a JSON string**. Shown an
  inline JSON plan, the TOLT LD passed `content` as an object with no `path`, five times.
- `px release` lands the ticket in **Todo**, where dispatch picks it up. Parking is release +
  move to Backlog (the applier's `release` takes `"lane": "Backlog"`).

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
- **"The agent keeps breaking a rule in its contract (lease, tag, no repeats)."** Stop asking.
  The agent decides and writes a plan; the driver acts (`px-apply.py`). A rule in code holds.

## PM/EM pair on two clocks (TOLT, 2026-11-12)

Two interval passes split decide from do, so neither one tunnels:

| | Launch Director (decides) | EM (applies) |
|---|---|---|
| Profile / job | `tolt-launch-director` / `76ebcd4d652f` | `tolt-pm` / `334a9363d4d1` |
| Candybar | `tolt-launch-director-pass`, `30 8-22 * * *` | `tolt-em-pass`, `0 8-22 * * *` |
| Monitor | open tickets' lanes + date line | lane, `ld-waiting:<n>` (LD comments newer than the last `[em]` one), `stale-claim` |
| Writes | `[launch-director]` comments only: rank, focus flag, QA verdict, path-label rec, date ask, one launch-gap ticket | `[em]` comments, lane moves, `px release`, close on an ACCEPTED verdict, under the board-driver lease |
| Roadmap | `agents/hermes/launch-director/runtime/roadmap.md` | `agents/hermes/pm/runtime/em-roadmap.md` |

- The comment tag is the handshake. The EM's monitor counts LD comments newer than its last
  `[em]` comment, so an LD decision wakes the EM within 30 minutes, and the EM answering clears it.
- Each side's writes wake the other once, and its own once (the "own echo"). The contract tells
  the agent to answer `quiet: own echo` with no tool calls when the diff is only its own writes.
- The EM never dispatches workers in the pass. It orders and unblocks Todo, and workers pull from
  there. The LD never moves lanes. Keep that split: the role that ranks is never the role that moves.
- Source: `~/code/tolt/agents/hermes/{launch-director,pm}/` (`launch-brief.py`,
  `em-pass.py --monitor|--brief|--apply`, `*-pass.prompt.md`) and `~/code/tolt/.candybars/`.
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

TOLT EM (tolt-pm), same day, each row one fix:

| Pass | Tokens | What changed |
|---|---|---|
| First pass, prompt-only writes | 480,789 | `px --help` x2, blocked heredoc, read-back, xhigh reasoning; 8 writes (backlog catch-up) |
| Exact px forms, medium reasoning | 194,627 | still a roadmap read+rewrite and a `gh` detour |
| Plan file + `--apply` | 122,550 | 2 tool calls, 3 writes |
| Plan file + `--apply`, small diff | 38,474 | 2 tool calls, 1 write |
| + no workdir, reasoning `low` | 67,324 | 5 calls at ~13k each (was ~33k at medium with workdir) |
| Unchanged board | 0 | 17.9s, the agent never started |

Gruvato's Launch Director, 2026-11-12: 1.07M naive, 441k lean (still hitting the cap with no
roadmap), 108,077 with plan + applier at medium effort (the pass rebuilt its roadmap; 0 board
writes). TOLT LD's first plan + applier pass: 138,329, five of its eight calls failed `write_file`
calls (pitfall above). The 33GOD crank beat measured the same ~1M naive baseline.

## Crank beat (33GOD, 2026-11-12)

The crank beat is the same driver over zellij panes instead of a board: one interval pass that
prods stalled agents forward. Every 5 minutes Candybar fires `crank-beat` → Hermes `33god-pm` job
`777c511a009c`.

| Part | Crank form |
|---|---|
| Gate | `zcrank-gate` prints `tab\|pane\|class` per pane that needs attention (poke, interrogateN, longN, burnN) plus local watchdog keys; unchanged = 0 tokens |
| Brief | `~/.agents/tools/jev-clairic/hermes/crank-beat-brief.sh`: the beat contract (`crank-beat-prompt.txt`) + `~/.local/state/zcrank/gate-tails.md`, the tail of every listed pane the gate already captured |
| Lazy load | `zellij action dump-screen` of one pane, `tail -40`, only when its tail in the brief is not enough |
| Lean | `enabled_toolsets: [terminal, no_mcp]`, no skills; 12-call cap, plan for 6, one call per pane |
| Writes | `zcrank-send` (tagged `[crank]`, screen-checked) and batched `zcrankctl log` rows: the tools already enforce tag, shell/draft refusal and logging, so no plan file is needed |

- The beat must never rerun `zcrank-scan.sh`: it mutates the stale counters, and re-reading
  200-line tails per pane is what made naive beats cost 600k-1.1M.
- Own echo: a send flips a pane from waiting to working, which changes the gate output, so the
  next beat wakes on a real change. `zcrankctl log` rows are not in the gate output and do not
  wake it.
- Measured: naive beats 600k-1.1M (12 beats burned the 10M/24h job cap by mid-morning); first lean
  beat 167,276 tokens in 3m27s, 6 calls, two verified sends, two operator asks. Unchanged gate: 0.
