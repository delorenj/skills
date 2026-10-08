---
name: ebook-to-audiobook
description: Turn an ebook, scanned PDF or EPUB into a multi-voice audiobook chapter by chapter with the local Voxxy/VoxCPM2 engine on the RTX 3090 - book metadata and resume markers, character research, per-character voice design, single-chapter conversion with ASR QA, and optional token/cost accounting. Use when asked to narrate, convert, resume or continue an audiobook, design or reuse character voices for a book, or record what a book build used. Not for one-off speech or cloning a person's voice (vox-tts), upgrading the Voxxy engines (vox-tts), speech-to-text of existing audio, or publishing and distributing the result.
---

# ebook-to-audiobook

Local, resumable, multi-voice audiobooks. Proven on *The Good Earth* chapter 1: 50:20 of
audio, 11 designed voices, 307 local synthesis calls (0 failures, 0 paid TTS), 24 sampled
chunks at 1.14% ASR word error. Everything below is what that run taught.

```
extract_pages -> prepare_chapter text -> research cast -> prepare_chapter quotes/build
   -> render_chapter prepare -> voices -> render -> verify_audio -> (usage.py)
                 every step mirrors into  <book>/book.json  (voices, progress, artifacts)
```

Scripts live in `scripts/` (stdlib-first Python 3.11+, `python3 -B`). Set
`S=~/.agents/skills/ebook-to-audiobook/scripts`. Tests: `cd $S && python3 -B -m unittest discover -s tests`.

## Preflight (30 seconds, before any render)

1. `voxxy health --json` is not enough. Check VoxCPM itself:
   `docker exec vox curl -fsS --max-time 10 http://voxxy-engine-voxcpm:8000/healthz` must say `ready: true`.
2. `nvidia-smi` has headroom (VoxCPM ~5 GB; VibeVoice ~7.5 GB; both can be resident).
3. `ffmpeg`, and for QA the `transcription-worker-1` container (override with `ABK_ASR_*` env).
4. Rights: record them in `book.json` (`source.rights`). A 1931 US work enters the public domain
   on 2027-01-01 (95 years). Personal listening from a supplied copy is the working assumption.

## Book workspace

One directory per book (default location `~/audiobooks/<slug>/` or inside the project):

```
<book>/book.json              single source of truth: voices, progress, artifacts, usage
<book>/source/                original file (hashed, not copied) + pages/page-NNN.txt
<book>/research/              characters.json (cast bible), chapter-NN.json (who speaks, evidence)
<book>/voices/<id>.wav        frozen reference clips - the book's voice library
<book>/chapters/NN/           chapter.txt, speakers.json, chapter.json, audio/ (render output)
<book>/usage/                 optional LLM snapshots + pricing assumptions
```

Never put the book under a git-tracked repo with the audio (WAVs are ~290 MB per hour); keep
`book.json`, research and manifests in git if you version them, ignore `audio/` and `voices/*.wav`.

## Workflows

| Task | Do this | Detail |
| --- | --- | --- |
| New book, or "where was I?" | `book.py init`, `book.py show`, `book.py resume` | [book-metadata](references/book-metadata.md) |
| Research the characters in a chapter | extract text, number the quotes, attribute speakers, write the cast | [character-research](references/character-research.md) |
| Create a voice with Voxxy/VoxCPM2 | design prompt + neutral reference text, freeze the clip, check it | [voice-design](references/voice-design.md) |
| Convert one chapter to audio | prepare -> voices -> render -> verify | [chapter-conversion](references/chapter-conversion.md) |
| Track tokens and cost (optional) | `usage.py capture --children`, `cost`, `record` | [usage-accounting](references/usage-accounting.md) |

| Script | Role |
| --- | --- |
| `book.py` | manifest CLI: `init`, `voice add/list`, `chapter set`, `progress set/show`, `artifact add/verify`, `import-render`, `resume`, `show` |
| `extract_pages.py` | PDF (text layer, else OCR) or EPUB -> `page-NNN.txt` |
| `prepare_chapter.py` | `text` (pages -> chapter.txt), `quotes` (numbered spans), `build` (-> `chapter.json`, verified lossless) |
| `render_chapter.py` | `prepare`, `voices`, `preview`, `render`, `redo`, `status`, `report`; direct VoxCPM2, resumable, ledgered |
| `verify_audio.py` | CPU Whisper spot-check, sample-scoped WER |
| `usage.py` | optional: OpenCode token capture (with child sessions), API-equivalent cost, energy scenario, `record` into `book.json` |

