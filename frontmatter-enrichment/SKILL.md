---
name: frontmatter-enrichment
description: "Enrich a markdown file's YAML frontmatter — stamp the repo's base schema, then fill context-aware values (incl. why the file exists / its role in the plan) interpolated from the driving agent's memory. Pipeline link #3, after folder-triage (type) and domain-triage (entity). Uses the `frontmatters` CLI (`apply-base`, `set`, `validate`) as the editor and the repo's Hermes PM memory + Hindsight bank as the context source — no new agent. Base schema is declared per-repo (vault `frontmatter-category-map.json`, a `.curator/taxonomy.yaml` frontmatter block, or a base.yaml). Use when applying base frontmatter, backfilling missing metadata, setting frontmatter key=values, writing context-aware tags/summary/why-created, or validating frontmatter against a schema. Do NOT use for type classification (folder-curator), entity detection/routing (domain-triage), memory mechanics (hindsight), or authoring schemas themselves. Biases: apply base first, never clobber, preserve key order, memory-informed values over guesses."
pipeline-status: new
---

# Frontmatter Enrichment

The third link in the triage pipeline. **folder-curator** types a file, **domain-triage** routes it to
its entity, then this fills the frontmatter — the base skeleton plus the context-aware values that only
the driving agent's memory can supply ("why does this file exist, what is its role in the plan").

## Operating principles

- **Base first, then context.** Stamp the declared base schema (idempotent, non-clobbering), then set
  the interpolated values on top.
- **Never clobber, never fabricate.** Preserve existing values; use `unknown`/`unconfirmed` rather than
  inventing. Memory-grounded values beat guesses.
- **The editor is `frontmatters`, not hand-edits.** It preserves key order and writes atomically;
  hand-editing YAML risks the order/format corruption the tool exists to avoid.
- **Memory is the differentiator.** The rich fields come from the repo's Hermes PM context — recent
  activity, decisions, and the Hindsight bank — not from the file alone.
- **No new agent.** The repo's Hermes PM drives this; its memory *is* the context.

## Quick navigation

| Task | Read |
|---|---|
| The enrichment procedure (step by step) | [references/enrichment-procedure.md](references/enrichment-procedure.md) |
| Declaring/resolving the base schema per repo | [references/base-schema.md](references/base-schema.md) |
| Deriving context-aware values from memory | [references/context-interpolation.md](references/context-interpolation.md) |
| Sharp edges | [references/gotchas.md](references/gotchas.md) |

## The tool (`frontmatters`)

The editor is the extended `frontmatters` CLI (repo: `~/code/frontmatters`; also an MCP mode):

```bash
frontmatters apply-base FILE --schema <base>   # add missing base keys (no clobber), order per schema
frontmatters set FILE key=value [key=value...] # set arbitrary values (type-coerced), order-preserved
frontmatters validate FILE --schema <base>     # required keys + enum check; exit 1 if invalid
```
`<base>` is a schema file OR a dir containing `.curator/taxonomy.yaml`. See references/base-schema.md.

## Procedure

Preconditions: the file is already typed (has `category`/`kind`) and entity-routed (domain-triage set
the entity label + moved it). Then:

1. **Apply the base skeleton.** `frontmatters apply-base FILE --schema <repo-base>` — stamps every base
   key, keeps what's there.
2. **Gather context** from the driving PM's memory: recent activity (`llr`/mtime), the decisions ledger,
   and `hindsight memory recall <bank> "<file topic>"`. This answers *why the file exists* and *its role
   in the plan*. See references/context-interpolation.md.
3. **Interpolate the context-aware values** — `title`, `description`, `tags`, `summary`, `domain`, and a
   plan-context field (e.g. `why`/`context`) — grounded in step 2, not invented.
4. **Write them:** `frontmatters set FILE title="…" description="…" tags="[…]" why="…"`.
5. **Validate:** `frontmatters validate FILE --schema <repo-base>`; fix any missing required keys.

## Base schema is per-repo (so any repo extends it)

The tool is schema-agnostic: each repo points `--schema` at its own base+extension. The DeLoDocs vault
uses its metadata-first contract (`_vault/Settings/frontmatter-category-map.json`); other repos declare
a `.curator/taxonomy.yaml` `frontmatter:` block or a plain `base.yaml`. See references/base-schema.md
for the resolution order and the two-convention caveat.

## Out of scope

- **Type classification** (category/kind/`plan`) → `folder-curator`.
- **Entity detection & routing** (which company/client/repo, moving the file) → `domain-triage`. This
  node runs *after* it and assumes the entity is already set.
- **Memory retain/recall/bank mechanics** → `hindsight`. This skill *consumes* recall; it doesn't manage banks.
- **Authoring the frontmatter schemas themselves** (defining a repo's base/extension) → that's a
  contract-authoring task; this skill applies an existing schema.
- **The vault Inbox classifier→specialist pipeline** → `_vault/Workflows/` in DeLoDocs.
- **Extending the `frontmatters` tool itself** → its own repo (`~/code/frontmatters`).
