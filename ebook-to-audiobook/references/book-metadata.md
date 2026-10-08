# Book metadata (`book.json`)

One JSON file per book is the durable memory: which voices exist, how far the build got, and what
was produced. Everything else (audio, caches) is derivable or regenerable; `book.json` is not.
`book.py` owns it: atomic writes, an exclusive `flock` (`.book.lock`) around every
read-modify-write, paths stored relative to the book directory so the folder can move.

## Commands

```bash
S=~/.agents/skills/ebook-to-audiobook/scripts; B=~/audiobooks/<slug>      # --dir defaults to cwd
python3 -B $S/book.py --dir $B init --title T [--author A] [--slug S] [--source FILE] [--language en]
python3 -B $S/book.py --dir $B voice add ID --mode designed|selected|cloned --character NAME \
        [--description D --reference-text R] [--reference-audio WAV] [--voxxy-slug S] [--chapter N] [--replace]
python3 -B $S/book.py --dir $B voice list
python3 -B $S/book.py --dir $B chapter set N [--title T] [--status STAGE] [--manifest P] [--output P] [--text P]
python3 -B $S/book.py --dir $B progress set --chapter N --stage STAGE [--chunk-id 000123 --chunks-done 123 --chunks-total 296 --char-offset 41230 --note ...]
python3 -B $S/book.py --dir $B progress show
python3 -B $S/book.py --dir $B artifact add --kind K --path P [--chapter N] [--status partial|complete|stale] [--note ...]
python3 -B $S/book.py --dir $B artifact verify [--no-mark]     # exit 2 + list when something drifted
python3 -B $S/book.py --dir $B import-render --chapter N --output chapters/NN/audio
python3 -B $S/book.py --dir $B resume                          # the next concrete action
python3 -B $S/book.py --dir $B show [--json]
```

You rarely call `voice add`, `progress set`, `artifact add` or `import-render` by hand:
`render_chapter.py ... --book $B` runs `import-render` after every `prepare`, `voices` and `render`
(also after a failure), registering designed voices, the chunk cache, the final audio and the
progress marker. Call them directly for work done outside the scripts: a voice you selected from the
Voxxy library, a hand-edited reference clip, a chapter produced elsewhere.

## Schema (`"schema": "ebook-to-audiobook/book/1"`)

```json
{
  "schema": "ebook-to-audiobook/book/1",
  "slug": "the-good-earth", "title": "The Good Earth", "author": "Pearl S. Buck", "language": "en",
  "created_utc": "...", "updated_utc": "...",
  "source": {"path": "/abs/or/relative/the-good-earth.pdf", "kind": "pdf", "sha256": "...", "bytes": 59352153,
             "rights": {"first_publication_year": 1931, "us_public_domain_date": "2027-01-01",
                        "note": "Personal listening from a supplied copy"}},
  "engine": {"name": "voxcpm2", "settings": {"cfg": 2.0, "steps": 12}},

  "voices": {
    "o_lan": {
      "character": "O-lan", "mode": "designed", "engine": "voxcpm2",
      "description": "Twenty-year-old woman, grounded plain restrained middle-low register; neither loud nor soft.",
      "reference_text": "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window.",
      "reference_audio": {"path": "voices/o_lan.wav", "sha256": "...", "duration_seconds": 8.12, "sample_rate": 48000},
      "voxxy_slug": null, "chapters": [1], "notes": null, "added_utc": "...", "updated_utc": "..."
    }
  },

  "chapters": {
    "1": {"title": "Chapter One", "status": "assembled", "text": "chapters/01/chapter.txt",
          "manifest": "chapters/01/chapter.json", "output": "chapters/01/audio", "updated_utc": "..."}
  },

  "progress": {
    "furthest": {"chapter": 1, "stage": "assembled", "chunk_id": "000296", "chunks_done": 296,
                 "chunks_total": 296, "char_offset": 40266, "note": null, "updated_utc": "..."},
    "current":  {"...": "last marker written, may be behind furthest when you redo an earlier chapter"}
  },

  "artifacts": [
    {"id": "a0003", "kind": "chapter-mp3", "chapter": 1, "path": "chapters/01/audio/chapter.mp3",
     "status": "complete", "bytes": 48322220, "sha256": "...", "note": null,
     "created_utc": "...", "updated_utc": "..."}
  ],

  "usage": [
    {"label": "build", "chapter": 1, "recorded_utc": "...", "snapshot": "usage/final.json",
     "totals": {"input_tokens": 13552862, "output_tokens": 194612, "...": "..."},
     "api_equivalent_usd": 29.40, "actual_llm_charge_usd": null}
  ]
}
```

### Voices

- `mode`: `designed` (VoxCPM2 voice design -> frozen clip; needs `description` + `reference_text`),
  `selected` (an existing Voxxy profile via `voxxy_slug`, or a supplied clip), `cloned` (a clip of a
  real voice; needs `reference_audio`; only on the user's request, see vox-tts).
- A voice is **book-level**, not chapter-level. `chapters` lists where it has spoken. The frozen clip in
  `voices/` is the canonical sound; `prepare_chapter.py build --book` pins matching speakers to it so
  `render_chapter.py` skips design and conditions chunks on that exact file.
- `voice add` on an existing id is refused without `--replace`. Replacing a voice mid-book changes the sound of
  every later chapter, so do it deliberately and rerender nothing silently.
- Reference audio from outside the book is copied to `voices/<id>.<ext>` and hashed; `description`
  may not contain parentheses (the renderer wraps them).

### Progress marker

`furthest` is a high-water mark ordered by (chapter, stage, chunks_done, char_offset), so redoing an old
chapter never drags it backwards. Stages, in order: `new, researched, prepared, voices, rendering,
assembled, qa, done`. `chunk_id` is the last chunk with a validated WAV; `char_offset` is cumulative
characters of chunk text consumed (position within the chunked chapter text, approximate by one space
per chunk). The chapter's own `status` only ever advances.

`book.py resume` turns the marker into the next action. The chunk cache, not the marker, is the real
resume state: `render_chapter.py status` counts valid chunks and names the next one.

### Artifacts

| kind | meaning | status rule |
| --- | --- | --- |
| `chunk-cache` | `audio/chunks/` directory (count recorded, no hash) | `partial` until every planned chunk exists |
| `chapter-mp3`, `chapter-wav` | mastered final audio | `complete` once assembled |
| `requests-ledger`, `metrics`, `assembly` | `requests.jsonl`, `metrics.json`, `assembly.json` | `complete` |
| `asr-qa` | `qa-*.json` | `complete` |
| anything else | free-form `--kind` | caller decides |

Artifacts are keyed by path (re-adding updates in place, keeping the id). `artifact verify` recomputes hashes
and marks missing/changed files `stale` with a note; exit code 2 means drift. Run it before trusting a
`complete` artifact after moving the book between machines.

### Do not store here

Secrets, API keys, tokens. Reference them as `op://...` in notes if needed. Large payloads (transcripts,
per-request ledgers) live in the audio directory; `book.json` points at them.
