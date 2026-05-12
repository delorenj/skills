---
name: tflo-implement
description: Implementation workflow for the tflo (Intelliforia Trello Flow) module. Routes the active ticket through the appropriate subagent chain based on its detected type (code/bug/feature/refactor/discovery/design/doc), produces the deliverable artifacts (architect plan, test plan, dev story, code commits OR analysis doc OR design doc), and transitions the FSM from implementing to verifying. The type field in current-ticket.md determines which chain runs.
---

# tflo-implement — Build the deliverable for the active ticket

## Overview

Routes the active ticket through a type-aware subagent chain and produces the deliverable artifacts. For code-shaped tickets that means: research → architect plan → test plan → dev story → commits. For non-code tickets (discovery, design, doc) the chain skips test/code generation and produces a different artifact.

All subagent invocations originate from this skill (the orchestrator runs the Skill / Agent tools). Subagent outputs land in `_bmad/memory/tflo/tickets/{idShort}/`.

## Preconditions

- `_bmad/memory/tflo/current-ticket.md` exists with `phase: implementing`
- Branch in current-ticket.md is checked out (`git rev-parse --abbrev-ref HEAD` matches `branch`)
- `type` field is populated (set at claim by detect_ticket_type)

If preconditions fail, abort or fix manually. Don't silently re-detect type — it would diverge from the recorded value.

## Autonomous-mode contract

This SKILL runs autonomously end-to-end. NEVER use `AskUserQuestion`. Every fork in the road has a defensible default; pick it and document the assumption.

When the card description is empty or scope is ambiguous:
1. Pick the highest-confidence default scope (e.g., "Provider Portal" for a portal-UX ticket where the codebase has two portals).
2. Post a Trello comment stating the assumption: `🤖 tflo-implement: card description empty. Assuming scope = X. Abort and re-scope if wrong.`
3. Document the assumption in the deliverable's "Assumptions" section.
4. Proceed.

When confidence is genuinely too low to pick a default (e.g., the ticket requires a credential or business decision only the human can give):
1. Run `mise run tflo abort --yes --reason "<why>"` to release the ticket.
2. Re-run triage to claim something tractable.
3. Do NOT pause for HITL.

When subagents disagree (architect vs test-engineer, etc.):
- Architect plan is the source of truth. Test engineer adapts. If irreconcilable, escalate via `tickets/{id}/escalation.md` and stop — but that's a true escalation, not a question.

Source of this contract: `feedback_tflo_autonomous_no_clarification.md` in user memory, learned from card #61 (Provider Portal UX review, 2026-05-11).

## Type-routing matrix

| Type | Chain | Deliverable | Branch lands code? |
|---|---|---|---|
| `code`, `feature` | architect → tea → create-story → dev-story | commits + story.md + plans | yes |
| `bug` | architect (root-cause) → tea (regression test required) → create-story → dev-story | commits including failing-then-passing regression test + story.md | yes |
| `refactor` | architect (scope assessment) → dev-story (no behavior change) | commits + brief story.md (no AC change) | yes |
| `discovery` | ui-ux-designer (for UX) or architect (for everything else) → produce deliverable | `docs/domains/<area>/YYYY-MM-DD-<slug>.md` + memory-bank copy | yes (commit the doc) |
| `design` | bmad-bmm-ux-designer.agent → produce design | `docs/domains/<area>/YYYY-MM-DD-<slug>-design.md` + memory-bank copy | yes (commit the doc) |
| `doc` | bmad-bmm-tech-writer-tech-writer.agent → produce doc in `docs/` | new file in `docs/<area>/<title>.md` | yes (commit the doc) |

## Capabilities

### Research (all types except trivial bugs)

Read the card description, scan related code paths, surface relevant files. Save findings to `_bmad/memory/tflo/tickets/{idShort}/research.md`.

For code-typed tickets: grep for symbols mentioned in the card name; read tests in the affected area; check git log for recent activity. For discovery/design: read the user-facing context (UI screens, related Trello cards). For doc: locate the existing docs the new content should live near.

### Architect consult (all types)

Invoke the architect subagent with this brief:

```
You are reviewing ticket [idShort]: <name>
Type: <type>
Description: <card.desc>
Research findings: <research.md path>
Prior verify failure (if cycle ≥ 2): <verify-log.md last entry, structured>

Produce a plan with:
- Goal restated in 1 sentence
- Approach (numbered steps)
- Alternatives considered (and why rejected)
- Risks / non-obvious considerations
- For non-code tickets: success criteria for the deliverable artifact (no AC checklist)

Write to tickets/{idShort}/architect-plan.md.
```

Subagent: `bmad-bmm-architect.agent` (Winston). Falls back to general-purpose if the BMAD agent isn't installed.

### Test engineer consult (code/feature/bug only)

Skip for refactor (tests already exist; just must keep passing), discovery, design, doc.

Invoke `bmad-bmm-tea.agent` (Murat) with this brief:

