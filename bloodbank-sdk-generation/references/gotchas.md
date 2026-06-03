# Bloodbank SDK Generation — Gotchas

Load this only when generation fails with a non-obvious error or the output looks wrong. Each entry follows: **Symptom → Cause → Fix → Why**.

## 1. `datamodel-codegen: error: unrecognized arguments`

- **Symptom:** the command rejects flags like `--output-model-type` or `--enum-field-as-literal`.
- **Cause:** older `datamodel-code-generator` versions (pre-0.25) lack the Pydantic v2 surface and the const-as-literal flag.
- **Fix:** pin the floor — `uvx --from 'datamodel-code-generator>=0.25'`.
- **Why:** the Pydantic v2 backend was rewritten in 0.25; earlier versions emitted v1 BaseModel even with the v2 flag, producing import errors downstream.

## 2. Generated Python has `type: str` instead of `type: Literal["bloodbank.v1...."]`

- **Symptom:** the `type` field of each event class is typed as plain `str`, not as a literal of the const value.
- **Cause:** `--enum-field-as-literal` is missing or set to `all`.
- **Fix:** pass `--enum-field-as-literal one`. The `one` value means "fields with a single-value enum or const become `Literal[...]`"; `all` over-promotes everything and breaks open-ended enums.
- **Why:** Bloodbank's 5-token contract relies on `properties.type.const` being authoritative at the type level — that's what gives consumers compile-time / static-type guarantees against wrong event types.

## 3. `Could not resolve reference ../../../_common/cloudevent_base.v1.json`

- **Symptom:** datamodel-codegen or json-schema-to-typescript fails resolving the `_common` ref.
- **Cause:** running from the wrong working directory, or pointing `--input` at a single file instead of the tree root.
- **Fix:** run from the Bloodbank repo root; pass the directory `schemas/bloodbank/v1` (Python) or use `--cwd schemas` plus a glob over the v1 tree (TypeScript). The `$ref` walks up to `schemas/_common/`; both tools need `schemas/` in scope.
- **Why:** the schemas are authored against a fixed relative path. The generator's resolver root determines whether `../../../_common/` lands inside or outside the tree.

## 4. TypeScript output is one giant union with anonymous types

- **Symptom:** `types.ts` contains one or two top-level types and a forest of inline anonymous shapes.
- **Cause:** the `title` field on each schema is missing or generic.
- **Fix:** verify each schema has a distinct `title` (e.g. `"Conversation Message Appended Event"`). `json-schema-to-typescript` derives interface names from `title`, falling back to the file path when titles collide.
- **Why:** the Bloodbank schemas already set per-event titles; check for accidental duplicates if you've recently added a schema.

## 5. Generated TS uses `any` or `unknown` for the `data` payload

- **Symptom:** the per-event `data` field types as `unknown` or `any`.
- **Cause:** `additionalProperties: true` (or unset) on the `data` object in the schema, OR the schema doesn't constrain `data.properties`.
- **Fix:** in the source schema, set `additionalProperties: false` on `data` and declare `data.properties`. The generator can't infer a shape the schema doesn't declare.
- **Why:** the contract is "the schema is authoritative." If `data` is loose in the schema, the generated type is loose by design — fix the schema, not the generator.

## 6. Want `EVENT_TYPE` class constants in Python

- **Symptom:** the Holyfields-era generator emitted `EVENT_TYPE: ClassVar[str] = "bloodbank.v1..."` on each model; `datamodel-code-generator` does not.
- **Cause:** datamodel-code-generator emits the literal as the `type` field's annotation, not as a separate class constant.
- **Fix:** either (a) skip — consumers can reference `Model.model_fields['type'].annotation.__args__[0]` to get the literal value, or (b) post-process with a one-shot script that walks the generated file, finds each `type: Literal['...']`, and inserts `EVENT_TYPE: ClassVar[str] = '...'` on the class. Keep the post-processor checked in next to the regenerate command if you commit to (b).
- **Why:** the type-level literal already provides static guarantees; a runtime constant is convenience, not contract.

## 7. Output differs across runs even when schemas are unchanged

- **Symptom:** `git diff` shows the generated file changes between runs with no schema edits.
- **Cause:** dict-ordering or import-ordering nondeterminism in older generator versions, or the generator picked up a different jsonschema/referencing version.
- **Fix:** pin both the generator and its inputs. `uvx --from 'datamodel-code-generator>=0.25,<1' --with 'pydantic>=2.6'` keeps the resolution stable. Re-run `mise run validate:schemas` first to confirm input determinism.
- **Why:** SDK generation is a build step; treat it like a compiler with reproducible-output expectations.

## 8. Holyfields-era generators shouldn't be ported

- **Symptom:** thinking about copying `tools/generators/generate_pydantic.py` from the Holyfields repo.
- **Cause:** muscle memory from before the RECOMMENDATION.md fold-in.
- **Fix:** don't. The hand-rolled generator was 333 lines of bespoke code that no one else maintained; `datamodel-code-generator` is more capable, supports Draft 2020-12 properly, handles `$id` URLs correctly, and ships with a community.
- **Why:** the recommendation explicitly defers SDK generation; the third-party tools are the right answer once a real consumer needs an SDK.
