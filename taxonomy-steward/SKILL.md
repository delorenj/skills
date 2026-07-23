---
name: taxonomy-steward
description: "Design a balanced schema for a directory and keep the vault's whole taxonomy healthy — the governance layer above folder-curator / domain-triage / frontmatter-enrichment. Mints a schema against the entire existing set (local-fit vs global rebalance: hoist / push-down / promote-tag-to-facet), and mitigates decay: tag explosion / singleton fat-tail (notes:tag ratio → 1), near-duplicate & case-collision tags, enum/value sprawl, orphan fields, base bloat, naming drift, cross-schema divergence — measure-first, human-approved, migration-aware. Manually invoked; ships scripts/schema_health.py. Use when adding a directory/domain schema, auditing vault/tag/schema health, fixing tag explosion, consolidating or pruning tags, rebalancing fields, or promoting a tag to a field. Do NOT use to apply a schema to a file (frontmatter-enrichment), type a file (folder-curator), route to an entity (domain-triage), or manage memory (hindsight). Biases: measure first, controlled vocabulary over folksonomy, DRY, never auto-apply."
pipeline-status: new
---

# Taxonomy Steward

The gardener for the whole classification system. Two jobs: **mint** a well-balanced schema for a new
directory *in the context of every existing schema*, and **keep the taxonomy healthy** as it drifts —
tags, fields, enums, and naming. Measure-first, human-approved, migration-aware.

## Operating principles

- **Measure before you touch.** Run `scripts/schema_health.py` and read the numbers; opinions about tag
  sprawl are worthless next to the notes:tag ratio and the singleton count.
- **See the whole set at once.** A schema is never designed alone — it's designed against the base + all
  siblings. Minting one is an occasion to rebalance all.
- **Controlled vocabulary beats folksonomy at scale.** Recurring, enumerable things become **facets**
  (typed fields with a value set), not freeform tags.
- **DRY across schemas.** A field that recurs in N schemas belongs in the base (**hoist**); a base field
  only one schema uses belongs there (**push-down**).
- **Every change is a migration.** Renaming a key, merging a tag, or moving a field rewrites existing
  notes. Weigh the blast-radius; propose, get approval, migrate in one coherent pass.
- **Never auto-apply.** Output a review artifact (diagnosis + diff + migration plan). Humans approve.

## Quick navigation

| Task / signal | Read |
|---|---|
| The named health phenomena + their fixes (the catalog) | [references/health-phenomena.md](references/health-phenomena.md) |
| How to measure (ratios, fill-rate, sprawl) | [references/measurement.md](references/measurement.md) |
| Mint a schema / rebalance the set (the workflow) | [references/rebalancing-workflow.md](references/rebalancing-workflow.md) |
| Sharp edges (migration, lossy merges, recency window) | [references/gotchas.md](references/gotchas.md) |
| Health-report output shape | `assets/report-template.md` |
| Measurement engine | `scripts/schema_health.py` |

## Where this sits

folder-curator (types) · domain-triage (routes to entity) · frontmatter-enrichment (fills values) —
these *operate within* the schemas. **taxonomy-steward defines and rebalances the schemas themselves.**
It reads the same contracts (the vault `frontmatter-category-map.json` + per-dir `.curator/taxonomy.yaml`
`frontmatter:` blocks) and, when a change is approved, drives the migration via `frontmatters set` /
`apply-base` across affected files.

## The two modes

1. **Mint a schema for a directory.** Analyze the dir's content + the full existing schema set → propose
   the smallest schema that fits, reusing base/shared fields, and flag any field that should be hoisted
   (recurs elsewhere) or any emergent tag pattern that should become a facet. See rebalancing-workflow.md.
2. **Health pass (audit + rebalance).** Run the metrics, match findings to the phenomena catalog, and
   produce a prioritized, migration-costed remediation plan (merge tags, prune singletons/orphans,
   consolidate enums, normalize naming, hoist/push-down fields, reconcile diverging conventions).

## Procedure (both modes)

1. **Measure.** `schema_health.py <dir>` (whole vault or a subtree). For emergent patterns, add
   `--recent-days 14` to see what's new this window vs the established set.
2. **Inventory the schema set.** Read the base + every extension so decisions are made against the whole.
3. **Diagnose.** Map each metric to the catalog (references/health-phenomena.md): ratio→explosion,
   near-dups→merge, low fill→orphan, dual-case→naming drift, enum count→sprawl, high fill in one schema→hoist.
4. **Decide local-fit vs global-rebalance** (references/rebalancing-workflow.md).
5. **Write the review artifact** (assets/report-template.md): findings, proposed schema/diff, and a
   migration plan with blast-radius counts.
6. **On approval, migrate** in one pass (frontmatters set/apply-base; update the contracts), then
   re-measure to confirm.

## Out of scope

- **Applying an existing schema to a file / backfilling one note** → `frontmatter-enrichment`.
- **Typing a file** (category/kind) → `folder-curator`. **Routing to an entity** → `domain-triage`.
- **Memory bank mechanics** → `hindsight`.
- **Authoring a brand-new domain's contract from scratch** (first `.curator/taxonomy.yaml` + TRIAGE + bank)
  → `domain-triage` / `folder-curator`. This skill refines and rebalances schemas that exist (or mints one
  against them), it doesn't stand up a domain's routing.
- **Editing the `frontmatters` tool** → its own repo (`~/code/frontmatters`).
