# Handoff-Ready BMAD Story Template

Use this template when creating or promoting a BMAD story that another developer may implement without live context from Damian or Codex.

## Story Header

- BMAD story id: `PLC-E<epic>-S<story>`
- Plane issue: `CAF-<number>` / `<Plane issue URL>`
- Title: `<imperative, reviewer-readable title>`
- Status: `backlog | todo | in-progress | blocked | review | done`
- Owner: `<person/team/agent, if known>`
- Updated: `<YYYY-MM-DD>`
- Promoted from component history: `yes | no`
- Component source path: `<component BMAD path, PR, transcript, or none>`

## Source Intent

What Damian, Jarad, or the team meant in plain language.

- Primary user/operator need:
- Product outcome:
- Non-goals:
- Source artifacts:
- Open assumptions:

## User Story

As a `<user/operator/developer/system role>`, I want `<capability>`, so that `<outcome>`.

## Acceptance Criteria

- `<observable behavior or artifact>`
- `<data/state/API expectation>`
- `<privacy/safety/review boundary, if applicable>`
- `<Plane/BMAD parity expectation, if applicable>`

## Dependencies

- BMAD stories:
- Plane issues:
- PRs/branches:
- Environment/secrets/access:
- Runtime services:

## Implementation Notes

- Files/modules likely involved:
- Existing patterns to follow:
- Data model/storage notes:
- MCP/Hermes/workflow-artifact notes:
- Rollout or migration notes:
- Backward compatibility notes:

## Validation Plan

- Local commands:
- Unit/contract tests:
- Manual verification:
- GitHub CI expectations:
- Evidence to record before marking Done:

## Blocker Handling

Set status to `blocked` only after the lifecycle blocked policy is satisfied.

- Blocked: `yes | no`
- Reason:
- Owner:
- Since:
- Next useful unblocked work:

## Plane Mirror

Plane should summarize execution state only. BMAD remains authoritative for requirements.

- Plane title:
- Plane status:
- Plane comments to add:
- PR links:
- Drift/parity notes:

## Completion Evidence

Fill this before changing status to `done`.

- PR merged:
- CI result:
- Acceptance criteria verified:
- Evidence summary:
