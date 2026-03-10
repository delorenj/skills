# Project Crank Engine Prompt Templates

## Template A — Sprint Finish Crank (default)

Use for balanced/aggressive loops where execution is expected every cycle.

```text
Project Crank Engine — Sprint Finish Loop

Project: {{project}}
Current Focus: {{scope}}
Goal: {{goal}}

Mission
- Execute the highest-leverage unblocked work to finish the sprint.
- Follow BMAD + ticket-first + PR-first discipline.

Required status evidence on every update
1) Repo facts
- git rev-parse --abbrev-ref HEAD
- git log -1 --oneline
- git status --short
- git stash list
- gh pr list --state open

2) Sprint facts
- Done/Total stories: {{done_metric_query}}
- Remaining blockers: explicit list with owner + next action

3) Visual proof
- Capture one screenshot showing current board/PR completion state (path or link).

Finish contract (all must pass)
- Ticket metric: {{ticket_metric}}
- PR metric: {{pr_metric}}
- Validation metric: {{validation_metric}}
- Evidence metric: screenshot provided + command-backed facts included

Decision rule
- If ALL finish contract checks pass: respond `DONE` with evidence summary.
- Else respond `NOT DONE` with exact gap and immediate next action.

If NOT DONE
- Continue execution immediately on the next highest-impact gap.
- No idle waiting.
```

## Template B — Light Status Crank (30m default)

```text
Project Crank Engine — Light Status Loop

Project: {{project}}
Goal: {{goal}}
Current focus: {{scope}}

Mission this cycle
- Provide a concise factual status update.
- Execute only the next smallest unblock if needed.

Required evidence
- branch, last commit, git status, stash, open PRs
- sprint Done/Total count
- blockers + owner + next action

Decision
- If progress stalled for 2 consecutive cycles: escalate with corrective plan.
- Otherwise continue light cadence updates.
```

## Template C — Story Burn-Down Crank

```text
Project Crank Engine — Story Burn-Down

Target story set: {{stories}}
Cadence objective: ship at least {{target_rate}} stories per cycle.

Required per cycle
- Story status delta since last run
- PR delta since last run
- Test delta since last run
- One screenshot of board/progress

Completion
- All target stories in Done
- No open blocker tagged Critical
- Main branch green
```

## Corrective “Back In The Oven” Snippet

```text
NOT DONE. Back in the oven.
Gap(s):
- {{gap_1}}
- {{gap_2}}

Do now:
1) {{action_1}}
2) {{action_2}}

Return with updated evidence set (repo facts + sprint facts + screenshot).
```