# Intent Capture Format

BMAD story: `PLC-E3-S1: Define intent capture format` (Plane `CAF-122`).

## Purpose

Intent capture is the layer between Damian's natural-language coaching method
and a versioned workflow artifact.

It is not the runtime workflow schema. That belongs to `CAF-123`. This format
captures enough structured intent for an engineer or artifact generator to
produce a reviewable workflow without inventing product rules.

## Path

```text
Damian's intent
  -> intent capture JSON
    -> workflow artifact generator/reviewer
      -> versioned workflow YAML/TOML
        -> Hermes conversational router
          -> generic MCP tools
            -> database state
```

## Files

- Schema:
  `workflow-artifacts/intent-capture.schema.json`
- Example:
  `workflow-artifacts/examples/messages-intent-capture.json`
- Validator:
  `skills/project-lifecycle/scripts/validate_intent_capture.py`

## Required Capture Areas

Each intent capture must include:

- source reference and capture date;
- phase or protocol ID/name/kind;
- phase purpose and operator intent;
- exact-language policy;
- ordered steps;
- prompts and whether exact wording must be preserved;
- expected answer type;
- strict mapped fields;
- loose notes;
- repeat/loop policy;
- duplicate policy;
- rating gates;
- coach approval gates;
- ambiguities that need human review.

## Strict Fields Versus Loose Notes

Use `strict_fields` for values the runtime should write into known database or
session fields, such as:

- starting migraine level;
- message count;
- final wellbeing level;
- objective rating.

Use `loose_notes` for captured meaning that should be remembered but is not yet
mapped to a stable schema, such as:

- exact subconscious message wording;
- emerging themes;
- possible follow-through guidance;
- coach nuance for a difficult step.

Loose notes are not a dumping ground for private coach/system context. The
later workflow artifact must still decide client-visible versus private use.

## Exact Language

When `preserve_exact_prompts` is true, the artifact generator must keep the
prompt wording unless a human reviewer approves a wording change.

Hermes may clarify what the current question means, but it must not invent new
coaching while an exact protocol step is active.

## Ambiguity Policy

If Damian's description leaves a runtime rule unclear, record it in
`ambiguities` instead of choosing a behavior silently. Good ambiguity entries
state:

- the unresolved question;
- why it matters;
- what downstream behavior would change.

## Validation

```bash
python3 skills/project-lifecycle/scripts/validate_intent_capture.py
python3 skills/project-lifecycle/scripts/test_validate_intent_capture.py
```

The validator uses Python standard library only. It checks required top-level
sections, step structure, answer types, loop policies, strict/loose capture
sections, and ambiguity entries. It is intentionally structural; it does not
try to validate coaching quality.
