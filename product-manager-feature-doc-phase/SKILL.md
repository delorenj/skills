---
name: product-manager-feature-doc-phase
description: FeatureDocPhase for ProductManager discovery. Use to write detailed PRD-like feature docs from a selected candidate, including problem framing, evidence, goals, non-goals, UX requirements, data/API notes, acceptance criteria, risks, rollout, metrics, dependencies, and implementation handoff. Triggers on FeatureDocPhase, PRD-like feature doc, product requirements, feature spec, acceptance criteria, implementation-ready candidate, and write the chosen feature. Do NOT use for raw ideation or broad reports.
---

# ProductManager FeatureDocPhase

FeatureDocPhase turns one selected candidate into a detailed, implementation-ready product document. It is not a build plan, but a dev team should be able to estimate from it without guessing the product intent.

## Inputs

Read:

- `candidate-matrix.md`
- `research.md`
- `evidence-log.md`
- Any user selection or override
- Relevant source files or UI routes for the chosen feature

If no candidate is selected, choose the top-ranked candidate and state that assumption.

## Feature Doc Template

Create `features/<candidate-slug>.md`:

```markdown
# [Feature Name]

## Summary

## User Problem

## Evidence
- Product evidence:
- Mock-use or visual evidence:
- External research:
- Assumptions:

## Goals

## Non-Goals

## User Stories

## Current Experience

## Proposed Experience

## UX Requirements

## Data and System Notes

## Acceptance Criteria

## Analytics or Success Signals

## Risks and Mitigations

## Rollout / Migration Notes

## Open Questions

## Implementation Handoff Notes
```

## Acceptance Criteria Rules

Acceptance criteria must be testable:

- Use observable behavior, not intentions.
- Include empty, loading, error, and edge states when relevant.
- Name permissions, data freshness, and idempotency expectations if the feature touches data.
- Include at least one negative case.

## Handoff Standard

The feature doc is ready when:

- A developer can point to the primary routes/components/data flows likely affected.
- The owner can tell what is deliberately out of scope.
- The expected user-visible change is obvious.
- Open questions are explicit, not buried in prose.

## Out of Scope

- **Broad candidate ranking:** use `product-manager-brainstorm-phase`.
- **Implementation plans or code edits:** hand off to dev, architecture, or planning skills after approval.
- **Final run summary:** use `product-manager-report-phase`.
