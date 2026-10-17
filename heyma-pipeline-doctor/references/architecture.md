# Architecture — the moving parts, and where each one can fail

One daemon owns everything. `waxd.service` (user unit, `PartOf=graphical-session`)
runs `components/wax/bin/waxd`, which is the parent of the encoder and of every
worker. Liveness comes from `Popen.wait()` and `renameat2()` return values, never
from `stat()`. Recoverability comes from sentinels written to disk *before* the
first audio byte, so a cold CLI can recompute state after a SIGKILL.

## The path a recording takes

```
Ctrl+\ (GNOME keybinding → ~/.local/bin/wax-toggle → wax rec toggle)
  │                                          also: wax rec start, NATS command
  ▼
stream/<rid>.segs/*.ogg          ffmpeg, 60 s segments, sentinels beside them
  │  encoder exits 0 AND ffprobe > 0.5 s
  ▼  renameat2(RENAME_NOREPLACE)
inbox/YYYYMMDD-HHMMSS-<slug>.ogg          ← also fed by dropoff/ (Syncthing)
  │
  ├──► archiver ──► S3 s3://recordings/YYYY-MM-DD/<sha12>-name
  │                 + <key>.wax.json + .by-content/<sha256>.json   [BEFORE transcription]
  │
  ▼  transcriber, concurrency 1
faster-whisper large-v3 (CUDA) ─┬─► text
                                └─► Sortformer diarization (separate venv)
  │  duration gate: ffprobe vs whisper info.duration, MIN_RATIO 0.95
  ▼
~/d/Transcripts/<name>.md        (→ ~/code/DeLoDocs/Transcripts)
  │
  ▼  enrichment passes — a FROZEN plan per item
frontmatter-stamp · clipboard-copy · classification · title-slug (renames the file) · diarization
  │   siblings run independently; requires/after gate and order within the plan
  │   transcription.completed is written ONLY when every planned pass completed/skipped
  │
  ▼  only after a live S3 HEAD re-verify
archive/YYYY/MM/<audio>          the audio is NEVER deleted
```

Documents are a second flow with no audio and no ledger `transcripts` row:
`~/d/Inbox/Wax` (→ `~/code/DeLoDocs/Inbox/Wax`) is scanned by the worker every
`WAX_DOCUMENT_SCAN_INTERVAL_S` (default 120 s); a compiled `documents` pipeline
(e.g. `doc-standard`: classification → title-slug) runs document-capable passes
over new arrivals only, proposing frontmatter/body — document runs reject
events and never rename. Detailed operation: the `wax-pipeline` skill.

Every edge also writes a row to the ledger and an event to the outbox, in the same
transaction. `waxd` drains the outbox to NATS every 10 s.

## Where state lives

| Thing | Path | Notes |
|---|---|---|
| Root | `$WAX_ROOT` → `$WAX_AUDIO_ROOT` → `~/HeyMa` | **everything is under the repo** |
| Ledger | `<root>/var/wax.db` | SQLite, WAL. Audio tables: items, backups, transcripts, passes, transitions; plan/event tables: processing_plans, completions, pass_events; pipeline/document tables: pipelines, documents, document_receipts, document_bindings; plus files_seen, meta, outbox |
| State mirror | `<root>/var/state.json` | rewritten ~1/s; a snapshot, not the source of truth |
| Control socket | `<root>/var/waxd.sock` | raw AF_UNIX, not HTTP |
| Scheduler flag | `<root>/var/pipeline.enabled` | absent ⇒ operator-paused |
| Per-item logs | `<root>/var/logs/<item_id>/transcription.N.log` | the only place diarization errors appear |
| Pass registry | `components/wax/config/passes.d/*.yaml` | **not** repo-root `passes.d/`; re-read on every call |
| Pipeline authoring | `components/wax/config/pipelines.d/*.yaml` (+ n8n export import) | compiled explicitly into frozen versioned definitions (`pipelines` table) |
| Transcripts | `$WAX_VAULT` → `~/d/Transcripts` | symlink into the notes vault; **output**, not watched |
| Document inbox | `~/d/Inbox/Wax` (→ `~/code/DeLoDocs/Inbox/Wax`) | new-arrivals-only binding, scanned every `WAX_DOCUMENT_SCAN_INTERVAL_S` (120 s) |
| Diarization runtime | `.venv-diarization/` + tracked `components/wax/src/wax/diarization_sortformer.py` | pinned by `requirements-diarization.txt`; rebuild with `mise run wax:diarization:install` |

