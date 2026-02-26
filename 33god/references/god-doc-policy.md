# GOD Doc Policy

GOD docs are architecture truth, not optional prose.

## Rules

1. Read relevant system/domain/component GOD docs before 33GOD changes.
2. If implementation and docs differ, treat it as drift and fix docs in the same delivery cycle.
3. Do not ship architecture-affecting changes without corresponding doc updates.

## Minimum update set

- System-level changes → `docs/GOD.md`
- Domain-level changes → `docs/domains/{domain}/GOD.md`
- Component-level changes → `{component}/GOD.md`

## Verification

Include doc-drift verification in delivery report:
- files touched
- what changed
- why the architecture truth remains coherent

## Deep references

Use `god-docs` skill for full workflow/tooling.
