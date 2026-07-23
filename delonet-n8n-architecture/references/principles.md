# Principles — the why, in depth

Read this when a design decision is contested or when justifying a refactor. The
SKILL.md states the rules; this file argues them and shows the DeLoNET-specific
reasoning so you can apply them to cases not spelled out.

## 1. One node, one reversible responsibility

A node should do a single thing that has one failure mode and one retry policy.
When you fold N concerns into one node you inherit the **union** of their failure
modes with **none** of the branching. The canonical anti-pattern on this instance
was `Run Transcribe`: a single `executeCommand` running a bash script that
(a) uploaded the source to S3, (b) verified it, (c) stashed a fallback copy on
failure, (d) transcribed with faster-whisper + diarization, (e) parsed a log for
the output path, (f) on remote hosts scp'd the markdown back. Six responsibilities,
three distinct failure modes (S3 down, GPU OOM, ssh/scp), one opaque exit code.
When any of them broke, the fix meant editing fragile bash inside a workflow
needed every day.

**The tell:** an `executeCommand` / `Code` node whose script has more than one
`if … fail …` branch, or whose name contains "and" if you were honest
("Transcribe **and** archive **and** deliver").

**The boundary test:** could this action be dropped into a *different* pipeline
unchanged and still make sense? "Archive a file to `s3://recordings/…` and verify"
— yes, useful anywhere. "Transcribe audio → structured JSON" — yes. "Fold both
into one step" — only useful here, so it is not a unit, it is a monolith.

## 2. The bus is the completion signal

Every pipeline outcome is an **event**, and events belong on bloodbank. This is
not ceremony — it is the difference between a pipeline that notifies *you* and a
pipeline that notifies *the system*. Concretely: `bloodbank-event-toaster`
subscribes to `bloodbank.evt.v1.>` and forwards every envelope to
`https://ntfy.delo.sh/bloodbank`. So a correctly-emitted `audio.transcription.completed`
already lands as an ntfy ping — **and** is persisted by Candystore, **and** is
visible to any future consumer (a "summarize new transcripts" agent, a metrics
sink, a Plane-ticket creator) with zero changes to this workflow.

Wiring an ntfy node directly reproduces exactly one downstream effect (your phone
buzzes) and forecloses every other one. It is strictly worse than emitting the
event. **If you catch yourself adding an ntfy/Slack/email node to signal that a
pipeline step finished, stop — emit the bloodbank event instead** and let the
toaster do the notifying.

## 3. Schema-first events

The bus is only worth trusting if envelopes are predictable. Emit **only** events
that already exist under `bloodbank/schemas/bloodbank/v1/<domain>/…`. For audio
work the contract already exists and should be used verbatim:

- `audio.file.received` — a new recording landed in an ingest path
- `audio.transcription.started` — work began
- `audio.transcription.completed` — transcript produced (carry mdPath, model, duration, lang, speaker count)
- `audio.transcription.failed` — carry the stage + error

If the event you need does not exist, author the schema first (→
`bloodbank-integration`), get it validated, then wire the emit. Never publish a
hand-rolled JSON blob to a subject — an unvalidated envelope is indistinguishable
from noise to every consumer.

## 4. Safety invariants are topology, not buried logic

A safety rule that lives inside a script is invisible and unauditable. A safety
rule expressed as graph structure is both. The backup-first / never-delete
guarantee for recordings should read on the canvas as:

```
[Archive → S3] --success--> [Transcribe]
      |
    (error)
      v
[Stash → ~/audio/recovered] --> [Transcribe]     (both paths converge; source is never deleted by any node)
```

Anyone opening the workflow can see the guarantee. Contrast with the old script,
where "we never delete the source" was a comment you had to trust. Make invariants
load-bearing structure so a future edit cannot silently violate them.

## 5. Reusable + parameterized beats bespoke — the escalation ladder

```
How reusable is this atomic action?
├─ One-off glue, THIS workflow only           → inline Code / Set / Execute Command
├─ Reused across 2+ workflows, no credentials  → subworkflow (Execute Sub-workflow)
│                                                 with an explicit typed input contract
└─ Reused broadly, OR needs credentials /
   schema validation / a first-class node UI   → custom node (n8n-nodes-<thing>)
```

- **Inline** is fine for genuinely single-use glue (compute an S3 key from mtime,
  reshape one payload). It is NOT fine as a hiding place for a multi-step job.
- **Subworkflow** is the pragmatic middle: no build step, editable in the UI,
  callable via `Execute Sub-workflow`. Its weakness is a clunky input contract
  and no credential management. `Parse File for Audio` (`Bxgua92kxXkycFB4`) is an
  existing example. Reach here first when you want SRP *today* without a node-dev
  cycle.
- **Custom node** is the destination for anything reused broadly or needing
  credentials, schema validation, or a proper UI (Bloodbank emit, MinIO/delo,
  Transcribe, Vault). Highest ceremony, highest payoff. → node-catalog.

**Promotion triggers:** a unit hits a 2nd pipeline; a unit needs a credential; a
unit needs to validate input against a schema; you have copy-pasted the same
`executeCommand` twice. Any one of these means promote up a rung.

Default to the lowest rung that still gives a clean, typed boundary — but split
responsibilities *first*. Splitting an oversized node into three inline nodes and
promoting them later is easy; carving a shipped monolith apart while it is on the
critical path is not.
