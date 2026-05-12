---
name: tflo-verify
description: Verify workflow for the tflo (Intelliforia Trello Flow) module. Runs the type-aware verify standard (tests + lint + typecheck + AC for code; deliverable review for discovery/design/doc) and decides whether to pass to create-pr, retry implement, or escalate after 3 failed cycles.
---

# tflo-verify — Decide pass / retry / escalate

## Overview

Reads the active ticket type from `current-ticket.md` and runs the appropriate verify standard. Outputs a decision: `pass` (transition to `pr-ready`), `retry` (transition back to `implementing`, increment retry count), or `escalate` (after 3 retries — pause for human).

Failure context is structured JSON written to `verify-log.md` so the next implement cycle can feed it back to the architect consult.

## Preconditions

- `_bmad/memory/tflo/current-ticket.md` exists with `phase: verifying`
- The expected deliverables for the ticket type exist (commits + story.md for code, deliverable.md for discovery, etc.)
- Test/lint/typecheck commands are configured (defaults: `mise run test`, `mise run lint`, `mise run typecheck`)

## Type-routing matrix

| Type | Verify standard |
|---|---|
| `code`, `feature` | tests pass + lint clean + typecheck clean + every AC in story.md done/n-a |
| `bug` | regression test exists and passes + tests pass + lint + every AC done/n-a |
| `refactor` | tests pass (same set as before) + lint + behavior-equivalence assertion in commit message or story |
| `discovery` | `deliverable.md` exists, non-empty, and architect/reviewer subagent rates it pass (rubric: clear findings, actionable recommendations, no factual errors) |
| `design` | `design.md` (or excalidraw export) exists, ux-designer subagent rates it pass (rubric: matches stated user goals, accessibility considered, consistent with existing design system) |
| `doc` | new doc file exists under `docs/`, tech-writer subagent rates it pass (rubric: scannable, complete, concrete examples), doc-placement hook passes |

## Capabilities

### Run code-test verify (code/feature/bug/refactor)

```bash
mise run test       # tflo_test_command
mise run lint       # tflo_lint_command
mise run typecheck  # tflo_typecheck_command (skip if empty)
```

Capture exit codes and last 50 lines of output. Discover available commands via `mise tasks ls` if defaults fail.

For bugs additionally: assert that a regression test was added in the diff (grep new test files for keywords from the bug name).

### Acceptance-criteria checklist (code/feature/bug/doc)

Read AC items from `story.md`. For each, mark `done` / `not-done` / `n-a` based on:
- Reading the diff against `claimed_from_branch` to see what changed
- Running the test that maps to the AC if obvious
- For ambiguous AC: invoke `bmad-bmm-code-review` for an opinion

If any AC is unchecked and not n-a → fail.

### Deliverable review (discovery/design/doc)

Prefer the **inline spot-check rubric** over a full subagent re-review. Subagent verify costs ~50K tokens for a yes/no on a doc the prior subagent just produced; the failure modes that matter (fabricated file:line citations, unactionable recommendations, missing rubric items) are catchable in O(seconds) with a 4–5 sample inline check.

**Inline spot-check rubric (preferred path):**

1. **Existence + non-empty**: deliverable file exists at the expected path, ≥10 lines.
2. **Clear findings**: structured format with severity / problem / recommendation. For discovery: ≥10 findings expected. For design: explicit design decisions section. For doc: scannable structure (TOC, examples, headings).
3. **Actionable recommendations**: every finding has a concrete fix + effort sizing (S/M/L/XL, never time estimates).
4. **No factual errors**: pick 4–5 random file:line citations from the deliverable and spot-check against the actual code. If any citation is fabricated or wrong, fail the verify and feed the bad citations back to implement.
5. **Assumptions documented**: if the card description was empty or scope was ambiguous, the deliverable's "Assumptions" section must state what was assumed.

Score each rubric item `pass` / `fail` and write the structured result to `verify-log.md`.

**Escalate to subagent review only when:**
- Spot-check uncovers ≥2 fabricated citations (you need a real reviewer to determine the scope of the problem)
- The deliverable lacks structure entirely (no findings, no rubric framework) and inline scoring isn't possible
- Retry cycle 2+ and the prior cycle's deliverable was rubric-passing but rejected by the human downstream

Subagent fallback (if escalating):
- discovery → `bmad-agent-architect` or `bmad-bmm-architect.agent`
- design → `bmad-bmm-ux-designer.agent`
- doc → `bmad-bmm-tech-writer-tech-writer.agent`

Source: card #61 retro (2026-05-11). Full subagent re-review took ~76K tokens / 500s; inline spot-check produced the same verdict in <60s.

### Decide outcome

```
if any failure:
    if retry_count + 1 < 3:
        increment retry_count in current-ticket.md
        write structured failure context to verify-log.md
        transition phase to implementing
        invoke tflo-implement (which reads the failure context)
    else:
        write tickets/{id}/escalation.md with full failure history
        transition phase to escalated
        pause for human
else:
    transition phase to pr-ready
    invoke tflo-create-pr
```

## Failure context schema (verify-log.md entries)

```json
{
  "ticket": "<idShort>",
  "attempt": 2,
  "timestamp": "2026-05-07T14:30:00Z",
  "type": "code",
  "pass": false,
  "failed_tests": ["tests/api/test_x.py::test_y"],
  "failed_ac": ["AC-3: handles empty payload"],
  "lint_errors": [{"file": "...", "line": 42, "rule": "..."}],
  "typecheck_errors": [],
  "deliverable_review": null,
  "manual_smoke_required": false
}
```

For non-code types, `failed_tests` / `lint_errors` / `typecheck_errors` are empty arrays and `deliverable_review` carries the reviewer's structured feedback.

## Flaky test handling

Track per-test pass/fail history across attempts. If a test fails on cycle N but passed on N-1 with no relevant code change in the test or its target, mark as flaky. Do not count flaky failures toward the retry budget. Configurable threshold (default: 1 cross-cycle inversion = flaky).

## UI / extension changes

For tickets touching `extension/` or known-UI paths in the diff, write `manual_smoke_required: true` with the steps the human should run. The orchestrator decides whether to escalate or proceed.

## Failure modes

| Symptom | Action |
|---|---|
| Test command not configured | Run `mise tasks ls`, suggest the right one to user. Escalate. |
| AC items in story.md are too vague to check | Invoke code-review for an opinion. If still ambiguous, escalate. |
| Review subagent unavailable | Fall back to general-purpose Agent. Logged warning. |
| Lint reports issues in unrelated files | Filter to files in the diff. Lint errors outside diff don't fail verify. |

## Inputs

- `_bmad/memory/tflo/current-ticket.md`
- `_bmad/memory/tflo/tickets/{id}/story.md` (or deliverable / design / doc artifact)
- `_bmad/memory/tflo/verify-log.md` (prior attempts)
- Test/lint/typecheck commands from config

## Outputs

- New entry appended to `_bmad/memory/tflo/verify-log.md`
- Updated `current-ticket.md` (incremented retry_count + new phase)
- On escalation: `_bmad/memory/tflo/tickets/{id}/escalation.md`

## Handoff

- pass → `tflo-create-pr`
- retry → `tflo-implement`
- escalate → orchestrator pauses, surfaces escalation.md to user
