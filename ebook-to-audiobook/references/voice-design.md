# Creating a voice with Voxxy / VoxCPM2

A book voice is one **frozen reference clip** (~8 s, 48 kHz mono WAV) designed from a text description,
reviewed once, then reused as the only conditioning for every chunk that speaker says - in this chapter and every
later one. Consistency comes from the clip, not from repeating the description.

## Why direct to the sidecar

`vox-tts` documents the public API (`/synthesize`, `voxxy speak`). For a book that is the wrong door:
none of them can pin an engine, core's fallback chain decides, and on the pilot day that chain was
`vibevoice -> elevenlabs` with VoxCPM2 absent (it was healthy, just not routed). `voxxy engine use voxcpm`
mutates shared service state and still leaves ElevenLabs as a fallback. So `render_chapter.py` posts to the
engine container's `POST /v1/synthesize` through `docker exec -i vox curl ...` (override: `--engine-url`,
`--via-container`, or env `VOXCPM_ENGINE_URL`, `VOX_CORE_CONTAINER`, `VOXCPM_ENGINE_CONTAINER`; `--via-container ''`
runs curl on the host if the port is published). It never touches Voxxy's routing or voice library,
and it fails closed if a response says `engine != "voxcpm"`.

Request shape (what the script sends):

```json
{"text": "(Warm mature woman, measured literary delivery.)The morning light falls across the room...",
 "cfg": 2.0, "steps": 12}                                   // design: description prefix, no reference
{"text": "It was Wang Lung's marriage day.", "cfg": 2.0, "steps": 12, "reference_audio_b64": "<frozen clip>"}  // chapter chunk
```

Response: `{engine, wav_b64, bytes, sample_rate, duration_s}`. Validate the WAV itself - the engine's `/healthz`
advertises 16 kHz while real output is 48 kHz.

## Writing the design prompt

`(description)reference_text`. The parenthetical is consumed by the model and not spoken.

- **description**: under 20 words, no parentheses, non-contradictory. Order that worked:
  *age/sex, register, manner, delivery, accent*. Describe qualities, not people ("like Morgan Freeman" is
  unreliable and may be filtered). Stack at most 3-4 traits.
- **reference_text**: 15-20 words (about 8 seconds), neutral, original, **never chapter content** (it would leak the
  scene into every voice and the clip would be heard by ASR as story text). The pilot used one sentence for all
  eleven voices: *"The morning light falls across the room, and a gentle breeze moves the curtains beside the open
  window."* A shared sentence also makes the voices directly comparable, which is how you hear that they differ.
- **cfg 2.0, steps 12** worked for design and chapter text. cfg 2-3 is the useful range; raise it if the voice drifts
  from the description; steps 4-6 are fine for quick auditions. The pilot sent only `text`, `cfg`, `steps` (no `normalize`),
  so spell out digits and abbreviations in the source text if they matter.
- Clips came out 5.6-10.1 s. The VoxCPM sidecar caps reference audio at 30 s (`/healthz` -> `max_ref_seconds`); aim for about 8.

### Pilot casting (descriptions that worked)

| id | description |
| --- | --- |
| narrator | Warm mature woman, measured literary delivery in clear American English. |
| wang_lung | Adult male, earnest light baritone; rural dignity with nervous hesitation. |
| father | Elderly male, dry weathered voice, grumbling but clear. |
| uncle | Middle-aged male, jovial and sly, easy conversational warmth. |
| o_lan | Twenty-year-old woman, grounded plain restrained middle-low register; neither loud nor soft, not ill-tempered. |
| old_mistress | Elderly woman, thin imperious voice, deliberate cultured delivery. |
| gatekeeper | Adult male, booming rough baritone, self-important and forceful. |
| barber | Adult male, amused nimble delivery in a clear middle register. |
| waiter | Adolescent boy, brisk impatient delivery with a light tenor. |
| beggar | Adult male, weary thin voice, pleading without exaggeration. |
| vendor | Adult male, brisk street call; neutral collective voice for unnamed vendors. |

