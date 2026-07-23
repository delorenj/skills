# Reference implementation — the inbox/transcribe pipeline

This is the canonical decomposition future file-processing workflows copy. It
turns the god-node workflow `Inbox → Local Transcribe (Whisper)`
(id `Yw0WvYW1yAU1QG49`) into atomic, reusable, bus-native steps.

## Before (the god-node)

```
[Watch Inbox]  [Watch Ingest] → [Parse File for Audio] → [Run Transcribe]
                                                              └─ executeCommand:
                                                                 transcribe "$sourcePath" --archive-s3
```

`Run Transcribe` alone did: S3 upload + verify, fallback stash, whisper +
diarization, log-parse, (remote) scp-back. Zero canvas visibility; every failure
meant editing bash in a daily-critical workflow; and it emitted **none** of the
five already-defined `audio.*` bloodbank events.

## After (target topology)

```
[Watch Inbox]   [Watch Ingest]
       \             /
     [Parse File for Audio]  (Bxgua92kxXkycFB4 → sourcePath)
              │
     [Emit audio.transcription.started]           → bloodbank
              │
     [Archive → S3/MinIO]  ──error──▶ [Stash → ~/audio/recovered]
              │                              │
              └────────── merge ────────────┘        ← backup-first, never-delete = VISIBLE
              │
     [Transcribe]  (pure: audio → {mdPath,text,segments,duration,model,lang,speakers})
        │   └──error──▶ [Emit audio.transcription.failed]  → bloodbank
        │
     [Deliver → Vault]  (route note, set triage status)
              │
     [Emit audio.transcription.completed]         → bloodbank → toaster → ntfy + all consumers
```

## Node-by-node contract

| Node | Implemented by | In → Out |
|---|---|---|
| Watch Inbox / Watch Ingest | `localFileTrigger` (existing) | fs event → `{path}` |
| Parse File for Audio | subworkflow `Bxgua92kxXkycFB4` (existing) | `{path}` → `{sourcePath}` |
| Compute S3 key | inline `Code`/`Set` | `{sourcePath}` → `+ {s3Key: "YYYY-MM-DD/HHMMSS-<base>"}` (from file mtime) |
| Archive → S3 | `n8n-nodes-minio` now; `n8n-nodes-delo-minio` later | put to `recordings/<s3Key>`, stat-verify → `+ {s3Uri}`; error output on failure |
| Stash (fallback) | inline `Execute Command` | copy source → `~/audio/recovered/` (error branch only) |
| Transcribe | thinned `bin/transcribe` via `Execute Command`; `n8n-nodes-transcribe` later | `{sourcePath}` → structured JSON (below) |
| Deliver → Vault | `n8n-nodes-vault` later; near-term this is transcribe.py's own write | place/route md, set `triage` status |
| Emit started/completed/failed | `HTTP Request` now; `n8n-nodes-bloodbank` later | → bloodbank (→ bloodbank-emit) |

## The thinned-script contract

The Transcribe step must do **only** transcription. Refactor `bin/transcribe`
(HeyMa, `/home/delorenj/code/HeyMa/bin/transcribe`) so that:

- **Removed:** `--archive-s3`, `archive_to_s3()`, `stash_local()` — n8n owns those
  now as visible nodes. (The script's own safety logic becomes graph topology.)
- **Simplified:** n8n runs **on** `big-chungus` (the transcribe host), so `is_local()`
  is always true — the remote scp path is dead code from n8n's perspective.
- **New stdout contract:** emit one JSON line instead of just the md path:
  ```json
  {"mdPath":"…","model":"…","durationSec":0,"language":"…","speakers":0,"host":"big-chungus"}
  ```
  (Keep `text`/`segments` optional/behind a flag — large payloads.) A `Set` node
  parses it so downstream nodes and the completed-event `data` have real fields.

Ordering invariant preserved: **Archive runs before Transcribe.** The source is
irreplaceable; secure it first. No node deletes the source.

## Migration notes

- The workflow already has `settings.availableInMCP: true` — MCP tooling can edit
  it. For tags / long descriptions use direct `PUT /api/v1/workflows/{id}` with the
  `{name, nodes, connections, settings}` envelope (→ gotchas).
- Build it as a **new** workflow first, pin-test with the existing `Watch Inbox`
  pinData (`clip_0055.mp3`), verify events land on `ntfy.delo.sh/bloodbank`, then
  cut the triggers over and archive the old one. Don't refactor the live daily
  workflow in place.
- Do the split in the ladder's order: get SRP + Secure Source + the three bloodbank
  emits working with **host CLIs** (`secure-source` + `bb-emit`) invoked from
  `Execute Command`, then promote Secure-Source/Transcribe/Vault/Emit to custom
  `n8n-nodes-*` nodes as each earns it.

## Status — built & verified (workflow `r2TUca8smk5HDNZx`)

The v1 rebuild exists as **`Inbox → Transcribe → Bloodbank (v2)`** (`r2TUca8smk5HDNZx`),
**inactive** pending cutover. Two host CLIs were extracted from the god-script and
back the Execute-Command nodes:

- `~/.local/bin/secure-source` — S3 archive (mc → `delo/recordings/YYYY-MM-DD/HHMMSS-<file>`)
  + verify, stash to `~/audio/recovered` on failure, never deletes the source, prints
  JSON. This is the archive/stash logic lifted out of `bin/transcribe`.
- `~/.local/bin/bb-emit` — the NATS-direct envelope publisher (→ bloodbank-emit).

Verified end-to-end (exec 222155, 6.8s clip): `started` + `completed` both published,
sharing `correlationid` derived from the transcription_id. Transcribe still writes the
markdown itself (to `~/d/Transcripts/`, NOT the stale `~/d/Notes/Transcripts` in older
docs); a dedicated `n8n-nodes-vault` step (routing + triage status) is the next promotion.

Cutover: activate `r2TUca8smk5HDNZx` and deactivate the old god-node workflow
`Yw0WvYW1yAU1QG49` in the same change (two active `localFileTrigger`s on the same dirs
would double-process).
