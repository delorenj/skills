# Voice workflows

Step-by-step procedures for making and upgrading voices. Background and the numbers behind every rule:
[reference-clip-quality](reference-clip-quality.md). All of these assume the `voxxy` CLI is installed with the
clone extra:

```bash
uv tool install --editable "$HOME/code/voxxy/cli[clone]" --force
```

Standing rules for every workflow:

- Whisper, the scoring harness and any batch job run through `heavy <cmd>` (shared 32 threads).
- A voice is not a clone until a synthesis came back from engine `voxcpm` (or `vibevoice`). Check the engine.
- Never delete anything in `~/code/voxxy/voices/` by hand. Remove temp voices with `voxxy voice delete <name> --yes`,
  and only `ztmp-*` voices you created.
- No keys in files. LLM calls use `VOXXY_CLONE_*` / `VOXXY_PERSONA_*` env or `op://` refs in `~/.config/voxxy/config.toml`.

---

## A. Clone a new voice from a description

Use when the user names a person or character ("clone the dog from Family Guy", "make me a Morgan Freeman voice").

```bash
heavy voxxy voice clone "the dog from Family Guy"
```

What it does, and where you can step in:

1. Web search + LLM resolve the identity ("Brian Griffin, from Family Guy, voiced by Seth MacFarlane"). You confirm,
   edit or abort. `--yes` accepts it; a low-confidence or unresolved identity then needs `--force` / `--name`.
2. YouTube search, ranked for the target's own clean voice. Studio interviews, audiobooks and monologues first;
   live events, reaction videos, dubs, covers and "funniest moments" montages last.
3. yt-dlp downloads the first `--max-minutes` (12) into `~/.cache/voxxy/clone/<slug>/` (`source.wav`, `source.json`,
   `identity.json`). A YouTube bot wall retries with browser cookies automatically.
4. whisper + pause analysis + speaker/music gates rank clean 10-15 s windows into `markers.json`. A weak video falls
   through to the next one (`--max-videos 3`).
5. You audition and pick. Unattended (`--yes`), a fictional character or multi-speaker source needs `--pick N`
   unless the ECAPA one-voice gate passed and the video title names the character or voice actor. Look at the
   candidates first (`<workdir>/markers.json`, or the table) and pick the one whose transcript is the target alone.
6. The clip is exported (re-encoded, never stream-copied) and uploaded **with `prompt_text`**.
7. A persona is authored (`voxxy persona generate` logic), validated, saved to
   `plugins/voice-persona/personas/<slug>.md` and associated with the voice.
8. A verification line is synthesized; the engine must be `voxcpm` or the CLI prints "NOT A CLONE" and exits 2.

Useful variants:

```bash
heavy voxxy voice clone "Arnold Schwarzenegger" --yes --dry-run --no-persona   # everything but upload; inspect the clip
voxxy voice clone "Morgan Freeman" --pick 2 --name morgan2 --force              # re-run is cheap: download + transcript cached
voxxy voice clone "narrator from Arrested Development" --name narrator          # name it yourself when the slug is unclear
```

Checks after it finishes:

```bash
voxxy voice info <name>                  # prompt_text present, persona set
voxxy persona rewrite --voice <name> "The build finished in 42 seconds and all 118 tests passed."
cat ~/.cache/voxxy/clone/<slug>/clip.json   # window, transcript, video, engine, audio URL
```

Exit codes: 0 ok, 1 failure, 2 degraded (voice uploaded but persona or verification fell short: not a failure),
3 server unreachable, 5 validation / refusal to overwrite / `--pick` required.

If the clone sounds weak, do not just accept it: score it (section 5 of reference-clip-quality) against a held-out
window of the same speaker, and if it is under ~0.6 retry with another video (`--pick`, or a different query) and
keep the better one. The saved workflow `~/code/voxxy/.claude/workflows/voxxy-voice-clone.js` does exactly this loop.

Known limits: the dominant speaker wins in an interview (the host can beat the guest); pitch-shifted sources are not
detected; a cold run on a 10-minute video takes minutes (whisper at ~0.25x realtime).

## B. Add a voice from a local file

Use when the user hands you a recording (their own voice note, a podcast clip, an mp3).

```bash
heavy voxxy voice candidates talk.mp3 --top 5            # optional: see the clean windows and their transcripts first
voxxy voice add talk.mp3 --auto -n brian -d "Brian" -t cartoon,male
```

Pick the right form:

| You have                                         | Command                                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| a long recording, no idea where the clean part is | `voice add FILE --auto -n NAME`                                          |
| a window you chose by ear                         | `voice add FILE --start 12.6 --end 26.1 -n NAME` (transcript is automatic) |
| an already-clean 10-15 s clip + its exact words   | `voice add clip.wav -n NAME --prompt-text "exact words spoken"`          |
| nothing better (legacy behaviour)                 | `voice add FILE -n NAME` (first 30 s, **no transcript**: avoid)          |

Then verify and associate a persona if there is one:

```bash
voxxy voice info NAME
voxxy speak --voice NAME "A short line to hear it."     # then confirm the engine, see below
voxxy persona generate <persona-id> -c "<who it is>" --voice NAME   # optional
```

Confirm the engine without guessing:

```bash
curl -s -X POST https://vox.delo.sh/synthesize-url -H 'content-type: application/json' \
  -d '{"text":"Engine check.","voice":"NAME"}' | jq '{engine, duration_s, audio_url}'
# engine must be voxcpm or vibevoice. elevenlabs means this is NOT a clone.
```

User recording their own voice over Telegram: see "Interactive voice cloning workflow" in
[voice-and-integration-workflows](voice-and-integration-workflows.md). Collect a 10-15 s recording (a passage from
`voice_cloning_passages.md`), then run this workflow B on the saved file (`--auto` or `--start/--end`; it
transcribes the cut for you, do not skip that).