Lessons from them: let the text's own wording drive the prompt (O-lan's "not loud, not soft, plain" beat a
generic "timid slave" and avoided portraying her as foolish); one narrator voice must be distinct from every character
(different sex or register); a collective gets one neutral voice; keep acted extras (coughing, whining) out of the
prompt - they become constant tics across hundreds of lines.

## Design, check, freeze

1. Put the voices in `speakers.json`; `prepare_chapter.py build` validates length rules and writes `chapter.json`.
2. `render_chapter.py prepare` (exact token counts, plan fingerprint) then `render_chapter.py voices`. Each voice
   is one synth call (~4 s). Results land in `audio/refs/<id>.wav` with a request receipt; they are never regenerated
   once they exist. Do not rerun `voices` hoping for a "better take" - change the description and use a fresh output
   directory, or `book.py voice add --replace` a hand-picked clip.
3. **Audition**: `render_chapter.py preview` concatenates every reference (with pauses) into
   `audio/voice-preview.wav/.mp3`. Listen to all voices back to back. The pilot's `voice-preview.mp3` was 85 s for 11 voices. Confirm: distinct from one another,
   no spoken design instructions, right sex/age, no artifacts.
4. **ASR check**: `verify_audio.py --phase refs` compares each clip's transcript to its reference_text
   (pilot: 197 of 198 words matched, no spoken instructions). A failing clip usually means the description was
   read aloud (misplaced parenthesis) or the voice is too exotic.
5. `render_chapter.py ... --book $B` (or `book.py import-render`) copies each clip to `<book>/voices/<id>.wav`,
   hashes it, and records `description`, `reference_text`, `mode: designed` in `book.json`.

## Reusing and choosing voices later

- **Next chapter, same cast**: `prepare_chapter.py build --book $B --chapter N` pins every registered speaker to
  its library clip; `render_chapter.py prepare` hashes the clip into the plan, `voices` only designs *new* speakers,
  and a changed clip invalidates the plan (fresh output directory).
- **Selected voice** (an existing Voxxy profile): `voxxy voice list`, then
  `book.py voice add ID --mode selected --voxxy-slug SLUG --reference-audio PATH`. The direct VoxCPM path needs the
  profile's reference *clip*, not its slug: use the original upload or copy it out of the core container
  (`docker cp vox:/data/voices/<slug>.wav .`, the location vox-tts uses for `rick`). Check the `engine` field on any
  render that goes through the public API: `vibevoice`/`voxcpm` is the voice, `elevenlabs` is a stranger.
- **Cloned voice**: only when the user supplies a recording and asks (vox-tts "Interactive voice cloning"). Do not run
  STT on it; it is a reference, not text. Reference budget is ~10 s of clean speech for VibeVoice, 30 s for VoxCPM.
  Register with `book.py voice add ID --mode cloned --reference-audio WAV`.
- **Mood without a new clone**: a description prefix can shift prosody on top of a reference (vox-tts voice_design.md),
  but chapter chunks here deliberately carry no description; keep it that way for audiobook consistency.
- Do not register book voices into the shared Voxxy library as a side effect; the library is shared state. If the user
  wants them there, add them explicitly with `voxxy voice add`, then record the slug in `book.json`.

## Failure modes seen or expected

| Symptom | Cause | Fix |
| --- | --- | --- |
| Response `engine` is not `voxcpm` | public route or engine down | Use the sidecar directly; start `voxxy-engine-voxcpm` with `--profile voxcpm` |
| "Prior failed/unfinished request" | timeout, container restart | Confirm idle GPU, then `--retry-failed` |
| Clip transcript includes the description | parenthesis lost or description too long | Shorten (<20 words), remove punctuation oddities |
| Two voices sound alike | prompts differ only in adjectives | Change sex/age/register, not mood |
| Voice differs between chapters | voice redesigned per chapter | Pin from `book.json` (`build --book`) |
