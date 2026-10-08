# Character research for a chapter

Goal: for every voice that will speak in this chapter, a **sourced fact sheet** (who they are, what the
text says about their age, sex, manner and voice) kept strictly apart from **creative casting** (pitch,
register, pacing - choices, not facts), plus a **reviewed speaker for every quoted span**. Output feeds
`voice-design.md` (the description) and `prepare_chapter.py build` (`speakers.json`).

## Procedure

1. **Primary text first.** Get the chapter text (`extract_pages.py`, `prepare_chapter.py text`). The book itself is the
   authority on who speaks and how they sound. Read it end to end; study guides are for corroboration.
2. **Number every quoted span.** `prepare_chapter.py quotes --text chapter.txt` prints each span with its
   paragraph and 80 characters of context either side. This is your attribution worksheet. A mismatch
   between open and close quotes aborts here, which is where a split quote or an OCR'd stray quote gets caught.
3. **Attribute each span** by context, not by the order speakers first appear. Decide the edge cases explicitly:
   - quoted thought and imagined speech -> the thinker (Wang Lung's inner replies were his voice);
   - recalled speech ("my uncle once said...") -> the person recalled;
   - unattributed saying or proverb -> narrator (do not invent a townsperson);
   - unnamed group ("the vendors cry out") -> one neutral voice for the collective, labeled as a casting choice;
   - a character present but without a line (Ching, the cousin) -> **no voice generated**; note it in research.
4. **Extract qualitative voice data per speaker** from the text: age (exact only if stated, else a band),
   sex as written, social position, how the narration describes their voice or manner ("not loud, not soft,
   plain", "booming", "thin, imperious", "whines"), speech habits, and the emotional register they hold in this chapter.
   Cite page numbers. Nothing here may be invented; unknowns stay `"not established"`.
5. **Corroborate with 2-3 secondary sources** (chapter summaries, character guides) for roles and who attends what
   scene. Use `web-search search|fetch` (built-in WebSearch/WebFetch return 400 here). Expect 403s (SparkNotes) and
   Brave rate limits; fall back to LitCharts / GradeSaver / BookRags and keep each source's `used_for`. Never let a
   secondary source override the text. Guides disagreed on who spoke at the dinner; the PDF settled it.
6. **Write the creative direction** per voice (see voice-design.md). Guardrails: describe qualities, never impersonate
   a real performer or a named actor; no ethnic caricature or invented accents; another character's
   judgement of someone (Old Mistress calls O-lan slow) is not a reason to perform them as foolish.
7. **Check rights** and record them in `book.json` `source.rights`.
8. **Save**: `research/characters.json` (book-level bible, append per chapter) and `research/chapter-NN.json`.
   Then `book.py --dir $B chapter set N --status researched --text chapters/NN/chapter.txt` (the marker that
   `book.py resume` reads). A voice you want before writing `speakers.json` can be designed and frozen on its own
   with `design_voice.py` (voice-design.md, path A).

## `research/characters.json` (cast bible, cumulative)

```json
{
  "book": "The Good Earth", "author": "Pearl S. Buck",
  "casting_policy": "Facts are sourced; pitch, accent, pacing and timbre are creative choices, not facts. Clear English, no caricature, no impersonation of real performers.",
  "characters": {
    "o_lan": {
      "display_name": "O-lan",
      "gender_in_text": "female", "age": 20,
      "age_evidence": "Old Mistress states she is twenty (PDF p.24)",
      "facts": ["Former kitchen slave sold into the Hwang household at ten", "Capable cook, guarded, reserved",
                "Narration: voice not loud, not soft, plain, not ill-tempered (p.25)"],
      "pdf_pages": [24, 25, 29],
      "creative_direction": "Grounded plain mid-low voice, restrained and matter-of-fact; not foolish",
      "voice_id": "o_lan", "lines_in_chapters": {"1": 4}
    },
    "ching": {"gender_in_text": "male", "facts": ["Quiet neighbor, dinner guest"], "casting": "No voice generated: no attributed lines"}
  }
}
```

`gender_in_text` / `age` take the value `"not established"` rather than a guess. `voice_id` must be a safe id
(letters, digits, `_`, `-`) because it names files.

## `research/chapter-NN.json`

```json
{
  "chapter": 1, "primary_source": "the-good-earth.pdf, PDF pages 8-31 (printed 3-26)",
  "sources": [{"url": "https://www.litcharts.com/lit/the-good-earth/chapter-1", "kind": "chapter study guide",
               "used_for": "scene order, speaking roles"}],
  "speakers": {"wang_lung": {"quotes": 50}, "father": {"quotes": 17}, "narrator": {"quotes": 1}},
  "uncertainties": [{"pdf_pages": [15], "text": "It is better to live alone...", "decision": "Unattributed saying stays with the narrator"}],
  "rights": {"first_publication_year": 1931, "us_public_domain_date": "2027-01-01"}
}
```

## `chapters/NN/speakers.json` (input to `prepare_chapter.py build`)

```json
{
  "title": "The Good Earth", "chapter": 1,
  "settings": {"cfg": 2.0, "steps": 12},
  "default_speaker": "narrator",
  "voices": {
    "narrator":  {"character": "Narrator", "description": "Warm mature woman, measured literary delivery in clear American English.",
                  "reference_text": "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window."},
    "wang_lung": {"character": "Wang Lung", "description": "Adult male, earnest light baritone; rural dignity with nervous hesitation.",
                  "reference_text": "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window."}
  },
  "quotes": [["wang_lung", "It is spring and I do not need this,"], ["father", "How is it that there is not water yet to heat my lungs?"]],
  "source": {"pdf": "the-good-earth.pdf", "pdf_pages": [8, 31], "uncertainties": []},
  "casting": {"designation": "creative", "choices": {"wang_lung": "Adult light baritone, earnest dignity"}}
}
```

- `quotes` has **exactly one entry per quoted span, in text order**. Each entry is `"speaker"`, `["speaker", "exact
  quote text"]`, or `{"speaker","text"}`. Include the text: it **pins** the attribution, so if OCR cleanup later
  changes a quote, `build` refuses ("Quote 50 changed...") instead of silently misassigning every span after it.
- Voices already registered in `book.json` (from an earlier chapter or `design_voice.py freeze`) are pinned
  automatically with `--book` when the speaker is listed under `voices` (an empty `{}` or just `"character"` is
  enough: no `description`/`reference_text` needed). New speakers need both. `build --book` also records the
  chapter's text and manifest in `book.json` and moves the marker to `prepared`; an optional top-level
  `"chapter_title"` is stored as the chapter's title.
- `unused_voices` in the build output lists voices with no segments; delete them so no design call is wasted.
- `build` also proves the text survived: every paragraph, and the whole chapter, must reconstruct exactly from the
  segments once dialogue delimiters and whitespace are removed. Keep `source.uncertainties` for every place you
  retained doubtful wording (dash lengths, "some thing", a comma that may be a period) so it is auditable.

## Turning text into clean paragraphs (scanned books)

`extract_pages.py` writes `page-NNN.txt` (1-based PDF page numbers, not printed folios). Then
`prepare_chapter.py text` assembles a chapter: `--start-marker/--end-marker` cut at headings (the end marker is
searched on every page, so an overshooting `--last` is harmless; `end_marker_found` reports the page, and a missing
marker warns),
`--strip-folio` drops the page-number line, `--join-previous 10,12` (or `--auto-join`) rejoins paragraphs split by a
page break, soft-hyphen line wraps are repaired, and `--corrections corrections.json` applies reviewed fixes
`[{"page": 9, "before": "carthen", "after": "earthen"}]`. A correction that no longer matches aborts the build
(a re-OCR changed the page), which is what you want. Pilot: 85 OCR/wrap repairs and 15 page-continuations across
24 pages, plus one restored paragraph break. Re-OCR doubtful pages at 300 dpi `--psm 6` and diff against the first pass.
If you cannot view page images, say so in `source.uncertainties` and leave doubtful wording as scanned.
