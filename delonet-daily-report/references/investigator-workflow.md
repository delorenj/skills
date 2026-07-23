# Investigator workflow

Use this reference to run the three-role evidence workflow and synthesize one
topic artifact.

## Reading order

Choose the path that matches the investigation condition you need to handle.

| Task | Read |
|---|---|
| Run a topic investigation | This file → `sources.md` → `report-composition.md` |
| No subagents available | This file, “Fallback” |
| Conflicting results | This file → `safety-gotchas.md` |

## Three-role batch

Assign distinct evidence responsibilities before synthesis begins.

When delegation is available, spawn all three ephemeral leaf investigators in one concurrent batch:

| Role | Assignment | Required output |
|---|---|---|
| Primary-source researcher | Search official sources and extract dated facts | Claims, primary citations, retrieval times |
| Change tracker | Compare the reporting window with prior known state | New, changed, unchanged, and retracted items |
| Skeptic / verifier | Challenge significance, corroboration, and source quality | Contradictions, caveats, confidence adjustments |

Give each investigator the topic ID, title, prompt, time window, approved sources, and `SectionArtifact` contract. Disallow child delegation. Collect all outputs, reconcile conflicts, validate citations, emit one artifact, then terminate investigators. Never persist their sessions as journalists.

## Synthesis gates

Apply every gate before writing the final `SectionArtifact`.

1. Reject claims outside the requested time window unless clearly labeled context.
2. Merge duplicate claims by canonical event, not URL alone.
3. Preserve disagreements in `caveats`; do not average incompatible facts.
4. Compute `fresh_until` from configured `max_age_hours`.
5. Set `stale`, `partial`, or `failed` when requirements are unmet; never fabricate completeness.

## Fallback

Preserve the same role separation when concurrent delegation is unavailable.

If delegation is unavailable, execute the three roles sequentially as explicit passes. Preserve separate notes so the skeptic reviews evidence rather than untracked intuition.
