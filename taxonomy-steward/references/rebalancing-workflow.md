---
pipeline-status: new
---
# Minting & rebalancing — the workflow

Both modes (mint a schema, or run a health pass) converge on the same recommend → approve → apply loop.
The distinctive decision is **local-fit vs. global-rebalance**.

## Local-fit vs. global-rebalance

When you design or change a schema, always compute BOTH options and present the trade-off:

- **Local-fit** — define the schema using only what exists (base + current extensions), adding the
  minimum new fields. Zero migration cost; risk: reinforces existing imbalance (e.g. adds yet another
  `*-name` field instead of unifying).
- **Global-rebalance** — additionally modify the existing set: hoist a now-recurring field to the base,
  push a misplaced base field down, merge near-duplicate fields, promote an emergent tag to a facet.
  Higher migration cost; payoff: the whole set gets healthier and the new schema is smaller.

Choose global-rebalance when the same pressure shows up in ≥2 places or a metric is in the alarm zone;
choose local-fit for a one-off that doesn't recur. When in doubt, present both with blast-radius counts
and let the human pick.

## The operations

- **Hoist** a field to the base when it recurs across schemas with healthy fill.
- **Push-down** a base field into the one extension that uses it (low global fill).
- **Merge** near-duplicate fields/tags to a canonical form; alias the old.
- **Promote** a recurring/emergent tag to a typed facet (field + value set).
- **Consolidate** an enum: define the canonical value set, map variants, validate on write.
- **Normalize** naming to one casing; alias strays.
- **Prune** singleton tags and orphan fields that aren't deliberate.
- **Reconcile** diverging conventions (or explicitly scope each and document the boundary).

## Mint a schema (mode 1)

1. Measure the target dir (`schema_health.py <dir>`) and read its representative files.
2. Inventory the full existing schema set (base + all extensions).
3. Draft the **local-fit** schema: reuse base/shared fields, add only genuinely-new ones.
4. Check each new field against the set: does it recur elsewhere (→ hoist candidate)? Is it an emergent
   tag pattern (→ facet-promote instead of a tag)? Produce the **global-rebalance** alternative.
5. Emit the review artifact with both options + migration costs.

## Health pass (mode 2)

1. `schema_health.py <vault>` (+ `--recent-days N` for drift).
2. Map every finding to references/health-phenomena.md.
3. Prioritize: alarms first, highest-value/lowest-cost first.
4. For each, specify the operation + the migration (files affected, the `frontmatters` commands).
5. Emit the artifact.

## Recommend → approve → apply (mirrors folder-curator structure-evolution)

- **Recommend:** write the artifact (assets/report-template.md) — diagnosis, proposed schema/diff,
  migration plan with blast-radius counts. Never apply unprompted.
- **Approve:** human reviews and picks (local-fit vs rebalance, which fixes).
- **Apply (one coherent pass):** update the contract(s) (`frontmatter-category-map.json` and/or the
  `.curator/taxonomy.yaml` `frontmatter:` block); migrate existing notes with the enrichment tool —
  `frontmatters set` (rename/merge values), `frontmatters apply-base --schema <new>` (add hoisted keys),
  `frontmatters validate --schema <new>` (confirm). Then **re-measure** to verify the metric moved.
- Record the decision (a Hindsight retain / a decisions/ entry) so the rationale survives.

## Migration tactics

- Prefer **additive + aliased** changes (add canonical, alias old) over destructive renames.
- Batch per operation; keep each migration reversible where possible.
- Do it in one pass so the tree is never half-migrated (inconsistent state is worse than either state).
