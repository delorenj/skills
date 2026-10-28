# Reference clip quality

How to make a voxcpm voice sound like its source, and how to prove it. Measured 2026-10-28 on `arnold`.
The CLI (`voxxy voice clone`, `voice add --auto`, `voice candidates`) automates everything in the first half;
the second half is the A/B procedure for judging any change.

## 1. Why `prompt_text` is the lever

A voice row has a reference WAV and an optional `prompt_text`. With only the WAV, voxcpm does plain voice cloning.
With `prompt_text` set to the **exact words spoken in the WAV**, voxcpm treats the clip as the beginning of the
utterance and continues it ("Ultimate Cloning" / continuation mode). Same clip, same engine:

| Reference clip for `arnold`                                         | ecapa vs source |
| ------------------------------------------------------------------- | --------------- |
| old upload: first 15 s, starts on a cut-off word, no transcript     | 0.59            |
| clean sentence-boundary cut, no transcript                          | 0.72            |
| same cut, **with** `prompt_text` (exact transcript)                 | 0.82-0.85       |

Clip length: 12-15 s scored the same as 22 s at lower latency. Target 10-15 s. VibeVoice ignores `prompt_text` and
caps its reference at 10 s (`VOX_REF_AUDIO_MAX_SECONDS`), so a 10-15 s clip is still right for both engines.

Rules that follow:

- The transcript must match the clip **word for word**. A wrong transcript is worse than none. Verify by
  re-transcribing the cut clip itself, not the whole file (whole-file whisper often returns lowercase text with no
  punctuation and mis-timed words at the edges).
- Setting `prompt_text` and changing the audio are one operation. Re-upload both together.
- `POST /voices` upserts and overwrites `voices/<name>.wav`, and keeps the voice's persona and ElevenLabs mapping.

## 2. What makes a good clip

1. **Speech seconds, not wall-clock.** A 15 s window with 4 s of silence is an 11 s clip. Count words per second:
   real speech is >= 1.2 words/s. Laughter, gunshots and crowd noise are loud but have almost no words; the CLI
   rejects windows under 1.2 words/s.
2. **Cut on whole sentences at pauses.** Find energy pauses (frames 30 dB under the p90 speech level, >= 80 ms; relax
   in steps for noisy sources). Start right after a pause and end right before one, on a sentence end where possible.
   No cut-off word fragment at either edge.
3. **No filler or fragment edges.** Never start or end on uh / um / er, on a low-probability word (< 0.5), or on a
   half word. Fillers inside the clip are tolerated but count against it.
