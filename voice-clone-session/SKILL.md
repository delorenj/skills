---
name: voice-clone-session
description: "Clone a voice on vox — passage, coaching, training, proof."
---

# Voice clone session

The full workflow for turning a person reading a passage into a working vox
voice profile, plus the failure modes that only show up at the end if you skip
verification. Service-level API detail lives in the `vox-tts` skill — read it
for endpoints; this skill is the *session* layer on top of it.

## The shape of a successful session

1. **Author the passage.** Generic passages exist in vox-tts, but a custom one
   reads better and performs better. Rules that hold:
   - **The model sees the first 10 seconds. Nothing else.** Two caps stack:
     `POST /voices` stores the first 30s (`VOX_REF_AUDIO_MAX_SECONDS=30` in
     `compose.yml`), but the vibevoice container sets the same variable to
     **10** (`compose.engines.yml:69`) and reloads the clip with
     `duration=10.0` at synthesis (`engines/vibevoice/engine/synth.py:183,208`);
     its `/healthz` reports `"max_ref_seconds": 10.0`. Budget the passage at
     **~25–30 words** and put the best, most neutral speech **first**.
     A 30-second read is not a richer reference — it is a 10-second reference
     with 20 seconds of decoration you will never hear.
   - **Silence is spent budget.** Long pauses inside the first 10s are dead
     weight. So is a mouth sound effect or a shouted line in the opening
     seconds — they set the timbre the model copies.
   - Cover phoneme families on purpose: heavy /l/ and /r/ words, sibilants,
     a /dʒ/ word ("Hoagie"), /ð/ ("this", "the"), varied vowels. Sound effects
     (VRRRM, WHOOSH) are gold — they force dynamic range the model latches onto.
   - Write for the reader: first-person, their real people and in-jokes, short
     sentences, a deadpan button at the end. An 11-year-old should be able to
     ham it up on the first read.
2. **Coach the recording, one breath per sentence.** Quiet room, phone 15–20cm
   from the mouth (not speakerphone), read naturally — don't over-enunciate.
   Big energy on the sound-effect beats is a feature, not a problem.
3. **Interrupted or broken take → discard and re-read from the top.** Never
   stitch or accept a partial; timbre consistency across the clip matters more
   than saving a take.
4. **Recover the raw audio from the platform cache, not the STT path.** STT
   metadata shows a `/tmp/hermes-local-stt-*/audio_*.wav` source path — those
   temp files are deleted as soon as transcription returns. The real bytes are
   in the Hermes profile's media cache (observed: `cache/audio/<id>.ogg` under
   the active profile dir). If that cache is cleaned before you grab it, the
   take is gone — re-record.
5. **Train:** `POST /voices` multipart with `name`, `display_name`, `audio=@file`.
6. **Verify in two steps, never one.** (a) `GET /voices` shows the profile.
   (b) Synthesize a short test line and **check the `engine` field in the
   response**, not just that audio came back.
   - `vibevoice` — correct, this engine holds the clone reference.
   - `voxcpm` — degraded but still your voice. It does receive the reference
     (`app/voices.py:46-48` falls back to `wav_path`), just at 30s and without
     vibevoice's conditioning. Expect recognisable-but-off.
   - `elevenlabs` — **not your voice at all.** vox answers `200` in a
     stranger's voice, logs `vox: voice clone BYPASSED`, and delivers it
     anyway. This is the one that makes the requester say "that is not the
     voice." Say so plainly rather than shipping it.
7. **A human listens before you declare victory.** Timbre quality is not
   machine-checkable. Send the test clip URL to the requester and wait for
   their ears.

## Failure modes, mapped

| Symptom | Cause | Fix |
|---|---|---|
| "That is not the voice at all" | Both GPU engines down → silent ElevenLabs substitution (`200 OK`, `clone BYPASSED` in the log) | Bring the engines up; never ship a take whose `engine` is `elevenlabs` |
| "Close, but off" | Served by voxcpm instead of vibevoice | Bring `voxxy-engine-vibevoice` up; `preferred` routing handles ordering — confirm `engine: vibevoice` |
| Clone ignores the best part of the read | It was after the 10s mark | Re-cut the reference so the best 8–10s is at the **start**; re-upload under the same `name` |
| "The STT audio path is gone" | Temp files are ephemeral | Pull from the profile media cache (step 4) |
| Clone sounds off | Bad reference (noise, flat read, or the wrong 10s) | Re-record quieter, livelier, or tighter to the **10s** budget; re-upload with the same `name` to overwrite |

## Comparing two candidate references: never on one sample

If you are choosing between two cuts of the same recording, A/B them by
registering each as a throwaway voice (`dumplytesta`, `dumplytestd`), synthesizing
the **same** lines with each, and measuring the output against the *full* original
recording — median f0 error, f0 histogram overlap, and voiced-frame ratio.
Delete the throwaways afterwards.

**Use at least six samples per candidate.** Run-to-run synthesis variance is
±3.6–3.9% on median f0, which is *larger* than the difference between two
reference cuts from one recording. Measured 2026-09-20 on Ava's clip: a
single-sample comparison ranked the candidates in exactly the **opposite** order
to the six-sample average. One sample will confidently tell you the wrong thing.

**Acoustic window scoring does not predict clone quality.** A candidate that won
on every acoustic measure (highest speech ratio, shortest internal silence,
fewest loud frames, calmest f0 spread) produced the worst clone by a wide margin
— 37.8% f0 error against 4.4% for the winner. Pick windows by *content*
(continuous narration, neutral register, no non-speech) and then confirm by
synthesis. Do not trust a silence-and-loudness score on its own.

And know when to stop: if two cuts of the same take measure within noise of each
other, the recording is the ceiling, not the cut. Ask for 15 clean seconds
instead of hunting for a better window.

## Household notes

- Voice profiles are stored on the service with a `name` slug that becomes the
  API/MCP voice parameter. Agree the slug before training; overwriting reuses
  the same `name`.
- First synthesis after an engine container restarts is slow (model warmup);
  don't read slowness as failure.
- **VibeVoice output carries an embedded watermark** (audible + imperceptible)
  baked into the model weights; it cannot be disabled. Call it out whenever the
  voice is going into something published.
