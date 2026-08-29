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
  ▼  enrichment passes — independent, per-slug
frontmatter-stamp  →  title-slug (renames the file to a summary slug)
  │
  ▼  only after a live S3 HEAD re-verify
archive/YYYY/MM/<audio>          the audio is NEVER deleted
```

Every edge also writes a row to the ledger and an event to the outbox, in the same
transaction. `waxd` drains the outbox to NATS every 10 s.

## Where state lives

| Thing | Path | Notes |
|---|---|---|
| Root | `$WAX_ROOT` → `$WAX_AUDIO_ROOT` → `~/HeyMa` | **everything is under the repo** |
| Ledger | `<root>/var/wax.db` | SQLite, WAL. Tables: items, backups, transcripts, passes, outbox, transitions |
| State mirror | `<root>/var/state.json` | rewritten ~1/s; a snapshot, not the source of truth |
| Control socket | `<root>/var/waxd.sock` | raw AF_UNIX, not HTTP |
| Scheduler flag | `<root>/var/pipeline.enabled` | absent ⇒ operator-paused |
| Per-item logs | `<root>/var/logs/<item_id>/transcription.N.log` | the only place diarization errors appear |
| Pass registry | `components/wax/config/passes.d/*.yaml` | **not** repo-root `passes.d/` |
| Transcripts | `$WAX_VAULT` → `~/d/Transcripts` | symlink into the notes vault |
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

## The health model — and its structural blind spot

`tray.colour_for(snap)` derives the icon from `stream.state`, `inbox.state`,
`inbox.pending`, and `queue.failed`. `queue` comes from `ledger.inbox_counts()`,
which tallies **item** states for files **physically present in the inbox**.

That is the whole problem. `worker.process()` parks the audio out of the inbox and
sets the item `complete` *after* a pass has already been recorded `failed`, so a
100 %-failing enrichment stage is invisible to the icon by construction. The
snapshot now carries `passes` and `diarization` blocks (see
`ledger.enrich()`) precisely so this class of degradation is representable.

**Practical consequence for you:** the ledger is the source of truth about whether
work actually succeeded. The tray is a summary of the *capture* machine, and only
recently of anything else.

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
- **Passes are independent by contract.** `requires:` exists in the schema but a
  non-empty value is refused. A pass failing must not block another pass.
- **Four passes are `enabled: false` placeholders** (domain-curation, mem-ops,
  transcription-enhance, wikification). They are unbuilt, not broken. Do not
  "fix" them.
