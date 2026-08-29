# Incident log — every outage, its signature, and what actually caused it

Read this early. This pipeline breaks in **repeating shapes**, and matching the
signature has repeatedly been faster than reasoning from first principles.

Newest first. Add to the top when you resolve something; a troubleshooting skill
that does not learn is just documentation.

---

## August 22, 2026 · GDM restart stranded a 23-hour capture · *audio graph teardown*

**Signature.** The tray returned yellow after the graphical session restarted.
`wax state` and `wax status` exited 2, and the stream reported
`error-partial (uninstructed_exit)`. The inbox and all pipeline stages were
healthy, but the doctor mislabeled the nonzero state result as `wax-cli`, which
made a capture fault look like a broken control plane.

**Cause.** A privileged `systemctl restart gdm` stopped the graphical user
session. The encoder's transient scope correctly outlived `waxd` by about 12
seconds, but D-Bus, PipeWire, and WirePlumber then stopped. FFmpeg exited when
its Pulse source graph disappeared. This was not a machine reboot: the boot ID
before and after the failure was identical.

**Recovery.** All 1,381 Ogg segments were independently valid: 273,860,321
bytes and 82,851.326 seconds. Wax remuxed them into a 273,651,230-byte recording,
verified its S3 object by size and multipart ETag, and parked the local copy
under `skipped/overduration/`. The original segment set remains under
`recovered/orphans/`, with a matching aggregate SHA-256 fingerprint.

**Fix.** Salvage now moves every original segment and sentinel into
`recovered/orphans/` instead of deleting the segment directory. A dedicated
systemd capture guard runs `wax rec quiesce` before an orderly graphical-session
teardown removes D-Bus or PipeWire. The doctor now separates CLI validity from
stream health and routes `error-partial` directly to the capture playbook.

**Checks that now catch it:** `stream-healthy`, `capture-guard-active`.

## 2026-08-21 · CUDA available, diarization on CPU · *execution overrode its own model loader*

**Signature.** Torch reported CUDA 13.0 and an RTX 3090, and importing the old
backend even allocated ~918 MiB on `cuda:0`, but every production log said
`Running diarization (cpu)`. Long recordings spent tens of minutes diarizing on
CPU despite a healthy GPU runtime.

**Cause.** The backend automatically loaded Sortformer onto CUDA, including one
hidden model at module import. `scripts/transcribe.py` then loaded a second copy
and explicitly moved that model and preprocessor to CPU under a stale
"partial CUDA runtime" workaround. No setting controlled this, and metadata did
not record the actual device.

**Fix.** Replaced the ignored WhisperLiveKit dependency with the tracked,
side-effect-free `wax.diarization_sortformer` adapter; made
`WAX_DIARIZATION_DEVICE=cuda` the strict default; kept ASR and diarization device
policies independent; pinned the rebuild manifest; and added requested/actual
device evidence to logs, transcript frontmatter, and adapter provenance. Both
the installer and doctor now load Sortformer and execute a real streaming CUDA
forward pass.

**Checks that now catch it:** `diarization-device`, `diarization-cuda`, plus the
primary `wax doctor` probes `diarization device policy` and
`diarization cuda runtime`.

---

## 2026-08-15 → 2026-08-19 · title-slug 404 · *dependency deleted off the host*

**Signature.** Transcripts land correctly but keep bare timestamp filenames
(`20260819-103057-rec.md`). Frontmatter shows
`wax.passes.title-slug: {state: failed}` with **no reason**, timestamped ~50 ms
after the pass started. Tray green. `wax status`: "no errors". Journal: empty.

**Cause.** The Ollama model `qwen3.6:latest` pinned by `title-slug.yaml` was
deleted from `/usr/share/ollama/.ollama/models` on 2026-08-15 09:47:53. Every run
POSTed `/api/chat` and got HTTP 404 in ~1 ms.

**Why it took five days.** Three independent failures of disclosure:
`urllib.error.HTTPError` is a subclass of `URLError`, so the body naming the
missing model was swallowed and rendered as the bare string
`HTTP Error 404: Not Found`; `reason_code` could not distinguish a missing model
from a timeout (both exit 1 ⇒ `nonzero_exit`); and no surface read the `passes`
table at all.

**Blast radius beyond titles.** `passes.py` gated `archive.link_transcript` on the
EP returning a slug, so the entire audio↔transcript linkage in S3 stopped too. And
`frontmatter_schema` was applied inside `_apply_result`, reached only on `rc == 0`,
so a remote LLM outage also blocked a purely local, deterministic vault-taxonomy
stamp. **Lesson: never gate a deterministic local step on a remote call's exit code.**

**Fix.** Retired local inference for this pass. The provider is now pure config
(`WAX_TITLE_API_BASE` / `WAX_TITLE_MODEL` / `WAX_TITLE_API_KEY_OP`) against any
OpenAI-compatible endpoint, with a `/models` preflight, `reason_code=missing_model`,
and the provider's own error body preserved.

**Check that now catches it:** `title-model-present`, `no-recent-pass-failures`.

---

## 2026-08-12 → 2026-08-19 · no diarization · *`git reset --hard` in the other checkout*

