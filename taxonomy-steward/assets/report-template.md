---
pipeline-status: new
---
# Taxonomy Health / Schema Proposal — <scope> — <date>

## 1. Measurements
<paste key numbers from schema_health.py: notes analyzed, notes:tag ratio + singletons,
enum distinct counts, base-candidate & orphan fields, naming drift. Add --recent-days diff if drift-scanning.>

## 2. Findings (mapped to the phenomena catalog)
| Finding | Phenomenon | Signal (number) | Severity |
|---|---|---|---|
| e.g. AI/ai/Docker/docker … | near-duplicate/case tags | 14 clusters | med |
| e.g. category has 43 values | enum sprawl | 43 vs ~6 intended | high |
| e.g. project_name in 2 casings | naming drift | dual-form key | med |

## 3. Proposal
### Option A — local-fit (minimal, ~0 migration)
<the schema / change using only existing fields; what new fields, if any>

### Option B — global-rebalance (healthier set, migration cost noted)
<hoist / push-down / facet-promotion / enum-consolidation / naming-normalization operations,
each with the canonical form and the aliases>

**Recommendation:** <A or B, and why — tie to a metric in the alarm zone or a recurrence ≥2 places>

## 4. Migration plan (only runs on approval)
| Operation | Canonical | Aliases/variants merged | Files affected | Commands |
|---|---|---|---|---|
| merge tags | `moc` | MOC, MOCs | N | frontmatters set … |
| consolidate enum | category set | Project→projects, Blog→blog | N | frontmatters set … |
| hoist field | `updated` (→ base) | modified_at | N | apply-base --schema … |

- Contract edits: <frontmatter-category-map.json and/or .curator/taxonomy.yaml blocks>
- Post-migration: `frontmatters validate --schema <new>` on the affected tree; re-run schema_health.py.

## 5. Decision
<record the human's choice + rationale; retain to Hindsight / decisions/>
