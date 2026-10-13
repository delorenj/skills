# Manifests

Global selection lives in `~/.agents/skills.json`; project selection lives in
`<repo>/.agents/skills.json`. This host's global selection is **composed** (no
set): the `bmad@6.12.1-next.1` pack plus explicit members. The legacy two-set
selection was normalized on 2026-10-13 — a whole-root set switch is refused
while installer-owned (`.system`) and foreign content share the root, so exact
membership preservation meant composing, not switching.

## Manifest shape

Use optional `"set": "name"` string; omission means no selected set. Never emit
`sets: ["name"]`, an array-of-one, an object, or null. `packs` remains an array.
Legacy `sets` belongs only in explicit normalization/migration input. Convert a
singleton through `skillex normalize` (preview, then `--apply`); multiple legacy
sets require an explicit membership-preserving base decision, not picking one.

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

The user chose scope-owned derivation for additions to shared set-backed roots:
create/select a derived set and add pack links there without changing the base
or other consumers. A project set replaces inherited Skillex selection while
leaving global roots intact. Agent discovery suppression is separate; use a
verified client adapter and never claim resolver inheritance proves isolation.
Normalization preserves exact membership, folds complete member groups into
packs, and refuses ambiguous legacy intent. Repeated individual global members
should become the global-set reference, not another long list.

Remove set defaults in the owning set, not by deleting a generated symlink. An
optional capability can remain in the catalog without being globally selected.
