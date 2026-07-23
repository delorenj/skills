# Autonomy And Blockers

## Default Autonomy

When the user delegates ticket triage or says "continue", choose the next likely work item without asking for a menu choice. Use context:

- active branch and git status;
- newest user instruction;
- BMAD story status;
- Plane ticket status;
- open PRs and review comments;
- recent local test or dashboard failures;
- known blockers.

Explain the chosen work briefly, then move.

## Next Ticket Selection

Prefer work that is:

- unblocked;
- aligned with the active checkpoint or BMAD epic;
- small enough to review;
- high leverage for the next acceptance gate;
- safe to do without external credentials;
- unlikely to conflict with a pending review.

Avoid work that:

- depends on an unresolved product decision;
- writes production data;
- requires unavailable credentials;
- conflicts with active teammate work;
- would create a second source of truth.

## Blocked Work

When blocked:

1. Record the blocker in the Plane issue and BMAD story.
2. Include exact missing input, owner, and date.
3. Move the ticket to Blocked if Plane supports that status.
4. Choose the next unblocked ticket.
5. If the blocker has repeated or caused long idle time, propose a notification or automation.

## No Idle Agents

Do not sit waiting when useful work remains. The pipeline should continue unless:

- the user explicitly says stop;
- all available work is blocked;
- continuing would risk irreversible damage;
- a required product decision cannot be inferred safely.

## Notification And Escalation Pattern

If a blocker waits too long:

- first occurrence: record and continue elsewhere;
- repeated occurrence: suggest a durable reminder or handoff;
- chronic occurrence: create a small lifecycle-improvement ticket such as an email/Slack/Plane notification hook.

## Reporting

When handing off, say:

- what was blocked;
- what was advanced instead;
- what needs the human;
- what should be picked up next;
- which BMAD and Plane records were updated.
