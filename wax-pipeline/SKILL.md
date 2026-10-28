---
name: wax-pipeline
description: Operate Wax audio and Markdown document enrichment through the Wax CLI. Use for pass discovery, pipeline configuration, document arrival bindings and retries, frozen EP graphs authored in n8n, audio provenance, or Holocene's read-only Wax tab. Covers maintaining existing passes and the n8n Wax node package; use create-enrichment-pass for implementing a portable EP and heyma-pipeline-doctor for incidents. Not generic n8n automation or vault-wide file routing.
---

# Wax pipeline

**One executor, two input shapes.** Wax owns audio capture/intake, archival,
transcription, document registration, EP execution, mutation, receipts, retry
budgets and its scheduler. n8n authors static graphs and provides explicit
CLI-backed control/preview nodes. Holocene reads the safe catalog; it never
compiles, enables or executes anything.

## Start with current truth

The deployed checkout is `~/HeyMa`, not the older `~/code/HeyMa`. Verify the
running unit/CLI location before a repair. From the owning checkout:

```bash
mise x -- ./bin/wax catalog --json
mise x -- ./bin/wax pipeline list --json
mise x -- ./bin/wax pipeline bindings --json
```

These separate registered/enabled/automatic from actually running, failed,
skipped, exhausted and unavailable. Pass-level counts are registry-wide;
pipeline counts are scoped to that pipeline and its frozen versions. A fresh
catalog timestamp proves the reader answered, not that the worker is alive:
inspect `pipelines.worker` and binding scan timestamps too.

Source of truth is `components/wax/src/wax/` and the registries, not old skills
or recalled outages. Read the current repo `AGENTS.md` and the relevant source
doc, then only the reference needed below. In agent shells use `mise x -- uv …`
for uv; a missing bare binary is not a missing installation.

## Choose the procedure

| Task | Read |
|---|---|
| Audio/source identity, stage ownership, event barriers | [Architecture and provenance](references/architecture.md) |
| Create a document binding, explicit edit run, retry/backfill | [Document scenarios](references/documents.md) |
| Compose, import or recompile a graph; maintain n8n nodes | [Pipelines and n8n](references/pipelines-and-n8n.md) |
| Change an EP, capability, result envelope or version | [EP maintenance](references/enrichment-passes.md); implementation → `create-enrichment-pass` |
| Holocene read API, fresh/degraded state, deploy checks | [Control surface](references/control-surface.md) |
| Transcript versions/history, semantic search, store lag, provisioning | [Transcriptions store](references/transcriptions-store.md) |
| Dated deployed scenarios and editor links | `~/HeyMa/components/wax/docs/CONTROL-SURFACE.md` |
| Recording lost, diarization failed, daemon wedged | `heyma-pipeline-doctor` |

## Invariants that change the decision

- **Preserve the source.** Audio is uploaded and verified before transcription;
  source bytes are never deleted. Documents are a separate context, not fake
  audio items or `transcripts` rows. Never invent S3/capture provenance.
- **EPs propose; Wax applies.** Portable text/frontmatter enrichment reads a
  document and emits `wax_ep_version: 1`. No direct file/ledger/S3 writes from
  a portable EP. Audio-dependent/notification behavior is a declared adapter
  capability, not a requirement imposed on every document.
- **New arrivals are new paths.** First document scan seeds existing files;
  later edits and Wax's own writes do not auto-enrich again. Explicit runs and
  backfill are mutations, not diagnostic commands. `~/d/Transcripts` is output,
  never a second watched inbox. The released document binding is `~/d/Inbox/Wax`.
- **Compile deliberately.** Registry YAML is live for uncompiled/manual registry
  operations; compiled graphs freeze configuration, edges, conditions and pass
  versions. Existing audio plans never migrate implicitly. Executable source
  code is **not** an immutable snapshot; changing it needs code verification
  and daemon restart, and may affect an old plan invoking that path.
- **Never publish Wax authoring workflows in n8n.** Export → `wax pipeline import`
  adopts the graph. Wax owns automatic trigger/retry execution. Ordinary n8n
  workflows may consume Wax events; they must not become another pipeline owner.
- **The transcriptions store is derived and fail-open.** Every applied pass is
  a version in Postgres `transcriptions`, but capture only queues a SQLite
  snapshot; an outage is `transcripts lagging|error`, never a failed pass. Fix
  lag with `wax transcripts sync`, not by re-running passes. History there is
  append-only: never point a test or a scratch ledger at the real DSN.
- **Show the boundary honestly.** `exported_snapshot` means the imported export,
  not a comparison against the current n8n draft. Registry drift is separate.
  Holocene consumes `wax catalog --json`, not raw SQLite, YAML, pass environment,
  stderr or document bodies. No CLI source becomes DOWN-as-healthy-empty.

## Bounded verification

For skill/document capture, do not restart services or replay live artifacts.
For code changes, run affected isolated tests, then the changed contract proof:

```bash
mise x -- python3 -m pytest components/wax/tests -q
```

n8n package changes additionally need its build/tests/lint **and native
PackageDirectoryLoader** test; TypeScript compilation alone missed a real
package-wide load failure. Never conclude success from a green tray or PM2
`online`. Verify worker receipts/heartbeat, HTTP readiness, and the affected
hosted UI after an authorized deployment. Keep historical backfill and enabling
a new scenario explicit; do not turn a maintenance request into either.
