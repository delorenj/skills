# Workflow Generation

Use this when the user gives a semantic workflow request and expects implementation artifacts.

Example trigger:
- "Watch a directory, process files, publish events"

## Generation flow

1. Classify complexity (simple/medium/complex).
2. Select architecture (Python-only vs hybrid orchestrated flow).
3. Define events, contracts, and routing.
4. Generate implementation artifacts.
5. Wire registry/subscriptions.
6. Produce verification steps.

If the request is primarily about contract lifecycle (new event/command, versioning, or pruning), route to:
- `event-command-lifecycle.md`

## Output package should include

- Architecture summary
- Event contract list
- Implementation artifacts (scripts/services/flow config)
- Registration/config changes
- Test/validation checklist

## Deep references

If needed, load standalone specialist skill:
- `33god-workflow-generator` (compatibility shim → this reference)
