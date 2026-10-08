# Converting a single chapter to audio

`prepare -> chunk -> synthesize -> assemble -> master -> ASR QA -> (usage)`. Every stage is idempotent and
resumable; the unit of resumption is the chunk. Assumes the chapter's `chapter.json` exists (see
character-research.md) and the voices are designed or pinned (voice-design.md).

```bash
S=~/.agents/skills/ebook-to-audiobook/scripts; B=<book dir>; N=01
M=$B/chapters/$N/chapter.json; O=$B/chapters/$N/audio
python3 -B $S/render_chapter.py prepare --manifest $M --output $O --book $B   # plan + exact token counts
python3 -B $S/render_chapter.py voices  --manifest $M --output $O --book $B   # design only the new speakers
python3 -B $S/render_chapter.py preview --manifest $M --output $O             # listen to the cast first
python3 -B $S/render_chapter.py render  --manifest $M --output $O --book $B --limit 5   # optional 5-chunk audition
python3 -B $S/render_chapter.py render  --manifest $M --output $O --book $B   # the rest, then assemble + master + mp3
python3 -B $S/verify_audio.py --manifest $M --root $O --phase all --max-chunks 24      # writes $O/qa-all.json
python3 -B $S/render_chapter.py report  --manifest $M --output $O --book $B   # metrics.json
python3 -B $S/book.py --dir $B progress set --chapter 1 --stage done
```

Add `--book $B` everywhere (or none anywhere) so `book.json` tracks voices, artifacts and the marker.
Run `render` in the background for a full chapter (30-45 min for an hour of audio) and poll
`render_chapter.py status`; the process holds an exclusive `.lock` on the output dir, so a second
command fails fast instead of racing.

## 1. Prepare

Validates the manifest, chunks all segments, and asks the engine container for the **exact VoxCPM2 input
text token count** of every design prompt and chunk (`--tokenizer none` skips this and records `null`).
The plan (`prepared.json`) embeds the manifest hash, model revision, pinned-reference hashes and a
`plan_sha256`. A later run that computes a different plan (edited text, new model snapshot, changed clip)
is refused: use a **fresh output directory** instead of patching a cache. Speakers with no segments are not
designed.

## 2. Chunk

