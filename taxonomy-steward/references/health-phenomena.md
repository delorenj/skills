---
pipeline-status: new
---
# Taxonomy health phenomena — the catalog

Named decay/design phenomena, each with its signal and its fix. This is the steward's diagnostic
vocabulary. Real DeLoDocs figures (2026-07) shown as live examples.

## Tag health

- **Vocabulary explosion / singleton fat-tail.** Tags proliferate until the vocabulary is nearly as
  large as the tagged corpus — a power law with a huge one-use tail. *Signal:* notes:tag ratio
  (distinct ÷ tagged-notes) → 1; high singleton count. *Live:* 426 distinct tags across 536 tagged
  notes = **0.795**; 246 singletons. *Fix:* prune singletons that aren't deliberate; merge near-dups;
  promote the recurring ones to facets; adopt a controlled vocabulary going forward.
- **Near-duplicate / case-collision tags.** The same concept under multiple surface forms. *Signal:*
  tags that normalize (lowercase, de-hyphenate, de-pluralize) to one key. *Live:* `projects/project`,
  `AI/ai`, `MOC/MOCs/moc`, `docker/Docker`, `33god/33GOD`. *Fix:* pick a canonical form, merge the rest
  (rewrite occurrences), and lowercase-normalize tag values at write time.
- **Granularity mismatch.** Tags too specific (one note each → noise) or too broad (everything → no
  signal). *Signal:* singleton tail (too specific) or a tag on >50% of notes (too broad). *Fix:* drop or
  merge over-specific tags; demote over-broad tags to a facet or drop them.
- **Folksonomy vs controlled vocabulary.** Free tagging scales badly; a fixed value set scales but
  resists novelty. *Fix:* keep tags folksonomic for the long tail, but crystallize any tag that recurs
  past a threshold into a controlled **facet** (see facet promotion).

## Field / schema health

- **Field proliferation & near-duplicate fields.** Many fields, several meaning the same thing.
  *Signal:* large field set with low-fill members; synonyms like `updated`/`modified_at`,
  `project-name`/`project_name`/`project`. *Live:* `project_name` exists in **both** kebab and snake;
  a long orphan-field tail. *Fix:* choose one canonical field per concept, alias the rest, migrate.
- **Orphan / dead fields.** Defined (or once-used) fields almost never populated. *Signal:* fill-rate
  below a floor (e.g. <5%). *Fix:* drop from the schema, or demote to clearly-optional; don't force them
  into the base.
- **Base bloat vs. base starvation.** Bloat = the base forces many fields onto every note that most
  don't need; starvation = shared fields aren't in the base, so each schema reinvents them. *Signal:*
  base fields with low global fill (bloat) OR the same field defined across many extensions
  (starvation). *Fix:* **push-down** low-value base fields to the extensions that use them; **hoist**
  cross-schema recurring fields into the base. *Live:* only `pipeline-status` clears 90% global fill —
  the base is broad but under-filled (bloat risk); audit which base fields earn their place.
- **Schema sprawl.** Too many near-identical specialist schemas. *Signal:* schemas differing by one or
  two fields. *Fix:* merge into one with an optional discriminator, or factor the shared part to base.

## Value / enum health

- **Enum / value drift & sprawl.** A field meant to be controlled accumulates uncontrolled values,
  including case/spelling variants. *Signal:* distinct-value count far above the intended enum; off-enum
  or case-variant values. *Live:* `category` = 43 distinct (`projects` vs `Project`, `Blog` vs `blog`);
  `pipeline-status` carries off-enum `Processed`/`discovery`/`publishing`; `status` = 20 distinct.
  *Fix:* define the canonical value set, map variants to it, migrate, then validate on write
  (frontmatters validate --schema with the enum).

## Cross-schema / naming health

- **Naming-convention drift.** Keys mix conventions. *Signal:* both kebab and snake keys; the same field
  in both forms. *Live:* dozens of `snake_case` keys (`created_at`, `modified_at`, `ollama_*`) alongside
  kebab; `project_name` dual-form. *Fix:* pick one casing (the vault is mostly kebab), alias+migrate the
  strays. Note the vault's deliberate snake trio (`created_at`/`modified_at`/`last_processed`) — decide
  and document whether that's an accepted exception.
- **Convention divergence.** Two schemas model the same concept incompatibly. *Signal:* the same idea
  with different keys/enums across contracts. *Live:* the vault's metadata-first contract vs the
  folder-curator `.curator` block disagree on the `pipeline-status` enum and on `kind`/`asset-kind`,
  `updated`/`modified_at`. *Fix:* reconcile to one canonical mapping, or explicitly scope each to its
  domain and document the boundary (don't silently cross them).
- **MECE violation.** Categories/facets that overlap or leave gaps (not Mutually Exclusive & Collectively
  Exhaustive). *Signal:* notes that fit two categories, or a recurring "other" bucket. *Fix:* redraw the
  category set so each note has exactly one right home; add a facet for the crosscutting dimension.

## Design-time phenomena (minting / rebalancing)

- **Schema synthesis under a controlled global taxonomy.** Designing a dir's schema against the *whole*
  existing set, not in isolation — reuse base/shared fields, only add what's genuinely new.
- **Hoisting (generalize up).** A field recurring across schemas is promoted to the base. Trigger:
  present in ≥N extensions with healthy fill.
- **Push-down (specialize down).** A base field only one schema meaningfully uses moves into that
  extension. Trigger: low global fill, concentrated in one type.
- **Facet promotion (tag → field).** An emergent tag pattern is crystallized into a typed, enumerable
  field before it sprawls. Trigger: a tag (or tag cluster) crossing a frequency threshold, especially a
  recent surge. This is the pre-emptive cure for vocabulary explosion.
- **Emergent-facet detection / taxonomy drift.** A pattern appears in a recent window that the schema set
  doesn't yet model. *Signal:* `schema_health.py --recent-days N` shows new high-frequency tags/values
  absent from the established set. *Fix:* facet-promote it (mint/extend a schema) rather than let it
  accrete as tags.
- **Migration blast-radius.** Every rename/merge/move rewrites existing notes; the cost is the count of
  affected files. Always quantify it before proposing a change; prefer additive+aliased migrations.