```
You are designing tests for ticket [idShort]: <name>
Type: <type>
Architect plan: <architect-plan.md path>

Produce a test plan with:
- Unit tests (function/class level)
- Integration tests (component boundaries)
- E2E / smoke tests if user-facing
- For bugs: a regression test that fails on current main and passes after the fix
- Coverage targets (if measurable)

Write to tickets/{idShort}/test-plan.md.
```

### Story creation (code/feature/bug/refactor/doc)

Invoke `bmad-bmm-create-story` with the architect plan + test plan as input. Output is a BMAD-format story at `tickets/{idShort}/story.md` with explicit acceptance criteria.

For discovery and design: skip story creation. The deliverable doc IS the story.

### Implement / produce deliverable

Type-routed:
- **code/feature/bug/refactor**: invoke `bmad-bmm-dev-story` with the story file. Commits land on the active ticket branch.
- **discovery**: invoke the right specialist subagent for the card label (`ui-ux-designer` for UX-labeled, `architect-review` for system/architecture, `general-purpose` otherwise) to write the deliverable. Write to `docs/domains/<area>/YYYY-MM-DD-<slug>.md` (NOT the gitignored memory bank — keep a memory-bank copy at `tickets/{id}/deliverable.md` for archive). Commit the doc to the ticket branch so it ships with the PR.
- **design**: invoke `bmad-bmm-ux-designer.agent` to produce design doc / mockup. Write to `docs/domains/<area>/YYYY-MM-DD-<slug>-design.md`. Optionally use `bmad-bmm-create-excalidraw-wireframe` for visuals. Commit to the ticket branch.
- **doc**: invoke `bmad-bmm-tech-writer-tech-writer.agent` to write the documentation file in `docs/<area>/<title>.md`. Commit the file to the ticket branch.

**Why the docs/ path matters**: `_bmad/memory/tflo/tickets/` is gitignored. Anything written only there will not ship with the PR. Discovery/design/doc deliverables must land in a non-ignored path. Keep a memory-bank copy for local archive, but it is not the artifact-of-record.

### Hand off to verify

Update `current-ticket.md` to `phase: verifying`. Append transition. Invoke `tflo-verify`.

## Retry behavior (cycle 2 or 3)

If the orchestrator re-enters this skill because verify failed and `retry_count < 3`:

1. Read the last entry in `verify-log.md`
2. Feed the structured failure context into the architect consult: "Cycle {N} of 3. Previous verify failed on: {failed_tests}, {failed_ac}, {lint_errors}. Refine the plan."
3. Architect produces a refined plan (overwrites `architect-plan.md` with a new section)
4. Re-run the appropriate subagent chain from architect onwards
5. Increment `retry_count` in current-ticket.md

If `retry_count` would exceed 3, escalate to human instead of re-running.

## Failure modes

| Symptom | Action |
|---|---|
| Architect returns "ticket as written cannot be done" | True escalation. Write `tickets/{id}/escalation.md` with the architect's reasoning. Transition phase to `escalated`. Stop. |
| Test engineer and architect disagree on approach | Architect plan wins. Comment on the Trello card noting the disagreement + the chosen path. Do not pause. |
| dev-story produces commits that don't match story AC | Hand to verify anyway with the mismatch noted in the transition log; verify will catch it via the AC checklist and either retry (cycle < 3) or escalate (cycle = 3). |
| Card description is empty / scope is ambiguous | Apply the autonomous-mode contract (above): pick highest-confidence default, comment on card with assumption, proceed. If confidence too low to pick, abort + retriage. |
| Subagent invocation errors out | Retry once. If still failing, escalate via `tickets/{id}/escalation.md`. |
| Doc/design subagent unavailable | Fall back to general-purpose Agent with appropriate persona prompt. Log warning. |

## Inputs

- `_bmad/memory/tflo/current-ticket.md` (active ticket)
- `_bmad/memory/tflo/verify-log.md` (if retry)

## Outputs

Memory-bank artifacts (local archive only, gitignored):
- `_bmad/memory/tflo/tickets/{id}/research.md`
- `_bmad/memory/tflo/tickets/{id}/architect-plan.md`
- `_bmad/memory/tflo/tickets/{id}/test-plan.md` (code/feature/bug only)
- `_bmad/memory/tflo/tickets/{id}/story.md` (code/feature/bug/refactor/doc)
- `_bmad/memory/tflo/tickets/{id}/deliverable.md` (discovery, memory copy)
- `_bmad/memory/tflo/tickets/{id}/design.md` (design, memory copy)

Committed artifacts (ship with the PR):
- Code commits on the ticket branch (code/feature/bug/refactor only)
- `docs/domains/<area>/YYYY-MM-DD-<slug>.md` (discovery)
- `docs/domains/<area>/YYYY-MM-DD-<slug>-design.md` (design)
- `docs/<area>/<title>.md` (doc)

FSM + side effects:
- Updated `current-ticket.md` with `phase: verifying`
- Appended entry in `tickets/{id}/transitions.jsonl`
- Comment on the Trello card summarizing what was implemented

## Handoff

After successful implement, the orchestrator invokes `tflo-verify`.
