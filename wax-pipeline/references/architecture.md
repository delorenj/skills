# Architecture and provenance

Read for stage ownership or changing identity/recovery. Paths below are relative
to the verified HeyMa checkout (`~/HeyMa` on this host).

## Authority map

| Owner | Truth |
|---|---|
| Wax CLI + `waxd` | Capture/intake, audio/archive/transcription and document EP execution, mutations, SQLite receipts, retries, outbox, scheduler |
| Pass YAML `components/wax/config/passes.d/*.yaml` | Available executable definitions, purpose, capability, timeout, ownership and registry conditions |
| Pipeline YAML `components/wax/config/pipelines.d/*.yaml` or n8n export | Authoring input; changing it alone does not change compiled execution |
| Compiled `pipelines` definitions | Selected graph/config identity; explicit compile/import changes future execution |
| `processing_plans` | Immutable minted audio-item plans, including authority provenance |
| n8n `components/n8n-nodes-heyma/` | Static graph editor + CLI control adapters, not a second scheduler |
| Holocene `/wax` | Read-only catalog/projection, not storage or execution authority |
| Bloodbank → Candystore | Durable shared facts; Wax ledger remains local execution/recovery authority |
| Postgres `transcriptions` (schema `tx`) | Versioned history + hybrid search of every vault transcript; a derived projection fed by Wax, never an execution authority. See [Transcriptions store](transcriptions-store.md) |

## Audio shape

`stream/` capture or `inbox/` intake → archive upload/verification → transcription
and sanity gate → EPs → audio link refresh/reverify/local parking → plan-gated
`transcription.completed`. A failed EP leaves enrichment pending; independent
siblings may finish. Pass-declared events can publish before whole-plan completion
once the producing pass's required subgraph is satisfied.

Audio identity is a real SHA256/content-addressed item, not a filename inference.
Archive keys are immutable `recordings/YYYY-MM-DD/<sha12>-<name>`. Transcript
renames update the linked note path and sidecars/tags, **never** rename/delete the
S3 audio object. Runner-owned fields include `wax-item-id`, the `wax` history
block, capture/source fields and S3 checksum/key/URI. Preserve them through edits
and recovery tooling. `dropoff/` is receive-only transport: Wax copies out, never
writes to it. `~/audio/*` and the old second checkout are retired.

The encoder runs in its own systemd scope and survives an ordinary `waxd`
restart. Session shutdown is different: capture guard quiesces before the audio
session disappears. Do not stop/salvage/cancel a capture as an incidental test.

## Document shape

Markdown (`.md`, `.markdown`) is registered under a binding with content identity
`doc-<sha16>` and tracked current hash. It has a `documents` row, **not** an audio
item/transcript row. Binding-scoped pass key is `doc-<sha16>@<binding-id>`; treat
the suffix as opaque (actual folder names may contain capitals). No fake duration,
source audio, verified backup or transcript-completion event is manufactured.

The document runner applies frontmatter/body proposals, preserves the path (the
transcript slug rename is audio-only), rejects pass-declared `events`, and records
per-binding/document/pipeline/compiled-definition receipts. A real cross-process
flock protects a whole document run. This is not a document backup/archive
service: describe audio provenance only when linked source evidence exists.

## Scheduling and history

- Audio gets the one enabled compiled transcription graph when exactly one
  exists. None → legacy registry plan; more than one → visible ambiguity and
  registry fallback. Do not create competing enabled transcription authorities.
- Existing minted audio plans keep definitions and provenance even if unfinished;
  recompiling never silently replans/backfills them.
- Worker toggle `wax pipeline enable|disable|status` remains the historical
  scheduler control, not per-graph enablement.
- Worker retries audio failures on `WAX_SWEEP_INTERVAL_S` (900s default);
  document scan/retry cadence is `WAX_DOCUMENT_SCAN_INTERVAL_S` (120s default).
  Both depend on worker processing being enabled. Attempt exhaustion is explicit.
- Code/command paths are not vendored inside compiled definitions. Configuration
  freezing does not preserve old executable bytes; version changes need tests.

## Event boundary

Wax owns command/lifecycle emission and its outbox (JetStream PubAck-gated).
n8n can relay/consume events but must not synthesize another Wax completion.
A pass must declare `emits`; data is checked against the Bloodbank schema tree
fail-closed. Per-subgraph pass event publication and final plan completion are
separate gates. Skipped/failed pass results do not publish declared events.

For new event types or consumers load `bloodbank-integration`; do not copy its
schema/envelope rules into this skill. Documents currently reject declared
business events; expanding this requires a real contract change, not pretending
that a text note is an audio transcription.

## Source map

- `src/wax/{capture,archive,transcribe_adapter,worker}.py`: audio stages.
- `src/wax/{passes,finalize,operations}.py`: result application, plans, locks,
  event barriers and definition identity.
- `src/wax/{documents,pipelines,catalog,ledger}.py`: document context, compiled
  graphs, safe discovery and receipts.
- `components/wax/docs/{WAX-DESIGN,ENRICHMENT-PASSES,CONTROL-SURFACE}.md`:
  source-owned design and current operator interface.
- `src/wax/transcriptions/` + `docs/TRANSCRIPTIONS-STORE.md`: the versioned
  transcript store (capture hooks, projector, embed, search, reconcile, health).
