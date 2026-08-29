---
pipeline-status:
  - new
---
# Voice cloning reading passages

Phonetically-balanced passages for voice cloning. Each passage is designed to
take **5–10 seconds** when read aloud at a natural pace (~150 wpm), covering a
broad range of English phonemes — sibilants, fricatives, vowels, nasals, and
voiced/voiceless contrasts — so the model captures a faithful timbre sample.

The Voxxy service auto-trims to 30 s mono on ingest, so even the longest
passage below is safe. Aim for **5–15 s of clean speech** — enough for the
model to lock onto the speaker's timbre without padding silence.

## How to use these passages

1. Present **one** passage to the user (rotate or pick by index for variety).
2. Ask the user to read it aloud as a Telegram voice message.
3. Do **not** run STT on the recording — you need the raw audio file path.
4. Upload the raw audio to `POST /voices` (see `scripts/clone_voice.sh`).

## Passage index

### 1. Standard (default)

> The quick brown fox jumps over the lazy dog. She sold sea shells by the sea shore, and the wind whispered through the tall green trees.

**~8 s** · 24 words · covers /ʃ/, /θ/, /ð/, /z/, /dʒ/, all major vowels.

### 2. Conversational

> Hey, good to see you! I was just thinking about what we talked about last week. Let's grab coffee tomorrow and figure out the next steps.

**~7 s** · 26 words · natural conversational prosody, contractions, /h/ drops.

### 3. Narrative

> Once upon a time, in a quiet village nestled between rolling hills, there lived an old clockmaker who could hear the heartbeat of every machine he touched.

**~9 s** · 26 words · sustained vowels, liquid consonants /l/ /r/, narrative pacing.

### 4. Technical

> The system processes each request through a pipeline of modular components, validating inputs, transforming data, and returning results in under two hundred milliseconds.

**~9 s** · 24 words · clusters /st/, /pr/, /ks/, /tr/, /mb/, technical vocabulary.

### 5. Emotive

> I can't believe we finally made it. After all this time, through every setback and every long night, here we are. This is just the beginning.

**~8 s** · 26 words · emotional prosody, glottal stops, breath groups, /f/ /v/ contrasts.

### 6. Short (minimum viable)

> The five boxing wizards jump quickly. Voice cloning captures the unique qualities of how a person speaks.

**~5 s** · 16 words · compact but phonetically dense; good for impatient users.

## Selection guidance

| Situation                        | Pick                |
| -------------------------------- | ------------------- |
| First-time clone (default)       | Passage 1 (Standard) |
| User wants a natural feel        | Passage 2 (Conversational) |
| User reads a lot / likes stories | Passage 3 (Narrative) |
| Technical / developer user       | Passage 4 (Technical) |
| User is in a hurry               | Passage 6 (Short)    |
| Want emotional range in the clone | Passage 5 (Emotive)  |

## Quality tips

- **Quiet room** — background noise degrades the clone more than anything else.
- **Hold the phone close** — 15–20 cm from the mouth, not on speakerphone.
- **Read naturally** — don't over-enunciate; the model learns the real voice.
- **One breath per sentence** — avoid long pauses; they waste the 30 s budget.
- **If the first clone sounds off**, re-record with a different passage. Different
  passages emphasize different phoneme distributions.
