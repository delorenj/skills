---
pipeline-status: new
---
# Gotchas

## Use the tool, not hand-edits — key order is load-bearing

The vault and folder-curator schemas carry a deliberate key order. `frontmatters` now writes with
`sort_keys=False` (fixed — it used to alphabetize and strip comments on every write). Hand-editing YAML
frontmatter risks reintroducing disorder and dropping the exact shape the pipeline expects. Always go
through `frontmatters set` / `apply-base`.

## `apply-base` places empty keys as `''`, not bare/null

Missing keys with no schema default are stamped as `key: ''` (explicit empty placeholder), not bare
`key:` (null) as some vault templates show. Both are valid; `''` is unambiguous "awaiting a value." Set
a real value with `set` when you have one; don't rely on the placeholder meaning null.

## Batch your writes — one `set` call, many keys

`frontmatters set FILE a=1 b=2 c=3` writes the file once. Calling `set` (or the old
`update_frontmatter`) once per key rewrites the file N times. Always pass all key=values in a single
`set`.

## Value coercion is YAML-flavored

`set key=value` coerces the value via `yaml.safe_load`: `true`→bool, `3`→int, `[a, b]`→list,
`2026-07-18`→date, empty→null. To force a string, quote it in YAML terms (`set k="'2026-07-18'"`), or set
a plain word (stays a string). Watch dates: `captured=2026-07-18` becomes a YAML date — fine for
frontmatter, but if a schema wants a string, quote it.

## Don't cross the two schemas

Validating a vault file against the folder-curator `pipeline-status` enum (or vice versa) fails
spuriously — the enums differ (`ready/hitl/queued` vs `processing/blocked`). Always pass the `--schema`
that matches the file's directory. See base-schema.md.

## Run AFTER type + entity are set

This node assumes `category`/`kind` (folder-curator) and the entity label (domain-triage) already exist.
Running enrichment first means the base skeleton stamps empty `category`/entity, and your context-aware
values have no anchor. Order the pipeline: type → entity → enrich.

## Don't overwrite provenance

`source`, `captured`, `vault-id`, `created_at` describe how/when the file arrived. Enrichment adds
meaning on top; it must not rewrite provenance. `apply-base` won't (it never clobbers); be careful with
explicit `set` — don't set provenance keys unless correcting a known error.