4. **One speaker.** Interviews, dialogue and compilations are the usual failure: the host or another character leaks
   in. The CLI gates in two layers:
   - MFCC with cepstral mean normalization on ~2 s segments, Ward clustering, the cluster with the most speech time
     is the dominant speaker; windows with other clusters are rejected. Average linkage collapses to one cluster on
     real audio; use Ward. Best-effort: it finds the most talkative voice and cannot always tell characters apart.
   - ECAPA one-voice check (`voxxy/speakergate.py`): coherence of the 2 s sub-windows inside a candidate (monologue
     0.49-0.55, dialogue <= 0.45) and dominance (closeness to the source's main voice). Rejects below 0.45 / 0.30.
     Off switch: `VOXXY_VOICE_GATE=off`.
5. **No music, no background, no clipping.** The gap floor between words (SNR) and tonality of the gaps (music) are
   scored. Live hall events (commencement, keynote, stage) fail on echo and audience noise (SNR ~18 dB); studio
   interviews, audiobooks and monologues pass (35-55 dB).
6. **Natural pitch.** Compilations and "funniest moments" montages are often pitch-shifted or spliced from many
   scenes. A clone of a shifted source scores well against that source and is still wrong. Prefer one uncut scene or
   monologue. The CLI does not detect pitch shift yet: compare f0 of the reference with the character's real voice.

## 3. The cut

Always **re-encode**. Never stream-copy (`-c copy`): it snaps to packet boundaries and truncates the clip.

```bash
ffmpeg -y -ss <start> -t <dur> -i source.wav \
  -af "highpass=f=55,afade=t=in:d=0.02,afade=t=out:st=<dur-0.03>:d=0.03,loudnorm=I=-20:TP=-1.5:LRA=11" \
  -ac 1 -ar 24000 -c:a pcm_s16le clip.wav
```

Mono, 24 kHz, PCM 16. The 20 ms / 30 ms fades kill clicks at the cut; loudnorm to -20 LUFS makes voices comparable.

Transcription, if doing it by hand (the CLI does this for you):

- Model: `deepdml/faster-whisper-large-v3-turbo-ct2` (already in `~/.cache/huggingface`).
- **Pre-decode with ffmpeg** to 16 kHz mono float32 numpy and pass the array. faster-whisper's own PyAV decode breaks
  here with `unexpected keyword argument metadata_errors`.
- Run long audio through `heavy`; whisper on CPU is ~0.25x realtime.
- Transcribe the **exported clip** again and use that text as `prompt_text`. Compare it with the whole-file words
  for the same span; if they disagree, trust the clip pass and eyeball it. Whisper adds a trailing period to any
  clip, so that period is weak evidence of a sentence end.

## 4. Traps that make a clone silently wrong

- **ElevenLabs fallback.** If the GPU engines are down or the call fails, vox answers `200` in ElevenLabs' stock
  voice, which ignores reference audio. `/healthz` readiness is not proof. Every verification must check the
  `X-Vox-Engine` header (or the `engine` field of `/synthesize-url`) is `voxcpm` (or `vibevoice`). The CLI's final
  step and the scoring harness both do this and print "NOT A CLONE" / exclude the line.
- **ollama VRAM.** An ollama model resident on the same 3090 OOMs voxcpm (it holds ~5 GB, vibevoice ~7.5 GB, neither
  evictable). Symptom: engine `OOM` errors or sudden fallback to elevenlabs. Fix: `ollama stop <model>`, set
  `OLLAMA_KEEP_ALIVE=0`, check `nvidia-smi`, then `voxxy daemon status`.
- **Oversized reference** is the other OOM cause; keep clips <= 15 s.
- **Wrong speaker** in an interview: the dominant speaker is whoever talks most, which may be the host. Audition the
  clip (or run `voice candidates` and read the transcripts) before trusting `--yes`.
- **Truncated yt-dlp download** (a video returning 160 of 720 s) and the YouTube "confirm you're not a bot" wall:
  the CLI warns under 60% and retries with browser cookies (`VOXXY_YTDLP_COOKIES_FROM_BROWSER`).

## 5. A/B evaluation procedure

Use whenever you change a voice's reference clip, compare two candidate cuts, or want to know whether a clone is good.
Harness: `scripts/score_voice_candidates.py` (a PEP 723 uv script; loads speechbrain ECAPA, resemblyzer and whisper).

```bash
# candidates are temp voices named ztmp-<voice>-<variant>; the current voice goes in the same run
heavy ~/code/skillex/all-skills/vox-tts/scripts/score_voice_candidates.py \
  --reference /path/to/full-source-recording.wav --lines 4 --json /tmp/score.json \
  arnold ztmp-arnold-a ztmp-arnold-b
```

- `--reference` is a recording of the **real target speaker**, ideally the full source, not the clip that was cut
  from it. Scoring a voice against its own reference clip rewards memorization.
- The harness synthesizes the same lines through every voice (`POST /synthesize`) and **rejects any line served by
  elevenlabs**, retrying and excluding it. If a voice has zero scoreable lines it is not a clone; do not compare it.
- Columns: `ecapa` (primary; speechbrain ECAPA cosine), `reSim` (resemblyzer, second opinion, less discriminative),
  `wer` (faster-whisper word error rate vs the requested text; garbling check), `f0` (median pitch).
- `--lines N` max 8; 4 is the default compromise, 6 when the decision is close.

### Decision rules

1. **Noise floor 0.03 ecapa.** A candidate must beat the incumbent by more than 0.03 to count. Within 0.03, keep the
   incumbent (no churn), unless the candidate fixes something else (e.g. it adds a missing `prompt_text` at a tie).
2. **WER guard.** If the candidate's `wer` is clearly worse (say more than 0.10 above the incumbent) it is garbling;
   reject it even with a higher ecapa.
3. **f0 drift.** Compare each voice's f0 with the reference's f0. A winner whose f0 is far from the reference
   (roughly > 15% off) is a pitch-shifted source or a bad clone; investigate before installing.
4. **Engine purity.** Only lines from voxcpm / vibevoice count. A voice with elevenlabs lines is unscored, not weak.
5. **Held-out scoring.** Score against a window of the source the clip did **not** come from, and say so. A clip
   scored on its own audio inflates the number. Also compute what the original clip itself scores against the same
   reference: that is the ceiling for any clone of it.
6. **Different sources are not comparable.** ecapa against source X and against source Y measure different things
   (a shifted source gives a high score for a shifted clone). Only compare candidates scored against one reference.
7. Install the winner (re-upload with its `prompt_text`) only if rules 1-4 pass; otherwise keep the current voice.

Differences under ~0.03 over 4-6 lines are noise. For a bar to aim for: clones of a clean clip land around
0.7-0.85 against a clean held-out reference of the same speaker; Brian Griffin (a natural-pitch single-scene clone)
reached 0.55-0.58, about 72% of the 0.78 the original clip itself scored, which is the practical ceiling.

### Arnold before / after (2026-10-28)

| Variant                                 | Clip                                           | prompt_text | ecapa vs source |
| --------------------------------------- | ---------------------------------------------- | ----------- | --------------- |
| old upload (the incumbent `arnold`)     | first 15 s, begins on a cut-off word           | no          | 0.59            |
| clean cut                               | whole sentences, pause to pause (10.24-22.50 s)| no          | 0.72            |
| clean cut + transcript                  | same cut                                       | exact transcript | 0.82-0.85  |
| 12-15 s cut vs 22 s cut                 | same sentences, shorter                        | exact transcript | same score, lower latency |

All lines served by voxcpm. The backup of every pre-change clip and the voice list is at
`~/.local/share/voxxy/voice-backups/2026-10-28-pre-prompt-text/`.
