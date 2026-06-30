---
name: vox-tts
description: Generate speech using the self-hosted voxxy (vox) TTS service at https://vox.delo.sh. Use when the user asks to speak, say, narrate, synthesize speech, clone a voice, create a voice, add or register a voice, pipe TTS, or control voice qualities by description (e.g. "a young woman with a cheerful voice"). Handles HTTP API usage, voice profile management, description-based voice design, cloning, MCP registration, and integration patterns for new platforms.
pipeline-status:
  - new
---

# vox-tts

A self-hosted TTS service at **<https://vox.delo.sh>** wrapping VoxCPM2 with a postgres-backed voice profile store and support for multiple engines. Deployed at `~/docker/stacks/utils/vox/`.

## Quick reference

| Action                                                          | How                                                                         |
| --------------------------------------------------------------- | --------------------------------------------------------------------------- |
| One-off synthesis (inline WAV bytes)                            | `POST /synthesize { text, voice?, cfg?, steps? }` → `audio/wav`             |
| **Synthesis for delivery to Telegram / browser / HA / Discord** | `POST /synthesize-url` → `{audio_url, engine, duration_s, bytes}`           |
| MCP tool: inline bytes (base64 WAV)                             | `speak(text, voice?)`                                                       |
| **MCP tool: delivery URL (OGG/Opus, Telegram-ready)**           | `speak_url(text, voice?)`                                                   |
| MCP tool: list voices                                           | `list_voices_tool()`                                                        |
| List voices (HTTP)                                              | `GET /voices`                                                               |
| Add a voice                                                     | `POST /voices` (multipart: name, display_name, audio)                       |
| Register with agent (Hermes/OpenClaw/Claude Code)               | MCP server at `https://vox.delo.sh/mcp/` (trailing slash required)          |
| Node-RED                                                        | `node-red-contrib-vox` at `~/docker/stacks/utils/vox/node-red-contrib-vox/` |
| Health + engine status                                          | `GET /healthz`                                                              |

**Trailing slash on `/mcp/` is mandatory.** Without it, FastAPI 307-redirects and HTTPX drops the POST body.

## speak vs speak_url: pick the right one

| If the audio will be...                               | Use         | Why                                                                                   |
| ----------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------- |
| Sent to Telegram / Discord / Slack                    | `speak_url` | Channel APIs accept a URL; their servers fetch it. Zero byte-bloat on the agent wire. |
| Piped into a browser `<audio>` tag                    | `speak_url` | Browsers stream URLs; no base64 round-trip.                                           |
| Handed to Home Assistant `media_player.play_media`    | `speak_url` | HA wants a URL for `media_content_id`.                                                |
| Processed inline by the agent (splice, analyze, loop) | `speak`     | Bytes are already local; a URL fetch would add a hop.                                 |
| Written to a local file in a shell script             | either      | `speak_url` + `curl -o` is easier than base64 + `base64 -d`.                          |

**Default to `speak_url`.** It costs the agent nothing in tokens (the response is small JSON) and works across every delivery surface except raw inline byte processing.

## Engine fallback

`GET /healthz` reports which engines are registered and whether each is available:

```json
{
  "status": "ok",
  "model_loaded": true,
  "engines": [
    { "name": "voxcpm", "available": true },
    { "name": "elevenlabs", "available": true }
  ]
}
```

The orchestrator tries them in order. Every `speak_url` / `speak` response includes `engine: "voxcpm"` or `engine: "elevenlabs"` so you can detect when fallback engaged. ElevenLabs auto-disables when `ELEVENLABS_API_KEY` is unset.

Per-voice ElevenLabs mapping lives in the `voices.elevenlabs_voice_id` column. NULL falls back to the global default (`ELEVENLABS_DEFAULT_VOICE`, Adam by default).

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

**Rule of thumb:** try description first unless the user names a voice or provides audio. Descriptions cost nothing to iterate.

## Workflows

### Add a new voice

Use `scripts/add_voice.sh` for a single command that uploads and registers the profile. The service auto-trims to 30s mono on ingest.

```bash
scripts/add_voice.sh <name> "<Display Name>" <path/to/audio.ext> [tag1,tag2]
```

Accepts wav, ogg, mp3, flac, m4a. For the raw HTTP form:

```bash
curl -X POST https://vox.delo.sh/voices \
  -F name=<slug> -F display_name="<Display>" \
  -F tags="<tag1>,<tag2>" \
  -F audio=@/path/to/audio.ogg
```

To also pin an ElevenLabs fallback voice, update the row directly against the host postgres:

```bash
psql -h localhost -U "$DEFAULT_USERNAME" -d vox -c \
  "UPDATE voices SET elevenlabs_voice_id='<voice_id>' WHERE name='<slug>';"
```

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

### Troubleshoot

Known failure modes and fixes live in `references/troubleshooting.md`. Check there before debugging from scratch. Top categories:

- OOM / VRAM exhaustion (usually reference audio too long or ollama coexistence)
- MCP handshake 400 (trailing slash missing on client-side URL)
- Telegram rejects the voice URL (use `speak_url`, not `speak` + upload; ensure OGG/Opus, not WAV)
- 500 on first request after container restart (warmup still in progress; ~45-60s with `VOX_OPTIMIZE=1`)
- Fallback engine not engaging (`ELEVENLABS_API_KEY` unset in container env)

## Defaults cheat sheet

| Param                       | Default                       | Notes                                                            |
| --------------------------- | ----------------------------- | ---------------------------------------------------------------- |
| `cfg`                       | 2.0                           | Classifier-free guidance; higher = more faithful, less variation |
| `steps`                     | 10                            | Diffusion steps; 4-6 for speed, 15-20 for max quality            |
| `normalize`                 | false                         | Text normalization (numbers → words etc.)                        |
| `denoise`                   | false                         | Apply ZipEnhancer to reference before cloning                    |
| Cache TTL (audio URLs)      | 3600s                         | `VOX_AUDIO_TTL_SECONDS` env; 1h is plenty for Telegram           |
| Fallback voice (ElevenLabs) | Adam (`pNInz6obpgDQGcFmaJgB`) | `ELEVENLABS_DEFAULT_VOICE` env                                   |

Steady-state synthesis ~2s on an RTX 3090 with `VOX_OPTIMIZE=1`. First call after restart takes ~15s (JIT compile). OGG/Opus transcode adds <100ms via ffmpeg.
