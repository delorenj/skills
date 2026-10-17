# The n8n ↔ Wax boundary (audio + documents)

Released control surface, 2026-10-16. This file is the **architecture boundary
only**: what n8n may do with Wax and what it must never take over. Operation
(CLI commands, graph authoring, deployment) lives in the `wax-pipeline` skill
and `components/wax/docs/CONTROL-SURFACE.md`; incidents in `heyma-pipeline-doctor`.

## Wax owns the pipeline — n8n must not

`waxd.service` (one systemd user daemon) is the single owner of recording,
archiving, transcription, and enrichment. It owns:

- **Triggers and scheduling.** Capture intent sentinels, inbox drain, and
  document-folder scans (every 120s). No n8n `localFileTrigger` watches any Wax
  input; `~/audio/*` is a **retired runtime root**, `dropoff/` (Syncthing
  `receiveonly`) is never written by us, and Telnyx intake delivers verified
  audio into `inbox/`.
- **Audio archival, backup-first.** S3 upload **before** transcription, with
  verified upload (size always gates); the source is never deleted. This
  invariant lives inside Wax (`archive.py`) — it is not n8n graph topology.
- **Transcription + diarization** (GPU) and every enrichment-pass (EP)
  execution, attempt budget, retry, and dead-letter receipt.
- **The ledger** (`var/wax.db`), pass/pipeline definitions, and every artifact
  mutation. Nodes never execute pass scripts, never read `passes.d/` or the
  ledger.
- **Audio lifecycle events.** Wax emits `bloodbank.audio.*`
  (`transcription.completed`, pass events, `task.exhausted` …) itself, as the
  owner, schema-validated. n8n never synthesizes the audio lifecycle — a
  workflow cannot truthfully report state it does not own (→ bloodbank-emit).

## What n8n is for

- **Graph authoring.** Enrichment graphs are authored in **unpublished** n8n
  workflows — Wax Pass nodes wired `continue`/`requires`, the Wax Pipeline
  node's Configure (Authoring) operation declaring trigger, folder bindings,
  policy, and enablement — then exported and compiled by `wax pipeline import`
  into a frozen versioned pipeline definition that Wax runs. **Never publish or
  activate a Wax authoring workflow**: publishing does not make Wax run the
  graph, and an active workflow is how n8n becomes a second scheduler.
- **Explicit control actions.** The `n8n-nodes-heyma` package (→ node-catalog)
  is a family of thin **CLI control adapters** invoking the absolute `wax`
  executable: start/stop recording, preview one pass on one item,
  compile/import/show pipelines, scan documents, run one document. This is the
  sanctioned exception to the in-process/no-host-CLI rule — the CLI *is* the
  control contract, and it keeps every mutation, receipt, and retry inside Wax.
- **Observation is Holocene's job, read-only.** Holocene's Wax tab
  (`holocene.delo.sh/wax`) renders `wax catalog --json` through the Holocene
  API; CLI failure shows as DOWN, never as healthy emptiness. n8n is not a
  Wax monitoring surface.

## Retired architecture (do not rebuild)

- `localFileTrigger` on `~/audio/inbox`/`~/audio/ingest` feeding an
  `executeCommand` transcribe god-node. This shape broke silently for two
  weeks when a repo moved under it. Wax capture intents + the single daemon
  replaced it.
- n8n archiving audio to S3 and emitting the transcription lifecycle itself
  (`secure-source` + hand-built `audio.*` emits). Retired with the god-node
  pipeline; Wax owns both today.
- Watching `~/d/Transcripts` for enrichment. It is Wax **output**; document
  arrivals come from the dedicated bound folder (`~/d/Inbox/Wax` →
  `~/code/DeLoDocs/Inbox/Wax` on this host), and human edits never re-trigger
  enrichment — only an explicit document run does.
