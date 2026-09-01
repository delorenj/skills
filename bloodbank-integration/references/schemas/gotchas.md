# Schemas — gotchas

Each gotcha is structured as: **Symptom**, **Cause**, **Fix**, **Prevention**.

## 1. `mise run smoketest:schemas` fails after a schema edit

**Symptom.** `validate:schemas` succeeds but `smoketest:schema-contract-consistency` or `smoketest:bloodbank-naming` fails.

**Cause.** JSON Schema syntax is valid, but the schema's contract-facing fields do not match the Bloodbank naming contract.

**Fix.** Check `$id`, `properties.type.const`, `properties.kind.const`, and the schema path under `schemas/bloodbank/<domain>/`. A common miss: `type.const` still carrying a `v1` token — the contract type is 4 tokens, `bloodbank.<domain>.<entity>.<action>`.

**Prevention.** Run `mise run smoketest:schemas` before pushing; don't run just `validate:schemas`.

## 2. Schema validator passes but producers fail at runtime

**Symptom.** `mise run validate:schemas` is green; a producer emits an envelope that the hook contract validator rejects.

**Cause.** The schema's `const` for `type` doesn't match what the producer is passing. Most often a copy-paste from a sibling schema where the `type` const wasn't updated.

**Fix.** Open the schema, confirm `properties.type.const` matches the dotted name everywhere: `$id`, `type` const, `schemaref`, and the derived NATS subject.

**Prevention.** Add a quick assertion in the producer (`assert envelope.type == "bloodbank.agent.session.started"`) until you trust the schema.

## 3. `allOf` extension doesn't add base fields to the generated model

**Symptom.** The generated Pydantic class is missing `specversion`, `id`, etc. from `cloudevent_base.v1.json`.

**Cause.** The `$ref` path is wrong (relative path mistake) or the base schema's `$id` URL doesn't match.

**Fix.** Use the relative-path form (`{ "$ref": "../../_common/cloudevent_base.v1.json" }`) — two levels up from `schemas/bloodbank/<domain>/`. Match the working examples in `schemas/bloodbank/agent/*.json`.

**Prevention.** Copy a working sibling schema as the starting point; never bootstrap an `allOf` block from scratch.

## 4. Two services disagree on the shape of an event

**Symptom.** Producer publishes `bloodbank.agent.session.started` with a v2 `schemaref`; consumer crashes parsing fields it expects from v1 (or vice versa).

**Cause.** A payload changed but the `dataschema` / `schemaref` revision (or the producer/consumer's import path) wasn't updated with it.

**Fix.** Decide whether the fact changed. If it did, it earns a new `action`/`entity` — a new type, a new subject, a new file — and the old one keeps flowing until nothing emits it (event-naming.md §3.1). If it did not, it is a compatible revision: bump `dataschema`/`schemaref` and leave the address alone.

**Prevention.** Land schema version bumps in a single commit that updates the producer, consumer, AND the schema file. The CI's drift check enforces the producer/consumer side at compile time.

## 5. Schema file isn't picked up by the validator

**Symptom.** New `bloodbank/schemas/bloodbank/<domain>/foo.bar.json` exists but `mise run validate:schemas` ignores it.

**Cause.** Either (a) the file is in a directory the validator doesn't traverse, or (b) the `$id` is malformed and the validator skipped it with a warning.

**Fix.** Confirm the file lives under `schemas/bloodbank/<domain>/` (not directly under `schemas/`, and not under a `v1/` tier — that tier no longer exists). Tail `mise run validate:schemas` output for skipped-file warnings.

**Prevention.** Mirror the layout of an existing schema directory exactly — validator conventions are positional.
