# Voice And Integration Workflows

Load only for the matching task. Historical versions and incidents are evidence
to verify against the current installation, not universal current facts.

## Two modes: design vs cloning

The service supports two distinct approaches to voice selection. Pick the right one for the task.

### Voice design (no reference audio)

Embed a parenthetical description at the start of the text. No voice profile needed. Fast, infinitely variable, great for one-offs or prototypes.

```json
{ "text": "(A young woman with a gentle, melancholic tone)Hello, old friend." }
```

Reach for this when: the user wants a specific vibe/accent/emotion but doesn't need repeatability, or there's no reference clip handy.

**See `references/voice_design.md` for the description pattern cookbook.**

### Voice cloning (reference audio)

Pass `voice: "<name>"` to use a saved profile. Repeatable, consistent across sessions. Seeded voice is `rick`.

```json
{ "text": "Wubba lubba dub dub", "voice": "rick" }
```

Use this when: a named character/persona needs to persist across calls, or the user explicitly supplied a reference sample.

**Create the voice with the CLI, not by hand:** `heavy voxxy voice clone "<who>"` for a person or character, `voxxy voice add FILE --auto` for a
recording. Both set `prompt_text` (the exact transcript of the reference clip), the biggest quality lever. See
[voice-workflows](voice-workflows.md) and [reference-clip-quality](reference-clip-quality.md).

**To clone a user's own voice interactively** (user says "clone my voice as…"), see the [Interactive voice cloning workflow](#interactive-voice-cloning-workflow) below — it walks through presenting a reading passage, receiving a Telegram voice message, and uploading the raw audio.

**Rule of thumb:** try description first unless the user names a voice or provides audio. Descriptions cost nothing to iterate.

## Workflows

### Add a new voice

Use the CLI. It cuts a clean 10-15 s clip, transcribes it and uploads both (`prompt_text`):

```bash
voxxy voice add FILE --auto -n <slug> -d "<Display Name>" -t tag1,tag2
voxxy voice add FILE --start 12.6 --end 26.1 -n <slug>        # you choose the window
voxxy voice add clip.wav -n <slug> --prompt-text "exact words spoken in the clip"
```

Accepts wav, ogg, mp3, flac, m4a. Full procedure: [voice-workflows](voice-workflows.md) B.

Raw-API fallback (no CLI available; no cutting, no transcript, so lower quality). `scripts/add_voice.sh` wraps it and takes an optional
`prompt_text`:

```bash
scripts/add_voice.sh <name> "<Display Name>" <path/to/audio.ext> [tag1,tag2] [prompt_text]
curl -X POST https://vox.delo.sh/voices \
  -F name=<slug> -F display_name="<Display>" -F tags="<tag1>,<tag2>" \
  -F prompt_text="<exact transcript of the clip>" \
  -F audio=@/path/to/audio.ogg
```

To also pin an ElevenLabs fallback voice, update the row directly against the host postgres:

```bash
psql -h localhost -U "$DEFAULT_USERNAME" -d vox -c \
  "UPDATE voices SET elevenlabs_voice_id='<voice_id>' WHERE name='<slug>';"
```

### Interactive voice cloning workflow

When the user says **"clone my voice as \<name\>"** (or any variant — "create a voice called…", "register my voice as…", "add a voice named…"), follow this 5-step interactive workflow. The entire flow is designed for Telegram voice messages but works with any audio file the agent can access.

**See `references/voice_cloning_passages.md` for the full set of phonetically-balanced reading passages.**

#### Step 1 — Slugify the name

Convert the user-provided name to a slug: lowercase, spaces → hyphens, strip non-alphanumeric characters. Example: `"My Cool Voice"` → `my-cool-voice`.

#### Step 2 — Present a reading passage

Pick a passage from `references/voice_cloning_passages.md` (default: Passage 1, "Standard"). Present it to the user and ask them to read it aloud as a **Telegram voice message**. The passage is ~5–10 s spoken — enough for the model to capture timbre without padding silence.

Example agent message:

> Great! I'll clone your voice as **jarad**. Please read this passage aloud and send it as a voice message:
>
> *"The quick brown fox jumps over the lazy dog. She sold sea shells by the sea shore, and the wind whispered through the tall green trees."*

#### Step 3 — Receive the recording

When the user sends a Telegram voice message, the agent receives the **raw audio file path** (typically an `.ogg` file). Keep the original file; the CLI decodes it itself.

(Older versions of this skill said never to run STT. That is wrong now: the exact transcript of the uploaded clip,
sent as `prompt_text`, is what makes the clone sound like the speaker. Transcribe the **clip**, not to replace the audio. `voice add --auto` does it for you.)

#### Step 4 — Upload the raw audio

Upload with the CLI (cuts, transcribes and sets `prompt_text`):

```bash
voxxy voice add /path/to/voice_message.ogg --auto -n <slug> -d "<Display Name>" --no-prompt
```

**Raw-API fallback** (only when the CLI is not installed; no cut, no transcript). `scripts/clone_voice.sh` uploads, verifies,
synthesizes a confirmation and fails loudly if the engine was not a real clone. Pass the transcript as the fifth argument:

```bash
scripts/clone_voice.sh <name> "<Display Name>" <path/to/audio.ogg> [tags] [prompt_text]
```

#### Step 5 — Verify and confirm

After upload, verify the voice was registered and synthesize a confirmation message in the new voice:

```bash
# Verify
curl https://vox.delo.sh/voices/<slug>

# Synthesize confirmation
curl -X POST https://vox.delo.sh/synthesize-url \
  -H 'content-type: application/json' \
  -d '{"text":"Voice cloning complete. How do I sound?","voice":"<slug>"}'
```

Or via MCP:

```
vox:speak_url(text="Voice cloning complete. How do I sound?", voice="<slug>")
```

Send the confirmation audio URL back to the user as a Telegram voice note (see the "Send a voice note to Telegram" workflow above). The user can then confirm whether the clone sounds right, and if not, re-record with a different passage.

#### Quick reference: the full agent flow

```
User: "clone my voice as jarad"
  ↓
Agent: slugify("jarad") → "jarad"
  ↓
Agent: present passage from references/voice_cloning_passages.md
  ↓
User: sends Telegram voice message (raw .ogg file)
  ↓
Agent: get raw audio file path
  ↓
Agent: voxxy voice add /path/to/voice_message.ogg --auto -n jarad --no-prompt
  ↓
Service: POST /voices → stores the clean clip as jarad.wav with prompt_text
  ↓
Agent: GET /voices/jarad → verify registered
  ↓
Agent: speak_url("Voice cloning complete.", voice="jarad") → audio_url
  ↓
Agent: send audio_url to user as Telegram voice note
  ↓
User: "sounds great!" or "try again with a different passage"
```

#### Pitfalls

- **Always set `prompt_text`** (exact transcript of the uploaded clip). It is worth about +0.1 ecapa over the same clip without it.
- **Name must be slugified** before upload. The service stores voices by slug; spaces and uppercase cause lookup failures.
- **If the clone sounds off**, re-record with a different passage from `references/voice_cloning_passages.md`. Different passages emphasize different phoneme distributions.
- **Background noise is the #1 quality killer.** Encourage the user to record in a quiet room.
- **The service keeps the first 30 s of an upload, which is not a clean cut.** Let `--auto` / `--start --end` choose a 10-15 s whole-sentence window instead. Aim for 10-15 s of actual speech.

### Synthesize speech (inline bytes)

```bash
scripts/synth.sh "Text to say" [voice] [output.wav]
```

### Synthesize speech (delivery URL)

```bash
scripts/synth_url.sh "Text to say" [voice]
# prints the OGG/Opus URL to stdout; usable in Telegram/HA/curl
```

### Send a voice note to Telegram (OpenClaw)

The end-to-end pattern for every OpenClaw agent. Two steps:

```
1. vox:speak_url(text, voice?)  →  { audio_url, engine, duration_s }
2. openclaw message send --channel telegram
                         --target <chat_id>
                         --media <audio_url>
                         --as-voice
```

Telegram fetches the URL directly from `vox.delo.sh/audio/<uuid>.ogg` (cached 1h). The agent never streams bytes. Works identically from crons, subagents, or direct agent turns.

**See `references/integrations.md` for the full Telegram recipe**, including per-job `delivery` config for cron jobs and topic-scoped sends.

### Register with an MCP-capable agent

The service exposes FastMCP at `/mcp/` with three tools: `speak`, `speak_url`, and `list_voices_tool`. Same endpoint works for Hermes, OpenClaw, and Claude Code.

```bash
scripts/register_mcp.sh hermes     # or openclaw, claude-code
```

**See `references/integrations.md` for the exact config per agent**, including the Hermes v0.8.0 CLI workaround.

### Integrate with Node-RED

Drop-in custom node at `~/docker/stacks/utils/vox/node-red-contrib-vox/`. Install into a running Node-RED:

```bash
cd ~/.node-red
npm install ~/docker/stacks/utils/vox/node-red-contrib-vox
# Restart Node-RED
```

Drag the **vox tts** node into a flow. Input `msg.payload` = string. Output `msg.payload` = WAV Buffer. Optional `msg.voice` overrides the configured voice.

**See `references/integrations.md` Node-RED section for flow examples.**

### Integrate with a new platform (generic checklist)

When bolting vox onto any new CLI or platform, follow the universal integration checklist in `references/integrations.md`. Short version:

1. Does the target speak MCP? Register `https://vox.delo.sh/mcp/` and use `speak_url`.
2. Else, does it accept an audio URL (Telegram, Discord, HA, `<audio>`)? `POST /synthesize-url`, hand over `audio_url`.
3. Else, does it accept bytes? `POST /synthesize`, stream WAV.
4. Else, does it run Node.js? Install `node-red-contrib-vox` or copy the wrapper.

### Upgrade an engine

To upgrade engine dependencies (e.g. `voxcpm` or `vibevoice`), resolve lockfiles, rebuild sidecar images, recreate containers with compose profiles, and run verification probes, follow the [Engine upgrade workflow](../SKILL.md#engine-upgrade-workflow) in `SKILL.md`.

### Troubleshoot

Known failure modes and fixes live in `references/troubleshooting.md`. Check there before debugging from scratch. Top categories:

- OOM / VRAM exhaustion (usually reference audio too long or ollama coexistence)
- MCP handshake 400 (trailing slash missing on client-side URL)
- Telegram rejects the voice URL (use `speak_url`, not `speak` + upload; ensure OGG/Opus, not WAV)
- 500 on first request after container restart (warmup still in progress; ~45-60s with `VOX_OPTIMIZE=1`)
- Fallback engine not engaging (`ELEVENLABS_API_KEY` unset in container env)

