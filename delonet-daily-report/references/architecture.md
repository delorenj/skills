# Architecture

Use this reference to understand component ownership, scheduler data flow, and
the durable filesystem contract.

## Reading order

Choose the shortest reading path for the architecture task you need to perform.

| Task | Read |
|---|---|
| Learn components and ownership | This file → `report-composition.md` |
| Change scheduler behavior | This file → `journalist-lifecycle.md` |
| Change config or artifact shapes | This file → `../assets/contracts/*.schema.json` |

## Data flow

The report system derives durable jobs and artifacts from one operator-owned
JSON configuration.

```text
JSON config (source of truth)
  ├─ ddr:journal:<topic-id> (durable Hermes cron, one per enabled topic)
  │    └─ three ephemeral investigators, batched when available
  │         └─ SectionArtifact JSON
  └─ ddr:daily (one durable Hermes cron)
       ├─ validates freshness and contracts
       ├─ writes RunManifest JSON
       └─ composes + archives DailyReport
```

Use configuration to derive desired jobs. Reconciliation compares desired jobs with a Hermes snapshot, removes duplicate managed jobs, edits drifted jobs, and removes stale managed names. Never alter jobs outside the `ddr:` namespace.

## Filesystem contract

Resolve all runtime paths from `artifact_dir` and `archive_dir` in the
operator-owned configuration.

Resolve `artifact_dir` and `archive_dir` from the operator-owned config:

```text
<artifact_dir>/<YYYY-MM-DD>/sections/<topic-id>.json
<artifact_dir>/<YYYY-MM-DD>/run-manifest.json
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/current.json
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/generations/<generation>/report.md
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/generations/<generation>/report.json
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/generations/<generation>/run-manifest.json
```

Treat only the immutable generation named by `current.json` as published.
`reportctl archive` locks the date, validates matching report/manifest identity,
stages and fsyncs the complete generation, renames it, then atomically switches
`current.json`. If the pointer rename succeeds but its directory fsync fails,
the command reports failure but retains the newly referenced generation. The
pointer therefore always names a coherent generation.

Retain immutable generations by default. An operator-managed garbage collector
may delete unreferenced generations according to a local retention policy, but
it must take the date archive lock, read `current.json`, exclude that generation,
and verify the pointer again immediately before deletion. Never delete the
generation named by either pointer read.

## Contract ownership

Each contract has one lifecycle owner and one durable purpose.

- `SectionArtifact`: one journalist run, one topic, evidence-backed findings and explicit freshness.
- `RunManifest`: aggregator audit trail covering every configured core section and topic.
- `DailyReport`: final structured report plus rendered Markdown archive path.

Treat JSON Schemas in `assets/contracts/` as normative. Keep prose subordinate to those contracts.