## C. Upgrade an existing voice

Use when a voice has no `prompt_text`, was cut by hand or by "first N seconds", or sounds off. One voice at a time;
D fans this out. Pre-upgrade `arnold` was 0.59, post-upgrade 0.82-0.85.

1. **Back up first.** Dated directory, one per day, shared by all voices that day:
   ```bash
   B=~/.local/share/voxxy/voice-backups/$(date +%F); mkdir -p "$B"
   voxxy voice list --json > "$B/voices.json"          # skip if it exists
   cp -n ~/code/voxxy/voices/<voice>.wav "$B/"          # files are often root-owned; reading is fine
   ```
   The first dated backup, `2026-10-28-pre-prompt-text/`, holds every clip and the voice list as of that day.
2. **Inspect the incumbent.** `voxxy voice info <voice>`; `voxxy voice list --json | jq '.[]|select(.name=="<voice>")'`.
   Note `prompt_text` (null = needs the upgrade), `duration_s`, `persona`, `elevenlabs_voice_id`.
3. **Find the best source.** In order of preference:
   a. the original recording (a download in `~/.cache/voxxy/clone/<slug>/source.wav`, or one you can fetch with
      `voxxy voice clone "<who>" --dry-run --no-persona`, or a path the user gives);
   b. the stored clip from the backup (`$B/<voice>.wav`, at most 30 s; usually only 1-3 candidate windows).
   Work from the BACKUP copy, never the live `voices/` file.
4. **Rank windows.** `heavy voxxy voice candidates <source> --top 5 --markers /tmp/<voice>.markers.json`. Read the
   transcripts: every window must be the target speaker, whole sentences, no filler edges. No window passes? The
   source is too short or too dirty; go back to step 3a with a better recording or stop (report `kept`).
5. **Build 2-3 temp voices** (never touch the live voice yet). Always name them `ztmp-<voice>-<variant>`:
   ```bash
   heavy voxxy voice add <source> --auto -n ztmp-<voice>-a --no-prompt                   # best window + transcript
   heavy voxxy voice add <source> --start S2 --end E2 -n ztmp-<voice>-b --no-prompt      # second-best window
   ```
   If the current clip is already clean and the only defect is the missing transcript, add a third variant that is
   the incumbent clip + `--prompt-text` (transcribe it with `voice candidates` on the backup copy, or `voice add --start 0`).
6. **Score** (reference must be real target speech, ideally not the clip itself; for a clip-only source use another
   recording of the same speaker, or say the score is not held-out):
   ```bash
   heavy ~/code/skillex/all-skills/vox-tts/scripts/score_voice_candidates.py \
     --reference <reference.wav> --lines 4 --json /tmp/<voice>.score.json \
     <voice> ztmp-<voice>-a ztmp-<voice>-b
   ```
   Make sure every scored line is engine voxcpm. If voxcpm is unreachable, fix that first (`voxxy daemon status`,
   stop ollama models that hold VRAM) rather than scoring elevenlabs audio.
7. **Decide** with the rules in reference-clip-quality section 5: the best candidate must beat the incumbent by more
   than 0.03 ecapa, with no worse WER and no f0 drift; at a tie, a candidate that adds a missing `prompt_text` wins.
   Otherwise keep the incumbent.
8. **Install the winner** by re-running the winning `voice add` with the real name (upsert; keeps persona and
   ElevenLabs mapping, overwrites `voices/<voice>.wav`):
   ```bash
   voxxy voice add <source> --start S --end E -n <voice> --no-prompt     # or --auto, same as the winner
   ```
   If you installed a hand-edited clip, pass `--prompt-text "<exact words>"` yourself.
9. **Clean up** the temp voices you made, and only those:
   ```bash
   voxxy voice delete ztmp-<voice>-a --yes
   voxxy voice delete ztmp-<voice>-b --yes
   voxxy voice list | grep ztmp- || echo clean
   ```
10. **Verify the installed voice**: `/synthesize-url` returns engine `voxcpm`, `voxxy voice info <voice>` shows the new
    `prompt_text` and the persona unchanged. Report before / after ecapa, wer, f0.

If anything goes wrong after step 8, restore from the backup: `voxxy voice add $B/<voice>.wav -n <voice> --no-prompt
--prompt-text "<old prompt_text from voices.json, or omit>"`.

Report format (one line per voice): `voice | incumbent ecapa | winner ecapa | delta | wer | f0 | action (installed / kept /
skipped) | note`.

## D. Batch-upgrade every voice

Use the saved Claude Code workflow; it fans out one agent per voice (4 at a time), each running workflow C, then
a summary agent merges the before / after table.

```
# in Claude Code, from ~/code/voxxy
Workflow({ name: 'voxxy-voice-upgrade' })                              // every voice from `voxxy voice list --json`
Workflow({ name: 'voxxy-voice-upgrade', args: ['brian', 'peter'] })    // only these voices
```

File: `~/code/voxxy/.claude/workflows/voxxy-voice-upgrade.js`. Notes:

- The backup (step 1 of C) is taken once by the workflow's first agent before the fan-out; every worker still
  copies its own clip defensively.
- Concurrency 4 is on purpose: each worker runs whisper and the scorer; more starves the box and the GPU engine.
- Voices with no source and no passing window end as `kept`, not failures. Read the summary table; do not trust
  an "all green".
- The workflow edits the live server's voices. It does not commit anything; commit persona or doc changes yourself.

New description-based voice with automatic retry: `Workflow({ name: 'voxxy-voice-clone', args: { query: 'the dog from
Family Guy', name: 'brian' } })` (file `voxxy-voice-clone.js`): runs `voxxy voice clone`, scores, and retries with another
video when weak.
