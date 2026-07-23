---
pipeline-status: new
---
# Gotchas

## Never auto-apply — this skill proposes, humans dispose

Taxonomy changes rewrite many notes and are hard to reverse in bulk. Always emit the review artifact and
get explicit approval before migrating. The one exception is measurement (read-only) — run that freely.

## Every change is a migration; quantify the blast radius first

A tag merge, key rename, enum consolidation, or hoist/push-down rewrites existing notes. Count affected
files (`grep -rl 'key:' <dir> | wc -l`, or the script's usage numbers) and put the count in the
proposal. A "clean" schema that requires rewriting 4000 notes may not be worth it — prefer additive +
aliased migrations that don't touch history.

## Tag/value merges are lossy

Merging `MOC/MOCs/moc` → `moc` discards the original surface form. Usually fine, but if a distinction was
intentional you can't recover it post-merge. Confirm clusters with the human before collapsing; don't
merge across a genuine semantic boundary (e.g. `agent` the role vs `agents` the directory).

## Declared ≠ actual — read both

`schema_health.py` measures notes; it doesn't read the contracts. A field can be heavily used but
undeclared (missing from the schema) or declared but never used (orphan). Always diff the script's field
list against `frontmatter-category-map.json` and the `.curator/taxonomy.yaml` blocks.

## Don't cross the vault's two conventions when validating

The metadata-first contract and folder-curator `.curator` block disagree on the `pipeline-status` enum
and some key names. Validate/consolidate each within its own scope; a cross-scope "fix" will flag correct
values as wrong. Reconciling them is itself a proposal, not a silent edit.

## Recency window is mtime-based and imperfect

`--recent-days` uses file mtime. The vault's 2026-05-11 migration touched everything; and the daily brief
reads `captured`, not mtime. For a true "what emerged this window," cross-check with `captured` where
present, and treat a single wholesale-migration spike as noise, not an emergent pattern.

## Base bloat is silent

An over-broad base looks fine (every note "has" the fields) but most are empty placeholders — that's
bloat, not coverage. Judge base membership by *fill-rate*, not presence. A base field under ~50% global
fill is a push-down candidate.

## Don't over-fit to a one-off

A pattern in a single recent burst may be a project spike, not a durable facet. Require recurrence (or a
sustained window) before promoting a tag to a facet or minting a schema around it — premature facets are
just field proliferation by another name.
