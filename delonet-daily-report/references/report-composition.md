# Report composition

Validate section artifacts, compose coverage, publish one coherent generation.

## Reading order

| Task | Read |
|---|---|
| Emit section JSON | This file → `../assets/contracts/section-artifact.schema.json` |
| Aggregate a run | This file → `../assets/contracts/run-manifest.schema.json` |
| Render the report | This file → `../assets/default-core-sections.json` → `../assets/contracts/daily-report.schema.json` |

## Composition lifecycle

Order matters: disabled sections stay excluded, and published files share one
validated run identity.

1. Enumerate every core section and every enabled section **from config**. Never
   infer coverage from the files on disk — that is precisely how a broken run
   comes to look complete.
2. Validate each `SectionArtifact` against its expected section id.
3. Mark `stale` when `fresh_until` precedes aggregation time, or the artifact
   belongs to another run date.
4. Write and validate `RunManifest` with one entry per enabled section. Missing,
   invalid, stale, and failed sections each get an entry with a reason.
5. Derive the overall status: `complete` when every enabled section is
   `complete`; `failed` when no section completed **or** a **required** section
   did not run (`failed` / `missing` / `stale` / `invalid`); `partial`
   otherwise. The trigger for `failed` is *did not run*, not *is not complete* —
   a required section that ran and returned `partial` degrades the report, and a
   required section that ran and reported bad news is `complete`.
6. Compose in core-section order, then enabled-section order. Partition every
   enabled section into disjoint `coverage.complete` or `coverage.degraded`.
7. Render Markdown and the structured `DailyReport`, then publish the
   identity-matched pair with
   `reportctl archive --report REPORT.json --markdown REPORT.md [--manifest RUN.json]`.
   Read only the immutable generation referenced by `current.json`.
8. Prove it: `reportctl verify --date YYYY-MM-DD`.

## Narration

Exactly one LLM call per run, over `bound_for_narrator(...)` output: the field
allowlist first, then the byte cap. The narrator writes prose; it never decides a
status, never adds a section, and never removes a caveat. If narration fails, the
deterministic fallback render publishes with `status: partial` and a caveat
saying so.

Provider invocation is `hermes -z <prompt> --ignore-rules -t todo --provider <p>
-m <m> --usage-file <tmp>` (`scripts/narrate.py`). `-t todo` is deliberate: `-z`
auto-bypasses approvals, and the default toolset would give a model reading other
people's commit subjects a working shell (measured: the default invocation ran
`id -un` on request; with `-t todo` it answers `SHELL_UNAVAILABLE`). Three
structural guarantees back the sentence above:

1. `coverage-freshness` is rendered from the manifest and is never sent to the
   model as a section to write.
2. Each narrated collector section is published with `**Status (authoritative):
   <status>**` as its first line, taken from the manifest.
3. The model's reply must be a JSON object naming every expected section id. A
   missing body is a narrator failure, not a blank section.

The usage report is read as an independent success signal: exit 0 with
`failed: true` is a failure, and a reported model that differs from the
configured one becomes a caveat rather than a silent substitution.

## Editorial rules

- Lead with material changes and say why they matter.
- Distinguish fact, source claim, and inference.
- Show stale, missing, and failed sections in "Coverage and freshness" instead of
  quietly dropping them.
- Do not repeat an event across sections; pick a primary and cross-reference.
- Say "no material update" only when the source was successfully read. If it was
  not, the status is `partial` or `failed` and the reason says what was
  unreachable.
- A status is a statement about the *collection*, not about the findings. A
  collector that read every source and found the pipeline broken is `complete`;
  its verdict belongs in `summary`, `metrics`, `caveats`, and `detail`, and must
  lead the section body rather than hide at the end of it.
