---
pipeline-status: new
---
# Measurement — the evidence

Never propose a taxonomy change without numbers. The bundled script is the fast path; `frontmatters`
and shell fill gaps.

## The bundled script

```bash
scripts/schema_health.py <dir>                 # whole tree (vault or subtree)
scripts/schema_health.py <dir> --recent-days 14 # only recently-modified notes (emergent-pattern scan)
scripts/schema_health.py <dir> --json           # machine-readable
scripts/schema_health.py <dir> --watch category,status,pipeline-status,contact-type
```
Reports: notes:tag ratio + singleton count, near-duplicate tag clusters, per-field fill-rate
(base-candidates ≥90%, orphans <5%), kebab/snake drift + dual-form keys, and enum sprawl on the watched
controlled fields. No writes.

## Metrics & thresholds (rules of thumb, not laws)

| Metric | How | Healthy | Alarm |
|---|---|---|---|
| notes:tag ratio (distinct ÷ tagged-notes) | script | < 0.3 | ≥ 0.6 → explosion |
| singleton share of tags | script | small tail | tail dominates the vocabulary |
| field fill-rate | script | base fields high; extension fields decent | base field <50% (bloat); any <5% (orphan) |
| enum distinct count | script `--watch` | ≈ intended set | ≫ intended, or case/off-enum variants |
| naming drift | script | one casing | same field in two casings |
| recent vs established | `--recent-days N` twice | new work reuses schema | new high-freq tags/values not modeled |

## Emergent-pattern detection (the "past few weeks" case)

Run the script twice — full corpus vs `--recent-days 14` — and diff the tag/enum profiles. Tags or
values that are hot recently but rare overall are **emergent facets**: candidates for facet promotion
before they sprawl. (Use `captured`/mtime as the time axis; `llr` is a quick recency compass.)

## Cross-checks with existing tools

- `frontmatters filter show <dir> --field <k>=<v>` / `--in k=v1,v2` — enumerate notes by a value (verify
  an enum's real usage before consolidating).
- `frontmatters tree show <dir> --tags` — eyeball tag distribution by area.
- `frontmatters organize analyze <tree.json> --agents` — its multi-agent pass proposes tag/category
  consolidations as a report (advisory input, not authority).
- `grep -rl 'someKey:' <dir> | wc -l` — exact blast-radius count for a proposed key rename/merge.

## What the script can't see

It measures *usage in notes*, not the *declared* schemas. Always also read the contracts
(`frontmatter-category-map.json`, each `.curator/taxonomy.yaml`) so you compare declared-vs-actual:
declared fields with zero usage are orphans; heavily-used undeclared keys are missing from the schema.
