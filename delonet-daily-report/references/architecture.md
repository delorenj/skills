# Architecture

Component ownership, pipeline data flow, and the durable filesystem contract.

## Reading order

| Task | Read |
|---|---|
| Learn components and ownership | This file → `report-composition.md` |
| Change config or artifact shapes | This file → `../assets/contracts/*.schema.json` |
| Diagnose a false green or a missing report | This file → `safety-gotchas.md` |

## Data flow

One cron job, four deterministic collectors, one narration pass.

```text
reportctl run --date <yesterday>
  │
  ├─ 1. COLLECT   local sources only: git, localhost HTTP, files under $HOME
  │     collectors/dev_activity.py     → sections/dev-activity.json
  │     collectors/fleet_health.py     → sections/fleet-health.json
  │     collectors/pr_maintenance.py   → sections/pr-maintenance.json
  │     collectors/report_delivery.py  → sections/report-delivery.json
  │     each emits a SectionArtifact v2 with a real status
  │
  ├─ 2. MANIFEST  sections enumerated FROM CONFIG, never from disk
  │     validate each artifact + freshness → run-manifest.json
  │     missing / invalid / stale are recorded, never dropped
  │
  ├─ 3. NARRATE   one LLM call over field-allowlisted input ≤ 256 KB
  │     → report.json (DailyReport) + report.md
  │     on failure → deterministic fallback render, status=partial
  │
  └─ 4. PUBLISH   stage → fsync → rename → swap current.json, then re-read it
        mirror report.md + report.json into 33GOD (_bmad-output/daily-journals)
        emit report.completed — or report.failed — with the derived status
```

Exit code: 0 for `complete` and `partial`, 3 for `failed` (no section completed,
or a required section did not run), 2 when the publish itself failed. A cron
agent cannot record success over a dead run — and, equally, a run that
accurately reports bad news exits 0, so the document naming the problem is not
itself suppressed as a failure.

Ownership is single-writer at every boundary: collectors own section artifacts,
the run owns the manifest and report, `publish_archive_pair` owns the pointer.

## Module map

| Module | Owns |
|---|---|
| `reportctl_config.py` | config schema v2, validate-before-replace writes |
| `reportctl_contracts.py` | SectionArtifact / RunManifest / DailyReport validators |
| `reportctl_runtime.py` | atomic writes, file lock, archive publish transaction, bounded subprocess |
| `reportctl_archive.py` | artifact health, status derivation, `verify_published`, archive publication |
| `collectors/base.py` | `SectionResult`, the field allowlist, the byte cap, `run_collector` |
| `run.py` | the four steps, status derivation, mirror, the Bloodbank envelope |
| `narrate.py` | the single provider call, output parsing, the deterministic render |
| `reportctl_cli.py` / `reportctl` | argument surface, exit codes |

Nothing here inspects the scheduler. Hermes profile parsing, timezone and
inference preflight, and cron reconciliation were removed with the multi-job
design: correctness is proven by reading the published artifact instead.

## Filesystem contract

Resolve every runtime path from `artifact_dir` and `archive_dir`.

```text
<artifact_dir>/<YYYY-MM-DD>/sections/<section-id>.json
<artifact_dir>/<YYYY-MM-DD>/run-manifest.json
<artifact_dir>/<YYYY-MM-DD>/report.json          # staged input to the publish
<artifact_dir>/<YYYY-MM-DD>/report.md            # staged input to the publish
<artifact_dir>/<YYYY-MM-DD>/report-event.json    # the envelope, emitted or not
<artifact_dir>/<YYYY-MM-DD>/.run.lock            # one run per date
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/current.json
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/generations/<generation>/report.md
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/generations/<generation>/report.json
<archive_dir>/<YYYY>/<MM>/<YYYY-MM-DD>/generations/<generation>/run-manifest.json
```

Only the immutable generation named by `current.json` is published. `archive`
locks the date, checks that the report and manifest share one identity, stages
and fsyncs a complete generation, renames it, then atomically swaps the pointer.
If the pointer rename succeeds but its directory fsync fails, the command reports
failure and retains the newly referenced generation — the pointer always names a
coherent generation.

Retain generations by default. A garbage collector must take the date lock, read
`current.json`, exclude that generation, and re-read the pointer immediately
before deleting. Never delete the generation named by either read.

## Contract ownership

- `SectionArtifact` v2: one collector run, one section, honest status plus a
  mandatory reason whenever that status is not `complete`. The status describes
  the *collection* — `complete` means every source was read, even when what they
  said is bad news; `partial` means a source could not be read; `failed` means
  the collector could not do its job. Findings live in `summary`, `metrics`,
  `caveats`, and `detail`.
- `RunManifest` v1: audit trail covering every enabled section exactly once, in
  config order, including the ones that failed.
- `DailyReport` v1: structured report plus the rendered Markdown archive path.

JSON Schemas in `assets/contracts/` are normative. Prose is subordinate to them.
