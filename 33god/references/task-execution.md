# Task Execution

Use this for day-to-day delivery once a task is assigned.

## Task source requirement

Every task must map to one source:
- Plane ticket ID
- Bloodbank correlation/event chain
- Explicit human directive with date/context

## Execution protocol

1. Confirm acceptance criteria before coding.
2. Link task source in working notes and commit context.
3. Implement in scoped branch/worktree.
4. Validate via tests/lint/manual checks.
5. Update docs/status artifacts impacted by the change.
6. Report outcome: shipped, evidence, blockers, next step.

## Minimum delivery report

```markdown
- Task source: <id>
- What changed: <1-3 bullets>
- Verification: <tests/checks>
- Blockers: <none | list>
- Next: <immediate next action>
```
