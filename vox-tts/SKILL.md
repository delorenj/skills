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
| **Upgrade an engine (VoxCPM / VibeVoice)**                      | See [Engine upgrade workflow](#engine-upgrade-workflow) below               |
| Speak from a Hermes agent                                       | Native `tts.provider: vox` (fleet base); the fleet does NOT load the vox MCP |
| Speak from a shell / any agent with a terminal                  | `voxxy speak "text"` (see `voxxy speak --help`)                            |
| Register with an MCP client that has no native vox path         | MCP server at `https://vox.delo.sh/mcp/` (trailing slash required)          |
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

## Engine upgrade workflow

The three-container topology decouples core orchestration (`voxxy-core`, container `vox`, CPU-only) from GPU-bound sidecar engines (`voxxy-engine-voxcpm`, `voxxy-engine-vibevoice`). Each engine container maintains its own `pyproject.toml`, `uv.lock`, and `Dockerfile` under `engines/<name>/`.

### Step-by-step upgrade procedure

#### 1. Version discovery & runtime audit
- **Upstream releases:** Check PyPI and GitHub releases:
  ```bash
  curl -s https://pypi.org/pypi/voxcpm/json | jq -r '.info.version'
  ```
- **Running container version:** Check installed package version via `importlib.metadata`:
  ```bash
  docker exec voxxy-engine-voxcpm /opt/venv/bin/python -c \
    "import importlib.metadata; print(importlib.metadata.version('voxcpm'))"
  ```
  *(Never use `voxcpm.__version__`; the module does not define it and raises `AttributeError`)*.
- **Model weights on Hugging Face:** Check if the model weights snapshot has updated:
  ```bash
  cat ~/.cache/huggingface/hub/models--openbmb--VoxCPM2/refs/main
  curl -s https://huggingface.co/api/models/openbmb/VoxCPM2 | jq -r '.sha'
  ```
  Package updates (inference code, streaming VAE decoders, device handling) are distinct from model weight revisions.

#### 2. Dependency bumping & lockfile update
- Bump the version pin in `engines/<name>/pyproject.toml` (e.g. `voxcpm==2.0.3`).
- Re-lock dependencies with uv:
  ```bash
  cd engines/voxcpm && uv lock
  ```
- Review the diff (`git diff engines/voxcpm/uv.lock`) to ensure PyTorch and torchaudio stay pinned to the explicit `pytorch-cu124` index and do not drift to PyPI CPU wheels.

#### 3. Rebuild the engine container image
Rebuild the engine image via compose:
```bash
docker compose -f compose.yml -f compose.engines.yml build voxxy-engine-voxcpm
# Or via mise alias:
mise run build:voxcpm
```
The Dockerfile provisions Python 3.12 via uv and runs `uv sync --frozen --no-install-project` into `/opt/venv`.

#### 4. Recreate the engine container with compose profile
Engine containers are defined with compose profiles in `compose.engines.yml` (`profiles: ["voxcpm"]` / `profiles: ["vibevoice"]`). You must pass `--profile` or compose will ignore the service:
```bash
docker compose -f compose.yml -f compose.engines.yml --profile voxcpm up -d --no-build voxxy-engine-voxcpm
```
Verify the container picked up the new version:
```bash
docker exec voxxy-engine-voxcpm /opt/venv/bin/python -c \
  "import importlib.metadata; print(importlib.metadata.version('voxcpm'))"
```

#### 5. Verification & smoke testing
- **Container startup:** Inspect logs for successful model load:
  ```bash
  docker logs --tail 30 voxxy-engine-voxcpm
  # Look for: "Loaded VoxCPM2Model" and "Application startup complete."
  ```
- **Engine healthz:**
  ```bash
  docker exec vox curl -s http://voxxy-engine-voxcpm:8000/healthz
  # Expects: {"engine":"voxcpm","ready":true,"model_loaded":true,...}
  ```
- **Direct synthesis test:** Send a raw synthesis payload directly from the `vox` core container over the Docker network:
  ```bash
  docker exec vox curl -s -X POST http://voxxy-engine-voxcpm:8000/v1/synthesize \
    -H 'content-type: application/json' \
    -d '{"text":"Testing synthesis."}' | jq -r '{engine, sample_rate, duration_s, bytes, has_wav: (.wav_b64 != null)}'
  ```
- **Voice cloning verification:** Test with a reference audio sample (`/data/voices/rick.wav`):
  ```bash
  docker exec vox python3 -c '
  import base64, urllib.request, json
  with open("/data/voices/rick.wav", "rb") as f:
      b64 = base64.b64encode(f.read()).decode("ascii")
  data = json.dumps({"text": "Test clone.", "reference_audio_b64": b64}).encode("utf-8")
  req = urllib.request.Request("http://voxxy-engine-voxcpm:8000/v1/synthesize", data=data, headers={"Content-Type": "application/json"})
  print(json.loads(urllib.request.urlopen(req).read().decode("utf-8")))
  '
  ```
- **Contract and CLI tests:**
  ```bash
  bash scripts/verify-engine-contract.sh
  (cd cli && uv run pytest)
  ```

#### 6. Delivery
Commit both `pyproject.toml` and `uv.lock` in the engine directory:
```bash
git add engines/voxcpm/pyproject.toml engines/voxcpm/uv.lock
git commit -m "feat(voxcpm): upgrade voxcpm to <version>"
git push origin main
```

### Lessons learned & engine gotchas

1. **`voxcpm` package version inspection:** `voxcpm` does NOT expose `__version__`. Calling `python -c "import voxcpm; print(voxcpm.__version__)"` throws `AttributeError`. Always inspect installed metadata with `importlib.metadata.version('voxcpm')`.
2. **Compose profiles requirement:** In `compose.engines.yml`, each engine has a profile (`profiles: ["voxcpm"]`). If you run `docker compose up voxxy-engine-voxcpm` without `--profile voxcpm`, Docker Compose will silently skip the service.
3. **Standby engines are directly testable:** Local engines on a single GPU card are mutually exclusive (VoxCPM ~5 GB VRAM, VibeVoice ~7.5 GB VRAM). Even if an engine is in `standby` in `voxxy daemon status` / `.voxxy.state.json`, its container remains running and healthy on the internal Docker network (`http://voxxy-engine-<name>:8000`). You can test it directly via curl from `vox` without switching the active engine.
4. **Pytest test suite location:** Running `pytest` from repo root fails because `plugins/tts/vox/` is a Hermes plugin expecting `agent.tts_provider`. The CLI and integration test suite lives in `cli/tests/` and should be executed via `cd cli && uv run pytest`.
5. **Weights cache persistence:** Engine containers bind-mount `/home/delorenj/.cache/huggingface` to `/cache/huggingface`. Never change this to an ephemeral volume, or image rebuilds will re-download gigabytes of weights on startup.

