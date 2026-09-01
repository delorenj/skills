# Delegation — every code change goes through a subagent

Momo performs **zero** code mutations. It never calls Edit/Write/NotebookEdit and never
runs code-changing Bash. Its only levers are read/inspect (Read, Grep, codegraph, git
status/log/diff), board + events, planning (TodoWrite/tasks), and **subagent dispatch**
(the Task/Agent tool). Every byte of code change flows through a delegated worker. This is
`subagent-driven-development` (kanban, WIP=1, two gates) mapped onto Claude Code, with
agent selection from the `coding-strategy` skill.

## Decompose first

Break the ticket into the smallest independent tasks (≈2–15 min each). For each record:
acceptance criteria, files **allowed** to touch, files **forbidden**, required checks
(project-specific — e.g. `pytest`, `ruff check`, `mise run ci`), and the output contract.
Tag each parallel-safe (disjoint files) or serialized (order by dependency). One TodoWrite
card per task with statuses `backlog/ready/in_progress/review/blocked/done`.

## Branch first

If the repo is on `main`/`master`, get consent and move work to a branch/worktree before
any card goes `in_progress`. **Record the base commit SHA now** — you need `BASE_SHA` for
the quality gate.

## Pick the agent (consult `coding-strategy`)

Classify (Trivial/Small/Medium/Large/Epic) and exhaust free/subscription tiers before
pay-per-token. Momo cannot do "trivial inline" (no code mutation), so even trivial goes to
a worker. Map `coding-strategy`'s OpenClaw primitives to this harness:

| coding-strategy says | In this Claude Code session |
| --- | --- |
| `sessions_spawn` / sub-agent | **Task/Agent tool** with a `subagent_type` (e.g. general-purpose, python-pro, frontend-developer) |
| `codex exec --full-auto` | `mcp__codex__codex` (or Bash `codex exec` in the repo, pty) |
| Claude Flow swarm / hive-mind | `mcp__claude-flow_alpha__swarm_init` + `task_orchestrate` (5+ files / Epic) |
| Jules (async PRs) | Jules API (`op://DeLoSecrets/Jules/API Key`) — fire-and-forget, returns a PR |

Small/Medium → one worker. Large/Epic → a swarm or several parallel workers on
non-overlapping files. Prefer a **different model/provider for review than for
implementation** to sharpen adversarial independence.

## Dispatch the implementer (WIP=1)

Move the card to `in_progress`. Spawn **one** worker. **Paste the FULL task text and
scene-setting context into the prompt** — never make the worker read the plan/ticket file,
never let it inherit Momo's session history. The prompt must carry:

- exact acceptance criteria;
- files allowed to modify / forbidden to modify;
- required checks/tests to run before reporting;
- the output contract: summary, changed files, test results, risks, and the ending status —
  one of `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`.

Do not run two implementers at once unless both cards are parallel-safe with disjoint files.
Answer questions the worker asks before it proceeds.

### Structured hand-back (33GPM-3)

Before dispatching, initialize a hand-back bundle so silent worker death is detectable:

```bash
python3 momo/skill/scripts/momo-worker-handback.py --issue <ISSUE> init --agent-id <worker-id>
```

The worker (or Momo on its behalf) calls `heartbeat` periodically to prove liveness.
When the worker finishes, it must `finalize` with `--status`, `--summary`, and check flags
(`--tests`, `--lint`, `--mutation`). A worker is not counted as done until `validate`
returns `VALID`. If the heartbeat goes stale (default TTL 300s), the monitor script
(`momo-worker-monitor.py`) detects it and Momo retries per the policy (max 3, exponential
backoff). The bundle is a JSON file at `_bmad-output/implementation-artifacts/handback/<ISSUE>.handback.json`.

**GoF pattern:** Command — each CLI subcommand (init/heartbeat/finalize/validate/show) is a
discrete command object with its own handler.

## Capture evidence (report is evidence, not truth)

When the worker returns, distill its report into the ticket's evidence file
(`_bmad-output/implementation-artifacts/issue-evidence/<ISSUE>.md`, shape in
`templates/issue-evidence.md`): status, files changed, test output, self-review findings,
risks, and the resulting **HEAD_SHA** and the implementer's identity (agent type +
model/provider — needed to prove reviewer independence later). Keep the raw transcript out
of your context; store only the distilled result.

### Automated evidence capture (33GPM-4)

Instead of re-running tests and mutation checks manually, use the evidence capture script:

```bash
python3 momo/skill/scripts/momo-evidence-capture.py --issue <ISSUE> \
  [--pytest-cmd "pytest"] [--ruff-cmd "ruff check ."] [--update-baseline]
```

This reads the hand-back bundle, runs baseline + branch test counts, executes a mutation
check (revert the fix, confirm tests fail, restore), and writes a machine-readable
`issue-<ISSUE>-evidence.json` artifact. Momo links this artifact in the evidence file
rather than narrating test runs in ticket comments. The `--update-baseline` flag records
the current test count as the baseline for future comparisons.

**GoF pattern:** Template Method — the capture flow (baseline → branch → mutation) is a
fixed skeleton with overridable steps (pytest-cmd, ruff-cmd).

Handle the status: `DONE` → gates. `DONE_WITH_CONCERNS` → address correctness/scope concerns
first. `NEEDS_CONTEXT` → supply it, re-dispatch. `BLOCKED` → give more context (same worker),
escalate to a more capable model, or split the task — never force an unchanged retry.

## Gate 1 — spec compliance (fresh, different subagent)

Move the card to `review`. Spawn a **new** Task worker whose prompt says: *do not trust the
implementer's report; read the actual diff line-by-line against the acceptance criteria;
report `✅ spec compliant` or `❌ issues [file:line]`.* Independence is structural — a
separate spawn with none of the implementer's context. On `❌`: hand the specific issues back
to the **same implementer** to fix (Momo never fixes code itself), then spawn **another
fresh** reviewer. Loop to `✅`.

## Gate 2 — code quality (only after spec ✅, fresh subagent)

Spawn a fresh reviewer (e.g. `code-reviewer` subagent) with `WHAT_WAS_IMPLEMENTED`,
`PLAN_OR_REQUIREMENTS`, `BASE_SHA`, `HEAD_SHA`, `DESCRIPTION`. Capture
Strengths/Issues(Critical/Important/Minor)/Assessment into evidence. On issues: same
implementer fixes → fresh quality reviewer re-reviews. Loop to approved. Then the card is
`done`.

## Reviewer-independence mechanism (how the gate stays honest)

1. Implementer, spec-reviewer, and quality-reviewer are **three separate spawns** — never
   continue the implementer's thread to review its own work.
2. The implementer's built-in self-review satisfies **neither** gate.
3. Prefer a different model/provider family for review vs. implementation.
4. Record implementer identity and each reviewer identity in the evidence so the audit trail
   proves independence — this is exactly what the sentinel's `issue-autonomous-review.sh`
   independence check reads (`- Worker:` / `- Implemented by:` in evidence).
5. Fixes go back to the original implementer; the follow-up review is always a brand-new
   reviewer instance.

## Milestone closeout

After all cards: dispatch one final reviewer over the whole diff, then finish the branch.
Emit the closeout: final board snapshot, decision log (scope cuts/retries/trade-offs),
validation summary, remaining backlog, next recommended card — and a decision event for any
consequential call.
