# Report composition

Use this reference to validate journalist artifacts, compose active-topic
coverage, and publish one coherent daily generation.

## Reading order

Choose the path that matches the artifact you need to produce.

| Task | Read |
|---|---|
| Emit section JSON | This file → `../assets/contracts/section-artifact.schema.json` |
| Aggregate a run | This file → `../assets/contracts/run-manifest.schema.json` |
| Render report | This file → `../assets/default-core-sections.json` → `../assets/contracts/daily-report.schema.json` |

## Composition lifecycle

Follow these steps in order so paused topics stay excluded and published files
share one validated run identity.

1. Enumerate every configured core section and topic; never infer coverage from files on disk.
2. Validate each `SectionArtifact` and its expected topic ID.
3. Mark stale when `fresh_until` precedes aggregation time, the window is wrong, or the file belongs to another run date.
4. Write and runtime-validate `RunManifest` with one entry per active topic; paused topics are intentionally excluded.
5. Compose in default core section order, then configured topic order.
6. Put required core sections first in configured order, followed by each active topic exactly once. Partition every active topic into disjoint `coverage.complete` or `coverage.degraded`; exclude paused topics.
7. Render Markdown and structured `DailyReport`; publish it with the fully validated, identity-matched `RunManifest` using `reportctl archive --report REPORT.json --markdown REPORT.md [--manifest RUN.json]`. Read only the immutable generation referenced by `current.json`.

## Editorial rules

Apply these rules to both the structured report and rendered Markdown.

- Lead with material changes and explain why they matter.
- Cite every externally verifiable claim; preserve source metadata in structured output.
- Distinguish fact, source claim, and inference.
- Show stale/missing sections in “Coverage and freshness” instead of silently dropping them.
- Avoid repeating an event across sections; choose a primary section and cross-reference briefly.
- Say “No material update” only when sources were successfully checked.

Copy shipped defaults into required `core_sections` configuration. The aggregator prompt uses that exact ordered list. Operators may add or rename sections, but retain explicit coverage/freshness.
