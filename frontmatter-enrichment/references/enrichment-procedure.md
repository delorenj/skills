---
pipeline-status: new
---
# Enrichment procedure

The detailed runbook for pipeline link #3. Assumes folder-curator has typed the file
(`category`/`kind`) and domain-triage has set the entity label + placed the file. Driven by the repo's
Hermes PM (so its memory auto-loads).

## Steps

1. **Resolve the base schema** for this repo (see base-schema.md). Call it `$BASE`.

2. **Apply the base skeleton** (idempotent, non-clobbering, order-preserving):
   ```bash
   frontmatters apply-base "$FILE" --schema "$BASE"
   ```
   Every base key now exists; existing values are untouched; keys are in schema order.

3. **Gather context** (the part only the PM can do — see context-interpolation.md):
   - `hindsight memory recall <bank> "<one line about the file>" --budget mid`
   - the PM's `runtime/memories/MEMORY.md` (auto-loaded) + `runtime/decisions/*.md`
   - recent activity as a recency compass: `llr` (mtime-sorted) near the file's siblings
   These answer *why the file was created* and *its role in the current plan*.

4. **Interpolate the context-aware values** — grounded in step 3, never invented:
   `title`, `description`, `tags`, `summary`, `domain`/`subdomain`, and a plan-context field
   (`why` / `context`). Leave provenance fields (`source`, `captured`, `vault-id`) to whatever created
   the file; don't overwrite them.

5. **Write in one pass** (order preserved, values type-coerced):
   ```bash
   frontmatters set "$FILE" \
     title="…" description="…" tags="[ai, interview, asana]" \
     domain="job-search" why="Created after the Asana intro call to prep the technical loop"
   ```

6. **Validate**:
   ```bash
   frontmatters validate "$FILE" --schema "$BASE"   # exit 1 if a required key is missing / enum bad
   ```
   Fix any reported gaps and re-validate.

## Batch

`apply-base` and `validate` accept a directory (`--depth N`) to backfill/audit a whole tree. `set` also
accepts a directory but applies the *same* values to every file — only useful for a uniform field.

## Where it sits (don't duplicate upstream links)

- folder-curator → sets `category`/`kind` (type). Don't recompute here.
- domain-triage's `domain-drain.py apply` → sets the entity label (`company`/`client`/…) and moves the
  file. Don't re-route here.
- This node → everything else in the frontmatter, especially the memory-derived fields.

If you're building the automated chain, call this right after `domain-drain.py apply … --apply`.
