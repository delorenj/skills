# Manifests

Global selection lives in `~/.agents/skills.json`; project selection lives in
`<repo>/.agents/skills.json`. This host selects the `min-global` set globally.

## Selection semantics

The user's 2026-10-10 definitions govern both scopes:

- A **set** replaces `.agents/skills/` with a symlink to that set's skill root.
  Sets are mutually exclusive, not composable member lists.
- A **pack** populates the existing `.agents/skills/` root with per-skill symlinks.
  Multiple packs compose; selecting a pack does not replace the root.

`all-skills/` owns definition bytes. It is not the canonical discovery root.

Inspect the live schema and installed resolver to identify compatibility, not to
redefine these terms. Legacy code may allow multiple sets and make one pack an
exclusive root replacement: that is reversed behavior. Do not recommend a set
as an additive workaround or a pack as a replacement workaround. Report the
mismatch and do not apply a contradictory sync plan.

The core definitions do not settle inheritance precedence, duplicate-name
conflicts, or how scope-local additions interact with a shared set target. Do
not silently mutate a shared set through its root alias; obtain the missing
policy before applying that combination.

Remove set defaults in the owning set, not by deleting a generated symlink. An
optional capability can remain in the catalog without being globally selected.