## The two state machines

**`stream/`** — `ready` → `recording` → `not-ready` (finalizing) → `ready`, with
`error-partial` for an uninstructed encoder exit and a sticky `error` catch-all.
Detection is literal: sentinel files plus an `alive()` triple of
(boot_id, `/proc/<pid>` exists, exe is ffmpeg, matching starttime). A stale
`boot_id` makes every pre-reboot claim false by construction, which is how reboots
and OOM kills are caught for free.

**`inbox/`** — `stopped` / `ready-and-waiting` / `ready-and-active` / `error`.
`error` means work is present with no live worker claim for >60 s.

Note `not-ready` is genuinely two conditions bolted onto one label, so the payload
carries a `clause`: `a-finalizing` (sub-250 ms normally, with a 45 s deadline so a
dead finalizer degrades to `error-partial` instead of wedging forever) and
`b-incapable` (preflight failed: no default source, disk low, dir unwritable).

## The health model — a historical blind spot, now narrowed

**The dated defect.** `tray.colour_for(snap)` used to derive the icon from
`stream.state`, `inbox.state`, `inbox.pending`, and `queue.failed` only —
`worker.process()` parked the audio and set the item `complete` *after* a pass
had already been recorded `failed`, so a 100 %-failing enrichment stage was
invisible to the icon by construction. That is how the five-day title-slug
outage stayed green.

Since then the snapshot carries `passes` and `diarization` blocks
(`ledger.enrich()`), the tray turns yellow on failed passes, degraded
diarization and an outbox backlog (with the failing slugs in the tooltip), and
`notify_stage_failure` puts a dead sub-stage on the desktop. Completion itself
is plan-gated: a failed pass leaves the item `enrichment_pending`, and an
exhausted pass dead-letters via `bloodbank.audio.task.exhausted`.

**Practical consequence for you:** the ledger is still the source of truth
about whether work actually succeeded. The tray and `wax status` summarize;
they are not proof.

## Deliberate design choices that look like bugs

- **No size-based stall detector.** A partial that stops growing while the encoder
  is alive raises a journald warning and a yellow tint only — it never mutates a
  file. Inferring a writer's state from `stat()` is what truncated a good
  recording once; the encoder's *exit* is the only trigger.
- **Ogg/Opus, not m4a.** A truncated Ogg stream is page-structured and remuxable.
  A truncated m4a is a brick.
- **Archive before transcribe.** The audio is irreplaceable; the transcript is
  recomputable. If S3 fails, the source is kept *and* stashed in
  `recovered/unbacked/`, and transcription still proceeds.
- **Diarization enablement and device are independent.** `WAX_DIARIZATION=1`
  requires a speaker track; `WAX_DIARIZATION_DEVICE=cuda` separately requires
  Sortformer to run on GPU. An ASR CPU retry never changes the latter.
- **`requires` gates and orders; siblings stay independent.** `requires` is a
  supported registry field: it orders a pass after its dependencies AND gates
  it (a requirement not `completed`/`skipped` records `dependency_failed`). A
  requirement that is missing, disabled, quarantined or manual-when-auto
  quarantines the dependent loudly instead of failing quietly. What remains
  true: a *failed* pass never stops a sibling that does not require it, and
  `after:` orders without gating at all.
- **Audio plans are frozen at mint.** With exactly one compiled+enabled
  `transcription` pipeline, new items get their pass plan from its frozen
  definition; a registry edit changes nothing for items already planned, and a
  minted plan never migrates when the graph changes.
- **Four passes are `enabled: false` placeholders** (domain-curation, mem-ops,
  transcription-enhance, wikification). They are unbuilt, not broken. Do not
  "fix" them. `project-extraction` and `ticketable` are implemented but
  deliberately disabled — also not broken.