`chunk_text` splits on sentence boundaries to about 450 characters (hard max 650), preferring commas/dashes only when
a single sentence is longer than the limit, and proves `" ".join(chunks) == normalized(text)`. Segment boundaries are
never merged across speakers. The pilot: 267 segments -> 296 chunks, no truncation. Sentences longer than 650
characters (the Old Mistress' speech) are the reason the splitter has a punctuation fallback.

## 3. Synthesize

For each chunk, in order: build the request spec (text + cfg/steps + model revision + reference hash), check the
cache, else write a `started` line to `requests.jsonl`, POST to the sidecar with the speaker's reference clip,
validate the response, write `chunks/<id>.wav` + `<id>.json` atomically, append `success`. Hard failures: a response
engine other than `voxcpm`, a WAV whose bytes/sample-rate/duration disagree with the reply, truncated PCM, invalid
base64. A cache hit requires the fingerprint, the WAV bytes and a matching success receipt to all agree; stray files in
`chunks/` abort the run.

Throughput on the RTX 3090 (pilot): 296 chunks, 2,961 s of audio, 1,420 s synthesis (RTF ~0.48, about 28 characters of
text per second of wall time). Plan roughly half the audio duration of wall time, plus ~15 s JIT on the first call after
an engine restart. Each call has `--max-time 240`; chunks are far below that.

Interruption: a killed run leaves a `started` line with no result. The next run refuses to continue
("Prior failed/unfinished request") until you confirm the engine is idle (`nvidia-smi`, `docker logs voxxy-engine-voxcpm`)
and pass `--retry-failed`. This is deliberate: a timed-out client request can still be running, and a duplicate
would double-charge GPU time and muddy the ledger. Successful chunks are never regenerated; a `success` receipt
with a lost WAV also aborts (investigate, do not silently re-roll a voice take).

## 4. Assemble and master

Chunks join in order with silence by boundary: 280 ms between paragraphs, 120 ms between speakers/segments, none inside
a segment, and 8 ms linear fades on every chunk edge to kill clicks. Rates, channel counts and widths must match across
chunks. The raw join (`chapter.raw.wav`) is kept. Mastering is a **two-pass `loudnorm` over the whole chapter** (target
-20 LUFS, -3 dBTP, LRA 7; measured pass feeds `linear=true`), then `chapter.wav` (PCM16 48 kHz mono) and
`chapter.mp3` (128 kb/s). `assembly.json` records frames, pause totals and SHA-256 of every output; a rerun that finds
a matching `assembly.json` verifies the files and returns without touching them (3.5 s for the pilot chapter, 0 synth calls).

Pilot result: 3,020.08 s (50:20); -20.06 LUFS, -2.91 dBTP (0.09 dB over target, reported as such), LRA 5.5 LU.

## 5. ASR QA

`verify_audio.py` runs faster-whisper large-v3-turbo on **CPU int8** inside the `transcription-worker-1` container
(`CUDA_VISIBLE_DEVICES=` empty, `nice -n 15`, hard timeout) so it cannot starve the TTS GPU, loads the model once,
and transcribes evenly spaced samples (`--max-chunks 24`, plus refs when `--phase all`) against the expected text
recorded in each chunk's metadata. It writes `qa-<phase>.json`, refuses to overwrite renderer files, and marks the run
`incomplete` (exit 1) if any sample failed to transcribe, rather than reporting a flattering WER from the survivors.

Reading the report (pilot: 24 chunks, 792 words, 9 edits, **WER 1.14%**, 109 s):

- `worst_wer_samples` first: listen to them. Real defects found: "asked"->"ask" and "Then he"->"They" (a mangled opening).
- Low-confidence trailing words (a stray "you" at 4.8% probability, a 40 ms timestamp) are usually ASR hallucination.
- Spelling variants (Wang/Wong, skilful/skillful, grey/gray) and dash tokenization are noise.
- 24/296 is a sample. If anything real turns up, widen it (`--max-chunks 60`) or pass `--samples` with the suspect chunks.
- **Re-roll one bad chunk** without redoing the chapter:
  `render_chapter.py redo --manifest $M --output $O --chunk 000116 --reason "ASR: opening mangled"` then `render` again.
  The old take moves to `superseded/<stamp>/` (with the stale assembly), stays in `requests.jsonl` so metrics still count
  its GPU time, and the next `render` makes exactly one new call and reassembles. A re-roll can fail the same way;
  if the same chunk keeps mangling, fix its text in the source and use a fresh output directory.
- ASR cannot hear wrong emphasis, wrong accent, or a voice that drifted. Spot-listen to 5-10 minutes across speakers.

## 6. Hand-off

`metrics.json` (from `report`) holds per-phase and per-speaker call counts, wall seconds, audio seconds, exact TTS text
tokens, failures, and `observed_paid_provider_charge_usd: 0` (true because engine!=voxcpm is a hard failure), with
energy/tools/LLM cost deliberately `null` unless supplied (usage-accounting.md). Then:

```bash
python3 -B $S/book.py --dir $B artifact verify          # hashes still match?
python3 -B $S/book.py --dir $B progress set --chapter 1 --stage done
python3 -B $S/book.py --dir $B resume                   # points at chapter 2
```

## Output directory contents

| file | purpose |
| --- | --- |
| `prepared.json` | frozen plan; the identity of this render |
| `requests.jsonl` | append-only started/success/failure ledger of every synth call |
| `refs/<id>.wav/.json` | designed reference clips + receipts |
| `chunks/<id>.wav/.json` | chunk audio + the exact request that produced it |
| `chapter.raw.wav`, `chapter.wav`, `chapter.mp3` | joined, mastered, delivered |
| `assembly.json` | pause/fade/mastering parameters and output hashes |
| `qa-*.json` | ASR diagnostics |
| `metrics.json`, `llm-usage.json` | totals; supplied LLM snapshot |
| `voice-preview.wav/.mp3` | cast sampler (from `preview`) |

## Troubleshooting

| Error | Meaning / fix |
| --- | --- |
| `Another chapter command owns this output directory` | A render is running; use `status` instead |
| `Prepared manifest, tokens, or model revision changed` | Text, clip or model changed; new `--output` |
| `Unknown cache files in .../chunks` | Something else wrote there; move it out |
| `Synthesis response engine must be voxcpm` | Sidecar down or URL points at core; check `/healthz` in the engine container |
| `Cannot split text without breaking a word` | A 650+ character token (OCR run-on); fix the text |
| `ffmpeg loudnorm did not return whole-chapter measurements` | Silent or malformed audio; inspect `chapter.raw.wav` |
| `docker: Error response ... No such container` | Override `--via-container`, `--engine-container`, `ABK_ASR_CONTAINER` |
