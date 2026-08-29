# Transcription & diarization — playbook

Symptoms that land here: `diarized: false` on everything; no speaker labels; a
transcript that never appeared; a `.suspect.md` file; transcription that seems to
hang.

## The chain, and the two places it splits

```
waxd → worker.process → transcribe_adapter.transcribe_command()
         │
         ├─ $WAX_TRANSCRIBE if set          ← pin this; PATH is not a contract
         └─ else shutil.which("transcribe") → ~/.local/bin/transcribe → SOME repo
                 │
                 ▼
           bin/transcribe (shell)
                 │  picks the interpreter:
                 ├─ $TRANSCRIBE_DIR/.venv-diarization/bin/python   → diarization ON
                 └─ else `mise x -- uv run python`                 → required run degrades loudly
                        │
                        ▼
                 scripts/transcribe.py → faster-whisper large-v3 (CUDA/auto policy)
                        └─ tracked wax.diarization_sortformer (strict CUDA default)
```

**Both splits have caused multi-day silent outages.** The `transcribe` binary
resolving into a different checkout than the daemon, and the venv selection
degrading without an error. Check `same-checkout` and `diarization-imports` before
anything else.

## Diarization triage

### 1. Confirm it is actually off

```bash
sqlite3 -readonly "file:$HOME/HeyMa/var/wax.db?mode=ro" \
  "SELECT created_at, diarized FROM transcripts ORDER BY created_at DESC LIMIT 10;"
```

Nothing else reports this. `sanity.py` checks duration and word count only; a
requested-and-failed diarization is indistinguishable from an honest
single-speaker result unless you look here.

### 2. Read the per-item log — the error only exists here

```bash
tail -40 "$(ls -t "$HOME/HeyMa/var/logs"/*/transcription.*.log | head -1)"
```

Look for `Diarization-Device`, `DIARIZATION-DEGRADED`, `Diarization device
preflight failed`, `Failed to load diarization model`, or `Diarization failed`.
Every successful production run records both requested and actual device.

### 3. Test the imports in the venv that will actually be used

```bash
T=$(readlink -f "$(command -v transcribe)")
R="$(dirname "$(dirname "$T")")"
D="$R/.venv-diarization/bin/python"
echo "transcriber: $T"; echo "venv: $D"
PYTHONPATH="$R/components/wax/src" "$D" -c \
  "from wax.diarization_sortformer import cuda_smoke; print(cuda_smoke())"
```

Run it against the venv beside the **resolved** transcriber, not the one you
expect to exist. That distinction is the whole 2026-08-12 incident.

### 4. Common causes, in the order they actually happen

| Finding | Cause | Fix |
|---|---|---|
| `No module named 'wax.diarization_sortformer'` | checkout predates the tracked adapter or `WAX_TRANSCRIBE` points elsewhere | update the deployed checkout and confirm `same-checkout` |
| no `.venv-diarization` at all | venv was deleted, lives in the other checkout, or was never built | `mise run wax:diarization:install` (pinned manifest + real CUDA smoke) |
| imports fine but still `diarized=0` | Sortformer weights not cached and the host is offline | check `~/.cache/huggingface/hub/models--nvidia--diar_streaming_sortformer_4spk-v2` (~450 MB) |
| `Diarization-Device` says `cpu` | `WAX_DIARIZATION_DEVICE=cpu/auto`, or old code forced CPU after loading | set strict `cuda`, reinstall the unit, restart waxd, run `wax doctor` |
| `transcribe` resolves outside the deployed repo | the two-checkout split | pin `Environment=WAX_TRANSCRIBE=/home/delorenj/HeyMa/bin/transcribe` in `waxd.service` |

### 5. The `WAX_DIARIZATION` trap

`WAX_DIARIZATION=1` means the stage is required and a missing speaker track is
reported as degraded; falsy values are the only opt-out. Device selection is a
separate contract: `WAX_DIARIZATION_DEVICE=cuda` is the strict production
default, `cpu` is an explicit escape hatch, and only `auto` may fall back to CPU.
An ASR `--device cpu` retry does not alter the diarizer device. The load-bearing
test is `wax doctor`: it executes a real Sortformer streaming step on CUDA.

## Transcription itself

`faster-whisper` `large-v3` on CUDA float16. This half has been reliable; when it
does fail it fails loudly.

**Limits** (exclusive ceilings, both configurable in the unit):
`MAX_AUDIO_FILE_SIZE_FOR_TRANSCRIPTION` (300MB) and
`MAX_AUDIO_DURATION_FOR_TRANSCRIPTION` (3h). A file *at* the ceiling is blocked.
An oversized item is skipped, not failed — check `wax items` if a large recording
never produced a transcript.

**The duration gate.** After transcription, `sanity.check()` compares ffprobe's
duration against whisper's `info.duration` with `MIN_RATIO 0.95` (30 s absolute /
5 % relative tolerance, unknowns fail closed). A mismatch writes
`<stem>.suspect.md` and **leaves the item in the inbox** rather than publishing a
truncated transcript as complete. A `.suspect.md` means "whisper stopped early" —
usually a corrupt or truncated source. Check the audio with `ffprobe` before
re-running.

**Concurrency is 1**, and `bin/transcribe` holds its own flock. A long meeting
blocks the queue; that is intended, not a hang. Watch progress with:

```bash
journalctl --user -u waxd.service -f
tail -f "$(ls -t "$HOME/HeyMa/var/logs"/*/transcription.*.log | head -1)"
```

## Re-running a transcription

The source audio is always in S3 (archive-before-transcribe), so any transcript is
recomputable:

```bash
bin/wax transcribe <path-to-audio>      # with the sanity gate
bin/wax drain                            # process the inbox now, one-shot
```

Re-transcribing does **not** re-run enrichment for an item already parked
`complete` — use `wax ep sweep` for that (see `enrichment.md`).
