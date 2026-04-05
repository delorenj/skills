---
pipeline-status:
  - new
---
# Workflow: Event/Command Contract Rollout

Deterministic runbook for introducing or pruning contracts.

## Inputs

- Ticket/directive ID
- Contract name and type (event or command)
- Producer and consumer owners

## Steps

1. **Contract spec drafted**
   - Define routing key, payload, required fields, and lifecycle outcomes.
2. **Holyfields updated first**
   - Add/update/remove schema file(s).
3. **Generate + drift gate**
   - Regenerate bindings and run drift checks.
4. **Producer wiring**
   - Emit valid envelope/command payload with required metadata.
5. **Consumer wiring**
   - Subscribe/handle success and failure paths.
6. **Holocene/Test Board update**
   - Add to vetted allowlist if approved for active use.
   - Validate linear event journey indicators.
7. **Verification package**
   - Publish test, stream visibility, persistence, consumer behavior.
8. **Docs + ownership**
   - Update impacted GOD docs and note ownership.

## Exit criteria

- Contract is schema-backed, wired, observable, and verified end-to-end.
- No schema drift remains.
- Deprecated contracts are removed from active registry and vetted UI.
