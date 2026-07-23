# Lifecycle Operating Model

## Purpose

Project Lifecycle keeps the delivery pipeline moving while preserving a clear product truth. It is for the phase after a project exists: BMAD is initialized, the repo has code and planning artifacts, and the team needs repeatable movement from intent to tickets to PRs.

It does not own company strategy, project inception, or product discovery from a blank page. Those can be added later. Its first boundary is: initialize or verify BMAD, turn product intent into BMAD artifacts, mirror execution into Plane, choose the next work, and keep blockers from stalling the line.

## Lifecycle Loop

1. Inspect the current state.
   - Read `git status --short`.
   - Run or inspect BMAD status.
   - Inspect root `_bmad_output/planning-artifacts`.
   - Inspect Plane only after BMAD context is understood.
   - Inspect open PRs or recent branches when current work is unclear.

2. Identify the authoritative work item.
   - Prefer a BMAD story with acceptance criteria.
   - If only a Plane issue exists, create or update the matching BMAD story before substantial implementation.
   - If the user provides raw intent, produce a BMAD planning artifact first, then mirror execution tickets.

3. Choose the next action.
   - If the user says "continue", continue the active ticket/story.
   - If the user says "what ticket next?", choose the highest-leverage unblocked item.
   - If a dependency is blocked, record it and switch to the next safe item.

4. Execute.
   - Make scoped code/doc/ticket changes.
   - Keep BMAD story status and Plane issue status aligned.
   - Run verification appropriate to the work.

5. Handoff.
   - Report changed files, BMAD artifacts, Plane issues, tests, known blockers, and next recommended action.
   - For dev-team handoff, include acceptance criteria and validation commands.

## North Star Pillars

- BMAD is truth; Plane is visibility.
- Keep the pipeline moving.
- Prefer explicit acceptance criteria over vibes.
- Prefer autonomy when the decision is reversible and bounded.
- Ask the user only when product intent, credentials, or irreversible choices are genuinely required.
- Log blockers where future operators will see them.
- Preserve privacy and secrets. Never expose API keys or tokens in tickets, docs, or logs.

## Human In The Loop

Ask the human when:

- a product decision changes client experience or coaching method semantics;
- access, credentials, or login are required;
- data deletion, production mutation, or irreversible change is proposed;
- acceptance criteria conflict;
- Plane and BMAD disagree and neither is clearly newer.

Do not ask the human when:

- an implementation choice is routine and reversible;
- tests or formatting are needed;
- a lower-risk unblocked ticket can be advanced while waiting;
- the user has explicitly delegated next-ticket triage.

## Done Definition

A lifecycle item is done only when:

- BMAD story acceptance criteria are met or deliberately revised;
- Plane status reflects the BMAD story state;
- verification has run or the reason it could not run is recorded;
- code/docs/tickets are ready for review;
- blockers and follow-ups are captured rather than hidden in chat.