**Signature.** Every transcript has `diarized: false`. No speaker labels. No error
anywhere the user would look. Ledger: last `diarized=1` at 2026-08-12T13:35:18Z,
then 128 consecutive zeros.

**Cause.** `~/.local/bin/transcribe` pointed at a **second checkout**
(`~/code/HeyMa`), 9 commits behind the tree everyone was editing (`~/HeyMa`). A
`git reset --hard origin/main` there fast-forwarded past commit `1d21e8b`, which
had deleted 63 files under `whisperlivekit/`. The editable install still mapped
`whisperlivekit` → that directory, which now held **0 `.py` files and 18 orphan
`.pyc`**. `diarize_local()` caught the `ImportError` and returned `[]`, so
`diarized: bool([])` was written as an honest `false`.

**Why the preflight did not catch it.** `missing_diarization_dependencies()`
probed `librosa` and `nemo` — both fine. Execution imported a **third** module,
`whisperlivekit.diarization.sortformer_backend_offline`, which was never checked.
The guard passed, up to 3 h of GPU ASR ran to completion, and the import died
afterwards. Measured waste on one job: **29 min 24 s of ASR**.

**Fix at the time.** Restored the subtree from history, moved the runtime into
the deployed tree, pinned `WAX_TRANSCRIBE` in the unit so PATH can never again
choose which code runs, and made the preflight import the real entry point. On
2026-08-21 the private backend was replaced entirely by the tracked owned Wax
adapter, removing this deletion class rather than merely detecting it.

**Lesson.** *A preflight that tests different modules than execution imports is
worse than no preflight* — it converts a hard failure into a silent downgrade and
buys false confidence. Test the actual entry point.

**Checks that now catch it:** `diarization-imports`, `same-checkout`,
`recent-diarized`, `no-diarization-error-in-log`.

---

## 2026-07-01 → 2026-07-14 · nothing transcribed for two weeks · *hardcoded path*

**Signature.** Recordings archived to S3 fine; no transcripts appeared. n8n showed
green executions.

**Cause.** The repo moved from `~/code/33GOD/HeyMa` to `~/code/HeyMa`, but
`bin/transcribe` had `TRANSCRIBE_DIR` hardcoded to the old path, so `cd
$TRANSCRIBE_DIR` failed and `transcribe.py` never ran.

**No audio lost** — the backup-first policy did its job, which is the entire reason
it exists. Everything was re-runnable from S3.

**Lesson.** This is the *same bug* as the 2026-08-12 incident wearing different
clothes: **the pipeline resolving its own code through a path that can drift.**
Both were "the code that ran was not the code that was edited." When something
inexplicably stopped working after a move, a reset, or a rename, check
`same-checkout` first.

---

## 2026-06-29 · a recording was destroyed · *wrote into a receive-only Syncthing folder*

**Cause.** A local writer dropped a file into a Syncthing `receiveonly` folder.
Files added locally to a receive-only folder are treated as divergent and get
reverted/deleted on any reconcile or folder-marker reset.

**Rule that came out of it.** Local writers never write into a receive-only
folder. `dropoff/` is Syncthing's; **`waxd` copies out of it and never writes into
it.** Recordings go to `inbox/`.

---

## Standing traps (not incidents — things that will mislead you *right now*)

- **`~/audio/var/state.json`** — a mirror from 2026-07-30 asserting inbox error,
  `scheduler_disabled`, 102 pending, tray yellow, and a dead PID. Unreachable by
  any running code, false in every field, and formatted exactly like a live status
  mirror. It already sent one investigation down the wrong hole.
- **Repo-root `passes.d/`** — a registry the runner never loads, whose commands
  point at a nonexistent `~/audio/passes.d/bin`, and which lacks `title-slug.yaml`
  entirely. Editing it changes nothing. The real one is
  `components/wax/config/passes.d/`.
- **Repo-root `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`** — described the retired
  n8n pipeline long after Wax replaced it, and are loaded into every agent's
  context in this repo.
- **n8n workflow `r2TUca8smk5HDNZx`** — reported `active: true` while its own
  description claimed it was inactive, with a `localFileTrigger` on
  `~/audio/inbox`. Quiet only because Wax moved. Any write there triggers an
  out-of-band transcribe with no ledger row and a duplicate S3 object.
- **`wax.db` mtime** — WAL mode leaves it untouched for hours. It looks abandoned
  when it is busy.
- **`systemctl status` memory** — counts reclaimable page cache from transcription
  children and reads ~4 GB while waxd's true RSS is ~53 MB. Use `/proc/<pid>/status`.
- **MinIO is one drive.** `EC:0`, un-versioned, and its `/data` is a bind mount on
  `/dev/nvme0n1p2` — **the same partition as the original audio**. The archive
  protects against deletion and corruption, not against losing that disk.

## The pattern behind all of it

Every verified defect in this pipeline's history is one of three shapes:

1. **An outside observer guessing the state of something it does not own**
   (a size-settle timer guessing at the recorder, `stat()` guessing at ffmpeg).
2. **The code that ran was not the code that was edited** (a drifted path, a
   second checkout, a stale symlink).
3. **A sub-stage degrading to an empty value with no path from "degraded" to
   "a human is told."**

When you find a new failure, name which of the three it is. If it is a fourth,
that is genuinely new — write it down here.
