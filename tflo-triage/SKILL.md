---
name: tflo-triage
description: Pick the next Trello card to work on. Scores open cards on the Intelliforia board, claims the top one, moves it to In-Progress, creates the branch, writes FSM state. Use when the user says "what should I work on?", "tflo start", "claim next ticket", or when the orchestrator loops idle → triage. Mutates Trello + git on claim.
---

# tflo-triage — Pick the next ticket

## Overview

Scores cards on the Intelliforia Trello board (`https://trello.com/b/jLl1NE0Z/intelliforia`), claims the top one, and hands off to `tflo-implement` with the FSM at `phase: implementing`.

Scoring + mutation logic lives in `scripts/tflo.py`. This SKILL is the orchestrator's contract for how to invoke it and route the outcome.

## Preconditions

- `_bmad/memory/tflo/current-ticket.md` does **not exist**. Absence of that file is the FSM's idle marker; there is no `phase: idle` value.
- No ticket is in the `escalated` state. Check the last entry of `_bmad/memory/tflo/tickets/*/transitions.jsonl` for any unresolved `to: escalated`. If found, surface to the user before claiming. Triage MUST NOT claim past an unacknowledged escalation.
- `TRELLO_API_KEY`, `TRELLO_TOKEN`, `TRELLO_BOARD_ID` env vars are set (exported from `~/.config/zshyzsh/secrets.zsh`).
- We're in the intelliforia repo on a sane base branch (`main` or `staging`, not a stale ticket branch).
- Hindsight recall has been run for the `intelliforia` bank this session (orchestrator's responsibility per global instructions; triage assumes it's done).

## Invocation modes

Triage runs in one of two modes depending on the caller. The SKILL behaves differently for each.

| Mode | Caller | Behavior |
|---|---|---|
| **Manual** | User typed `/tflo-triage` or asked "what should I work on?" | Run dry-run, present ranking, ask once before claiming. HITL confirmation is appropriate here because the user is browsing. |
| **Autonomous** | Orchestrator looping from `idle` (Otto, /loop, autopilot) | Run dry-run for the log, then claim the top card with `--yes`. No HITL. If preconditions fail, abort the loop iteration and surface to the next idle check, do NOT pause to ask. |

**Detection heuristic**: if the immediately-preceding turn was a user typing `/tflo-triage` or an exploratory question, treat as manual. If the preceding context is an orchestrator hand-off from `tflo-create-pr` resetting FSM to idle, treat as autonomous.

## Capabilities

### Dry-run (read-only, no mutations)

```bash
mise run tflo:dry-run
```

Output: markdown table with rank, total score, type, card name, list position, and the per-component score breakdown (Pos / Pri / Bug / Free / Mine).

Underlying script flags (use directly if `mise` isn't available):

```bash
uv run python scripts/tflo.py dry-run --list-name 'To-Do' --limit 10 --format table
```

Use when:
- Manual mode — show the ranking before claiming.
- Autonomous mode — log the ranking before the claim so the run record has it.
- The user is browsing the backlog and not yet committed to claiming.

### Claim the top card

Score the source list, move the top card from `To-Do` to `In-Progress`, create branch, write `current-ticket.md`, post a Trello comment.

Preview (no mutations):
```bash
mise run tflo claim           # equivalent to: uv run python scripts/tflo.py claim
```

Execute (real mutations):
```bash
mise run tflo claim --yes     # equivalent to: uv run python scripts/tflo.py claim --yes
```

Output on success:
```
✓ Claimed [N] '<card name>'
  Branch:  <idShort>-<kebab-name> (checked out)
  Memory:  <path to current-ticket.md>
```

After successful claim, FSM is at `phase: implementing`. Hand off to `tflo-implement`.

### Manual pick (specific card)

Not implemented as a CLI flag. Workaround: drag the preferred card to position #1 in `To-Do`, then claim. Position dominates scoring, so #1 always wins. If you find yourself doing this often, it's a signal to add a `--card-id` flag to `scripts/tflo.py claim`.

## Failure modes

| Symptom | Meaning | Action |
|---|---|---|
| `current-ticket.md exists at <path>` | A previous ticket is in flight | Run `mise run tflo abort --yes` to release it, or invoke the orchestrator's `resume` capability. |
| Unresolved `escalated` transition in `tickets/*/transitions.jsonl` | Prior ticket escalated to human, never acknowledged | Surface to user. Do NOT claim. |
| `List not found on board: 'To-Do'` | Board structure changed | Re-run `mise run tflo:list-lists`, update `scripts/tflo.py` defaults if needed. |
| `Missing required env var: TRELLO_*` | Creds missing | Source `~/.config/zshyzsh/secrets.zsh` or set env vars manually. |
| HTTP 401 / 403 from Trello | Token expired or revoked | Regenerate Trello token, update env. |
| HTTP 5xx | Trello transient | Retry once. If persistent, surface to human. |

## Inputs

Dry-run flags (`scripts/tflo.py dry-run`):
- `--list-name TEXT` — list to score (default `To-Do`)
- `--limit INTEGER` — top N to display (default 10)
- `--format [table|json]` — output format (default `table`)

Claim flags (`scripts/tflo.py claim`):
- `--source-list TEXT` — list to draw from (default `To-Do`)
- `--target-list TEXT` — list to move into (default `In-Progress`)
- `--yes` — execute mutations (without this flag, dry-run only)

## Outputs

- `_bmad/memory/tflo/current-ticket.md` written with FSM state. Includes `previous_list` + `claimed_from_branch` for abort reversibility.
- New git branch checked out, named `<idShort>-<kebab-name>`, capped at 60 chars.
- Comment posted on the Trello card announcing the claim.
- First entry appended to `_bmad/memory/tflo/tickets/<idShort>/transitions.jsonl`.

## Handoff

After successful claim: orchestrator invokes `tflo-implement`. `current-ticket.md` is the source of truth for what to implement (notably the `type` field, which drives the implement chain).

## Related

- Reverse a claim: `mise run tflo abort --yes` (returns card to source list, deletes FSM, drops branch)
- Orchestrator: `tflo-agent-orchestrator`
- Module plan: `_bmad-output/planning-artifacts/module-plan-trello-lifecycle-2026-05-06.md`
- Autonomous-mode contract for the full chain: `feedback_tflo_autonomous_no_clarification.md` in user memory
