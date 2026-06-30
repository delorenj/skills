# OKF alignment OKR and implementation plan

This note captures the target state for aligning `karpathy-llm-wiki` with
Google Cloud's Open Knowledge Format (OKF) while preserving the existing
Karpathy-style `raw/` plus `wiki/` workflow.

Sources:

- Google Cloud: [How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- GoogleCloudPlatform knowledge catalog: [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)

## OKF details

OKF treats a knowledge base as markdown concept files with YAML frontmatter.
The frontmatter supplies machine-readable identity and retrieval metadata,
while markdown links form the human-readable and agent-readable graph.

The minimum OKF requirement is intentionally small:

- Each non-reserved markdown concept file has parseable YAML frontmatter.
- The frontmatter includes a `type` field.
- Optional but recommended fields include `title`, `description`, `resource`,
  `tags`, and `timestamp`.
- `index.md` and `log.md` are reserved support files. `index.md` gives
  progressive disclosure into the knowledge base. `log.md` records chronological
  history.

The existing LLM wiki model is already close to OKF:

- `raw/` stores immutable source material.
- `wiki/` stores durable concept pages.
- `wiki/index.md` and `wiki/log.md` already match the OKF support-file pattern.
- Markdown links already express cross-page relationships.

The gap is frontmatter. Current templates emphasize human-readable sources and
raw references, but they do not require a stable OKF `type` or the recommended
retrieval fields.

## Objective

Make `karpathy-llm-wiki` produce OKF-compatible concept files by default
without losing the existing raw-source provenance, ingest workflow, cascade
updates, query archiving, or lint behavior.

## Key results

1. Every generated `wiki/<topic>/<article>.md` concept page includes parseable
   YAML frontmatter with at least `type`, `title`, `description`, `tags`, and
   `timestamp`.
2. Raw provenance remains intact through existing `Sources` and `Raw` metadata
   or an equivalent OKF-compatible representation.
3. `references/article-template.md`, `references/archive-template.md`, and
   `references/index-template.md` document OKF-compatible output.
4. `SKILL.md` ingest, archive, query, and lint instructions explain how to
   create and validate OKF metadata.
5. Lint catches missing `type`, unparsable frontmatter, broken raw references,
   and stale index entries without deleting user-authored content.
6. The examples directory contains at least three OKF-compatible sample pages:
   a normal concept article, an archived query answer, and an index/log pair.
7. A migration path exists for older LLM wiki pages that lack OKF frontmatter.

## Implementation plan

### Phase 1: Define the schema contract

Decide the required and recommended fields for each file class:

- **Concept article:** `type`, `title`, `description`, `tags`, `timestamp`,
  `sources`, and `raw`.
- **Archived query answer:** `type`, `title`, `description`, `tags`,
  `timestamp`, `archived_from`, and `sources`.
- **Raw source file:** source URL, collected date, published date, and optional
  OKF `type` if raw files become concept-addressable.
- **Index and log:** keep as reserved support files; do not require concept
  metadata unless OKF upstream requires it later.

Recommended `type` values:

- `Concept` for normal wiki pages.
- `Archive` for saved query answers.
- `Source` for raw source material if raw files receive OKF metadata.
- `Index` and `Log` only if support files need explicit metadata.

### Phase 2: Update templates

Patch the templates in `references/` so every new page starts with OKF
frontmatter and keeps the existing wiki affordances.

Target article shape:

```yaml
---
type: Concept
title: Attention mechanisms
description: How attention lets transformer models route information across token positions.
tags: [transformers, attention, language-models]
timestamp: 2026-06-25T00:00:00Z
sources:
  - "Vaswani et al., 2017"
raw:
  - "../../raw/machine-learning/2017-06-12-attention-is-all-you-need.md"
---
```

Keep the human-readable `> Sources:` and `> Raw:` block only if it remains useful
for scanability. If both representations are present, lint must verify they do
not drift.

### Phase 3: Update workflow rules

Modify `SKILL.md` so each operation knows what OKF-compatible output means:

- **Ingest:** generate or update OKF frontmatter during compile.
- **Cascade updates:** refresh `timestamp` only when article knowledge changes.
- **Query archive:** use `type: Archive` and keep citations as markdown links.
- **Lint:** validate OKF metadata before link checks.

The skill must preserve the existing rule that `raw/` is immutable after fetch.
Any migration of raw file metadata must be explicit and separate from normal
ingest.

### Phase 4: Add lint and migration behavior

Extend lint instructions to cover OKF checks:

- Frontmatter exists and parses.
- `type` exists on concept files.
- `title` and `description` are non-empty.
- `timestamp` is ISO-like and represents knowledge update time.
- `tags` are a YAML list or a clearly parseable scalar list.
- `sources` and `raw` fields agree with existing prose metadata if both exist.

For old pages, auto-fix only safe fields:

- Add `type: Concept` when missing.
- Add `title` from the first H1 when missing.
- Add placeholder `description: TODO` only if the user explicitly requests
  migration with placeholders.

Report anything requiring interpretation, such as weak descriptions, incorrect
tags, or ambiguous source provenance.

### Phase 5: Update examples

Refresh examples so users and agents can see the intended OKF shape:

- Convert one normal article example to `type: Concept`.
- Convert one archived answer example to `type: Archive`.
- Keep an example `index.md` and `log.md` showing how support files work.

Examples must demonstrate relative links that still resolve under the existing
`wiki/<topic>/` one-level topic rule.

### Phase 6: Verify the skill

Run a completion audit before calling the OKF implementation done:

- Search every template for OKF fields.
- Check every example article has parseable frontmatter and a `type`.
- Check SKILL instructions mention OKF behavior in ingest, archive, and lint.
- Confirm existing raw/wiki/index/log architecture remains documented.
- Run package or validation tooling if available in the repo.

## Design notes

- OKF is a base layer, not a replacement for richer local metadata. Project,
  domain, owner, confidence, questions answered, and next action can remain as
  DeLoDocs-specific extensions.
- Location stays secondary. The frontmatter must make files useful even if the
  physical folder layout changes later.
- The first implementation should bias toward compatibility and migration
  safety over aggressive rewrites.
