# Schemas — gotchas

Each gotcha is structured as: **Symptom**, **Cause**, **Fix**, **Prevention**.

## 1. `mise run check:drift` fails after a generate

**Symptom.** `generate:all` succeeds but `check:drift` says generated files differ from schemas.

**Cause.** Either (a) a stale generated file wasn't deleted before regeneration, or (b) the generator's deterministic output changed (rare, signals a generator-tools bump worth flagging in an ADR).

**Fix.** `git clean -fdx holyfields/packages/*/src/generated/` then `mise run generate:all`. Commit the result.

**Prevention.** Run `mise run ci` (which chains validate → generate → drift → tests) before pushing; don't run just `generate:all`.

## 2. Schema validator passes but producers fail at runtime

**Symptom.** `mise run validate:schemas` is green; a producer using the generated model raises a `pydantic.ValidationError`.

**Cause.** The schema's `const` for `type` doesn't match what the producer is passing. Most often a copy-paste from a sibling schema where the `type` const wasn't updated.

**Fix.** Open the schema, confirm `properties.type.const` matches the dotted name everywhere — filename, `$id`, `type` const, NATS subject.

**Prevention.** Add a quick assertion in the producer (`assert envelope.type == "agent.session.started"`) until you trust the schema.

## 3. `allOf` extension doesn't add base fields to the generated model

**Symptom.** The generated Pydantic class is missing `specversion`, `id`, etc. from `cloudevent_base.v1.json`.

**Cause.** The `$ref` path is wrong (relative path mistake) or the base schema's `$id` URL doesn't match.

**Fix.** Use the relative-path form (`{ "$ref": "../_common/cloudevent_base.v1.json" }`) — match the working examples in `agent/*.v1.json`.

**Prevention.** Copy a working sibling schema as the starting point; never bootstrap an `allOf` block from scratch.

## 4. Two services disagree on the version of an event

**Symptom.** Producer publishes `agent.session.started` v2; consumer crashes parsing fields it expects from v1 (or vice versa).

**Cause.** Schema bumped to `.v2.json` but `dataschema` URIs (or the producer/consumer's import path) wasn't updated together.

**Fix.** Decide on a cutover plan. Either: (a) run both v1 and v2 schemas in parallel until all consumers migrate, then drop v1; or (b) keep v1 as the wire schema and version internally.

**Prevention.** Land schema version bumps in a single commit that updates the producer, consumer, AND the schema file. The CI's drift check enforces the producer/consumer side at compile time.

## 5. Schema file isn't picked up by the generator

**Symptom.** New `holyfields/schemas/<domain>/foo.bar.v1.json` exists but no Python/TS class is generated.

**Cause.** Either (a) the file is in a directory the generator doesn't traverse, or (b) the `$id` is malformed and the generator skipped it with a warning.

**Fix.** Confirm the file lives under `schemas/<domain>/` (not `schemas/`). Tail the `generate:all` output for skipped-file warnings.

**Prevention.** Mirror the layout of an existing schema directory exactly — generator conventions are positional.
