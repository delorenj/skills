---
name: vox-tts
description: Generate speech using the self-hosted vox TTS service (VoxCPM2) at https://vox.delo.sh. Use when the user asks to speak, say, narrate, synthesize speech, clone a voice, create a voice, add or register a voice, pipe TTS into OpenClaw / Hermes / Claude Code / Node-RED, or control voice qualities by description (e.g. "a young woman with a cheerful voice"). Handles HTTP API usage, voice profile management, description-based voice design vs reference cloning, MCP registration for agent systems, and Node-RED custom node integration.
---

# vox-tts

A self-hosted TTS service at **https://vox.delo.sh** wrapping VoxCPM2 with a postgres-backed voice profile store. Deployed at `~/docker/stacks/utils/vox/`.

## Quick reference

| Action | How |
|---|---|
| One-off synthesis | `POST /synthesize { text, voice?, cfg?, steps? }` → `audio/wav` |
| List voices | `GET /voices` |
| Add a voice | `POST /voices` (multipart: name, display_name, audio) |
| Register with agent (Hermes/OpenClaw) | MCP server at `https://vox.delo.sh/mcp/` (trailing slash required) |
| Node-RED | `node-red-contrib-vox` package at `~/docker/stacks/utils/vox/node-red-contrib-vox/` |
| Health | `GET /healthz` |

**Trailing slash on `/mcp/` is mandatory.** Without it, FastAPI 307-redirects and HTTPX drops the POST body.

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

### Synthesize speech

```bash
scripts/synth.sh "Text to say" [voice] [output.wav]
```

Defaults: no voice (description mode), writes to `./out.wav`. For programmatic use:

```bash
curl -X POST https://vox.delo.sh/synthesize \
  -H 'content-type: application/json' \
  -d '{"text":"Hello world","voice":"rick","cfg":2.0,"steps":10}' \
  -o out.wav
```

### Register with an MCP-capable agent

The service exposes FastMCP at `/mcp/` with two tools: `speak` and `list_voices_tool`. Same endpoint works for Hermes, OpenClaw, and Claude Code.

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

### Troubleshoot

Known failure modes and fixes live in `references/troubleshooting.md`. Check there before debugging from scratch. Top categories:

- OOM / VRAM exhaustion (usually reference audio too long or ollama coexistence)
- MCP handshake 400 (trailing slash missing on client-side URL)
- 500 on first request after container restart (warmup still in progress; ~45-60s with `VOX_OPTIMIZE=1`)

## Defaults cheat sheet

| Param | Default | Notes |
|---|---|---|
| `cfg` | 2.0 | Classifier-free guidance; higher = more faithful, less variation |
| `steps` | 10 | Diffusion steps; 4-6 for speed, 15-20 for max quality |
| `normalize` | false | Text normalization (numbers → words etc.) |
| `denoise` | false | Apply ZipEnhancer to reference before cloning |

Steady-state synthesis ~2s on an RTX 3090 with `VOX_OPTIMIZE=1`. First call after restart takes ~15s (JIT compile).
