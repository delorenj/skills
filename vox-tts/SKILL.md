---
name: vox-tts
description: Generate speech using the self-hosted voxxy (vox) TTS service at https://vox.delo.sh.
  Use when the user asks to speak, say, narrate, synthesize speech, clone a voice,
  create a voice, add or register a voice, pipe TTS, or control voice qualities by
  description (e.g. "a young woman with a cheerful voice"). Handles HTTP API usage,
  voice profile management, description-based voice design, cloning, MCP registration,
  and integration patterns for new platforms.
metadata:
  pipeline-status:
  - new
---

# vox-tts

A self-hosted TTS service at **<https://vox.delo.sh>** wrapping VoxCPM2 with a postgres-backed voice profile store and support for multiple engines. Deployed at `~/code/voxxy` (core: `compose.yml`, GPU engines: `compose.engines.yml` — both engine containers must be up or clones degrade silently, see below).

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
| **Interactive voice cloning** (user says "clone my voice as…")  | See [Interactive voice cloning workflow](#interactive-voice-cloning-workflow) below |
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

**Cloned voices are engine-bound.** A voice cloned via `POST /voices` stores its reference in `vibevoice_ref_path` and is served by the **vibevoice** engine first (per-request `preferred` routing in `app/engines.py`; everything else follows `VOX_ENGINES` order, voxcpm first). If vibevoice is down, voxcpm still receives the reference clip — `app/voices.py:46-48` falls back to `wav_path` for any engine with no specific override — so the clone *degrades*, it is not erased. Symptom is a recognisable-but-off read, not a stranger. Fix: `docker compose -f ~/code/voxxy/compose.engines.yml up -d voxxy-engine-vibevoice`, then confirm `"name":"vibevoice","ready":true` in `/healthz`.

The one that does replace the voice outright is **ElevenLabs fallback**: if both GPU engines are down and `ELEVENLABS_API_KEY` is set, vox answers `200` in a stranger's voice, logging `vox: voice clone BYPASSED`, and delivers it anyway. **Check the `engine` field on every clone synthesis** — `vibevoice` or `voxcpm` is the clone, `elevenlabs` is not your voice.

**The reference budget is 10 seconds, not 30.** Two different caps stack, and only the second one matters. `POST /voices` trims ingest to `VOX_REF_AUDIO_MAX_SECONDS` = 30s (`compose.yml:16`, applied at `app/main.py:578-584`, keeping the **first** 30s). But the vibevoice container sets the same variable to **10** (`compose.engines.yml:69`), and `engines/vibevoice/engine/synth.py:183,208` reloads the reference with `duration=10.0`. Its `/healthz` says so directly: `"max_ref_seconds": 10.0`. So seconds 10–30 of any reference clip are stored, backed up, and never seen by the model. Write clone passages for **8–10 clean seconds** and put the best, most neutral speech first — everything after is dead weight.

## Detailed procedures

Read [voice and integration workflows](references/voice-and-integration-workflows.md) for the relevant
implementation or diagnosis. Voice cloning and external delivery require the
user to request those actions.

## Defaults cheat sheet

| Param                       | Default                       | Notes                                                            |
| --------------------------- | ----------------------------- | ---------------------------------------------------------------- |
| `cfg`                       | 2.0                           | Classifier-free guidance; higher = more faithful, less variation |
| `steps`                     | 10                            | Diffusion steps; 4-6 for speed, 15-20 for max quality            |
| `normalize`                 | false                         | Text normalization (numbers → words etc.)                        |
| `denoise`                   | false                         | **Dead field.** Declared at `app/main.py:98`, read nowhere; `POST /voices` has no denoise param at all. Clean the audio before upload instead. |
| Cache TTL (audio URLs)      | 3600s                         | `VOX_AUDIO_TTL_SECONDS` env; 1h is plenty for Telegram           |
| Fallback voice (ElevenLabs) | Adam (`pNInz6obpgDQGcFmaJgB`) | `ELEVENLABS_DEFAULT_VOICE` env                                   |

Synthesis runs at roughly **21 characters per second** on an RTX 3090 with `VOX_OPTIMIZE=1` — measured, not estimated: a 60-char line takes ~2s, a 1,665-char line takes ~35s. Budget by length, not by the 2s headline. First call after a container restart adds ~15s (JIT compile). OGG/Opus transcode adds <100ms via ffmpeg.

This matters for any caller with a timeout. The Hermes `vox` TTS plugin hardcodes a 60s httpx timeout (`plugins/tts/vox/__init__.py:29,316`) and ignores `tts.vox.timeout`, so a single chunk past roughly 2,500 characters fails outright. Cap it with `tts.vox.max_text_length` (read at `tools/tts_tool.py:436-441`), which chunks instead of failing.