Fast path for a fresh chapter once the book exists (all paths relative to the book dir):

```bash
S=~/.agents/skills/ebook-to-audiobook/scripts; B=~/audiobooks/the-good-earth
python3 -B $S/book.py --dir $B init --title "The Good Earth" --author "Pearl S. Buck" --source ~/Downloads/the-good-earth.pdf
python3 -B $S/extract_pages.py ~/Downloads/the-good-earth.pdf --out $B/source/pages --first 8 --last 31
python3 -B $S/prepare_chapter.py text --pages-dir $B/source/pages --first 8 --last 31 --out $B/chapters/01/chapter.txt \
    --start-marker "CHAPTER ONE" --end-marker "CHAPTER TWO" --strip-folio --auto-join
python3 -B $S/prepare_chapter.py quotes --text $B/chapters/01/chapter.txt      # attribute every span, write speakers.json
python3 -B $S/prepare_chapter.py build --text $B/chapters/01/chapter.txt --speakers $B/chapters/01/speakers.json --book $B --chapter 1
M=$B/chapters/01/chapter.json; O=$B/chapters/01/audio
for c in prepare voices render; do python3 -B $S/render_chapter.py $c --manifest $M --output $O --book $B; done
python3 -B $S/verify_audio.py --manifest $M --root $O --phase all --max-chunks 24
```

`--book` makes every render step mirror voices, artifacts and the progress marker into `book.json`,
including after a failure, so a hung session or a crashed render is resumable from the file alone.

## Gotchas that cost real time

- **Never route a book through the public vox API or `voxxy speak`.** They cannot pin an engine. On the
  pilot day core's chain was VibeVoice -> ElevenLabs with VoxCPM2 absent; a request would have come back
  in a different voice and looked fine. `render_chapter.py` calls the VoxCPM sidecar directly and treats
  `engine != "voxcpm"` as a hard failure. `voxxy engine use` changes shared service state; do not.
- **Design once, freeze, reuse.** `(description)reference_text` is for the reference clip only. Chapter text
  is conditioned on the clip's audio and never carries a description (a description mid-text is read aloud).
  Pin a book's voices across chapters (`prepare_chapter.py build --book`), or each chapter will cast new actors.
- **Reference text is neutral and original** (15-20 words, about 8 s), never chapter content; descriptions
  stay under 20 words with no parentheses. Longer descriptions degrade the voice.
- **Health lies about sample rate** (reports 16 kHz; real output is 48 kHz). Trust WAV headers.
- **Do not retry a timed-out request blindly.** A client timeout does not stop the GPU. Confirm the engine is
  idle, then `--retry-failed`. Stale or hand-edited caches are refused; use a fresh output dir after a manifest change.
- **Quote attribution is the real work.** Count and pin every quoted span; unbalanced curly quotes, quoted
  thoughts, recalled speech and collective voices ("the vendors") all need a decision. Pilot: 117 spans, 11 speakers.
- **OCR a scanned PDF at `--psm 6`, 300 dpi**, review every page, and record each correction. Repair line-wrap
  hyphens, page-spanning paragraphs, and OCR-turned periods (`floor, Every`). Keep uncertain wording and list it.
- **Master the whole chapter once** (two-pass loudnorm, -20 LUFS / -3 dBTP). Per-chunk normalization makes
  voices pump. Expect true peak to land within about 0.1 dB of the target and say so rather than pretending.
- **ASR QA is a diagnostic, not a verdict.** CPU faster-whisper int8 keeps the GPU free; it misses
  mispronunciation, flags names (Wang/Wong) and dashes. Listen to the worst few samples.
- **TTS tokens are not LLM tokens.** 9,906 VoxCPM text tokens vs 17.3M LLM tokens for the whole project. Keep two ledgers.
- **OpenCode v2 removed `opencode export`**; read its sqlite DB read-only (`usage.py` does). A hung session
  still has a readable DB and a complete requests ledger: check `render_chapter.py status` before redoing anything.
- No credentials in any manifest or snapshot; use `op://` references if a pricing or API note needs one.
