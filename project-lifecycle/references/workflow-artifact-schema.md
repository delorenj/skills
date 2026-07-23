# Workflow Artifact Schema

BMAD story: `PLC-E3-S2: Draft workflow artifact schema` (Plane `CAF-123`).

## Purpose

The workflow artifact is the runtime contract between reviewed coaching intent
and Hermes/MCP execution.

Intent capture records what Damian meant. A workflow artifact records what the
system may actually run: prompts, step order, gates, transitions, storage
targets, and version pinning.

## Files

- Schema: `workflow-artifacts/workflow-schema.json`
- Example directory: `workflow-artifacts/workflow-examples/`
- First example: `workflow-artifacts/workflow-examples/messages-workflow.v1.json`
- Validator: `skills/project-lifecycle/scripts/validate_workflow_artifacts.py`

## Runtime Requirements

Each workflow artifact must include:

- `workflow_id` and immutable `version`;
- source intent ID;
- phase or protocol identity;
- session state scope and version pinning;
- known fields and storage targets;
- ordered steps with stable step IDs and field IDs;
- exact prompt text;
- answer types;
- repeat and duplicate policies;
- clarification behavior that can refuse advancement;
- completion gates;
- transitions to the next step or `complete`.

## Session Pinning

`session.pin_workflow_version` should be true for client-facing workflows. That
lets an active client session finish on the same workflow version even if
Damian or the dev team approve a newer artifact later.

## Validation

```bash
python3 skills/project-lifecycle/scripts/validate_workflow_artifacts.py
python3 skills/project-lifecycle/scripts/test_validate_workflow_artifacts.py
```

The validator is deliberately structural. It makes sure examples are present,
top-level sections exist, step IDs and field IDs are unique enough to route,
step fields exist in `fields`, transitions point to known steps or `complete`,
rating gates declare 0-10 bounds, and clarification behavior says whether a
clarification advances the state.
