---
pipeline-status: new
---
# Base schema — per-repo, extensible

The tool is schema-agnostic: `frontmatters apply-base/validate --schema <X>` reads the base+extension
from whatever `<X>` the repo declares. That is how "base defined in the vault; any repo extends it"
works without hardcoding one vault's schema.

## What `--schema` accepts (resolution)

`<X>` may be a file, or a **directory** (then it reads `<dir>/.curator/taxonomy.yaml`). Three source
shapes are understood:

1. **folder-curator `.curator/taxonomy.yaml`** — reads its `frontmatter:` block:
   `order`, `required`, `defaults`, `pipeline_status_values` (→ enum for `pipeline-status`). This is the
   established per-repo/per-directory extension convention (JobHunting uses it), deep-merged over the
   folder-curator default. **Preferred for non-vault repos.**
2. **vault `frontmatter-category-map.json`** — reads `metadataFirstContract.fields` (field order) as the
   base skeleton. Use this for the DeLoDocs vault (its richer 22-field metadata-first contract).
3. **plain YAML/JSON mapping** key→default — order = key order. Simplest custom base (`base.yaml`).

`apply-base` stamps the full skeleton: every key in `order` that's missing gets its default, or `''` as
a placeholder when there's no default (matching the vault's empty-placeholder base style).

## The two-convention caveat (important)

DeLoDocs has **two** frontmatter conventions that disagree, and you must not cross them:

| | vault metadata-first | folder-curator `.curator` |
|---|---|---|
| source | `_vault/Settings/frontmatter-category-map.json` / `_vault/templates/BaseProps.md` | `.curator/taxonomy.yaml` `frontmatter:` block |
| type key | `asset-kind` | `kind` |
| updated key | `modified_at` | `updated` |
| `pipeline-status` enum | `new, queued, ready, processed, hitl, error-*` | `new, processing, processed, blocked` |
| casing | mixed kebab + snake (`created_at`) | kebab |

Pick the schema that matches the file's directory: vault files → the vault contract; a repo with a
`.curator/taxonomy.yaml` → that. Never validate a vault file against the folder-curator enum (or vice
versa) — the `pipeline-status` values will spuriously fail.

## Recommended per-repo setup

- **Non-vault repo:** add a `.curator/taxonomy.yaml` with a `frontmatter:` block (order/required/
  defaults/pipeline_status_values). One file declares both the base and the repo's extension fields.
- **DeLoDocs vault:** point `--schema` at `_vault/Settings/frontmatter-category-map.json`. (A future
  cleanup could emit a single reconciled `base.yaml` the tool reads directly; until then, keep the two
  conventions separate and matched to their files.)
