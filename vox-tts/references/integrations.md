---
pipeline-status:
  - new
---
# Integrations

One service, one contract, multiple consumers. All integrations speak to `https://vox.delo.sh`.

## Universal integration checklist

Before writing a new integration, walk this decision tree. Most new platforms fall into case 1 or case 2 and need zero code on the vox side.

```
Does the target...
  1. Speak MCP (streamable HTTP)?
     → Register https://vox.delo.sh/mcp/ (trailing slash!)
     → Use the speak_url tool
     → Example: OpenClaw, Cursor, any FastMCP-native client
     → NOT the Hermes fleet: it speaks through the native tts/vox plugin
       (`tts.provider: vox` in ~/.hermes/config.yaml). The vox MCP was removed
       from the fleet on 2026-10-01 because its schemas cost tokens every turn.

  2. Accept a remote audio URL (the target fetches it)?
     → POST /synthesize-url, pass audio_url into the target action
     → Example: Telegram sendVoice, Discord embed, Home Assistant
       media_player.play_media, <audio src="...">

  3. Accept raw audio bytes uploaded by the caller?
     → POST /synthesize, stream the returned WAV or transcode on the caller
     → Example: legacy SIP voice gateways, some CMS pipelines

  4. Run in Node.js / Node-RED?
     → Install node-red-contrib-vox (bytes path) or copy the HTTP wrapper

  5. None of the above?
     → Make the caller do HTTP. Use the Python or TypeScript sketch at the
       bottom of this file as the starting point.
```

**Rule of thumb:** prefer the URL path (`POST /synthesize-url` → `audio_url`) whenever the target supports it. Three wins:

1. Agent-side token cost is tiny (small JSON, not base64 audio)
2. The target's own CDN / fetcher handles delivery, letting it stream and cache
3. Vox stays domain-pure; no target-specific knowledge leaks in

The one hard rule: Telegram voice notes must be OGG/Opus, not WAV. That's why `speak_url` returns `.ogg` URLs. Do not try to hand `/synthesize`'s raw WAV to Telegram — `sendVoice` will reject it or downgrade playback.

## Telegram (OpenClaw / direct Bot API)

The universal delivery surface for OpenClaw agents. Two steps, regardless of agent.

### From within an OpenClaw agent turn

```
1. call  vox:speak_url(text="...", voice?="rick")
         → { audio_url, engine, duration_s, bytes }

2. call  openclaw message send
         --channel telegram
         --target <chat_id>            # or "<group>:topic:<topic_id>"
         --media  <audio_url>
         --as-voice
```

The OpenClaw gateway resolves the `target`, POSTs the action to the Telegram adapter, and Telegram servers fetch the URL from `vox.delo.sh/audio/<uuid>.ogg` directly. Cache lives for `VOX_AUDIO_TTL_SECONDS` (default 3600s) — more than enough for Telegram to fetch.

### From a cron / subagent (per-job `delivery` config)

Cron jobs carry their own delivery block. For jobs that should speak their output:

```json
{
  "delivery": {
    "mode": "announce",
    "channel": "telegram",
    "to": "-1001234567890:topic:55"
  },
  "run": "agent.speakAndReport"
}
```

The agent body still calls `vox:speak_url` internally; the gateway routes the resulting `message send` to the topic named in `delivery.to`.

### From the Bot API directly (no OpenClaw)

```bash
# 1. Synthesize
audio_url=$(
  curl -fsS -X POST https://vox.delo.sh/synthesize-url \
    -H 'content-type: application/json' \
    -d '{"text":"System online","voice":"rick"}' \
  | jq -r .audio_url
)

# 2. Send as voice note
curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendVoice" \
     -d "chat_id=${TG_CHAT_ID}" \
     -d "voice=${audio_url}"
```

The `voice=<url>` form tells Telegram to fetch. No multipart upload needed.

**Gotchas:**

- **Trailing slash** on `/mcp/` is mandatory for MCP; the `/audio/<id>.ogg` path has no such quirk.
- **Cache expiry:** if you hold the URL longer than 1 hour, Telegram's fetch returns 404. Resynthesize.
- **Size cap:** Telegram's `channels.telegram.mediaMaxMb` defaults to 100 MB. Voice notes at 32 kbps are ~4 KB/s; you'd need a 7+ hour monologue to trip it.
- **Format:** `speak_url` always returns OGG/Opus (48 kHz mono, VoIP preset). Telegram's native voice-note format.

## MCP-capable agents (OpenClaw, Claude Code)

FastMCP is mounted at `/mcp/` (trailing slash required). Tools exposed:

- `speak(text, voice=None, cfg=2.0, steps=10)` → `{audio_wav_b64, engine, bytes}` — inline WAV bytes, for callers that process audio locally
- `speak_url(text, voice=None, cfg=2.0, steps=10)` → `{audio_url, engine, duration_s, bytes, format}` — short-lived OGG/Opus URL, **preferred for delivery to Telegram/Discord/HA/browser**
- `list_voices_tool()` → list of saved voices

Every tool response carries `engine: "voxcpm" | "elevenlabs"` so agents can detect when ElevenLabs fallback engaged.

### Hermes

Do not register the vox MCP in Hermes. Fleet agents speak through the native
tts/vox plugin (`tts.provider: vox` in the fleet base `~/.hermes/config.yaml`,
enforced by flume's `hermes.fleet-config` rule), and anything with a terminal
can run `voxxy speak`. The MCP was removed from the fleet on 2026-10-01: its
tool schemas were loaded into every turn of every agent.

Never write `~/.hermes/config.yaml` with `yaml.safe_dump`: it is the
hand-maintained fleet base and a dump strips every comment in it. Profile
configs under `~/.hermes/profiles/` are generated; see the
agent-fleet-operations skill.

### OpenClaw

OpenClaw uses the same MCP semantics. Try CLI first, fall back to config file on failure:

```bash
openclaw mcp add vox --url https://vox.delo.sh/mcp/
```

If the CLI rejects, find OpenClaw's config file and add the same `mcp_servers` entry used for Hermes.

### Claude Code

Claude Code reads MCP servers from `~/.claude/settings.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "vox": {
      "type": "http",
      "url": "https://vox.delo.sh/mcp/"
    }
  }
}
```

Restart Claude Code after editing. Tools show up namespaced as `vox:speak`, `vox:speak_url`, and `vox:list_voices_tool`.

## Node-RED

### Install the custom node

```bash
cd ~/.node-red
npm install ~/docker/stacks/utils/vox/node-red-contrib-vox
# Restart Node-RED
```

### Flow patterns

**Pattern 1: HTTP webhook → TTS → file**

```
[HTTP In /speak]
    │ msg.payload = {text, voice}
    ▼
[Function: split payload]
    │ msg.payload = text; msg.voice = voice
    ▼
[vox tts]
    │ msg.payload = WAV Buffer
    ▼
[Write file /tmp/out.wav]
    ▼
[HTTP Response 200]
```

**Pattern 2: MQTT-driven announcements**

```
[MQTT In house/announce]
    │ msg.payload = string
    ▼
[vox tts] voice=announcer
    ▼
[HTTP POST to Home Assistant media_player.play_media]
```

**Pattern 3: Per-message voice via `msg.voice`**

The node accepts an override per message. Set `msg.voice` in a function node before the vox node to switch voices dynamically (e.g. different voice per user, channel, or topic).

### Future: Bloodbank event-driven pattern

The HTTP path works today. For at-least-once delivery + scale, replace the HTTP call with a Bloodbank (RabbitMQ) publish on topic `vox.synthesize`, and add an MCP-side subscriber. The command-pattern payload stays identical; only the transport changes.

## Plain HTTP

Any language. Synthesize:

```bash
curl -X POST https://vox.delo.sh/synthesize \
  -H 'content-type: application/json' \
  -d '{"text":"Hello","voice":"rick"}' \
  -o out.wav
```

List voices:

```bash
curl https://vox.delo.sh/voices
```

Add a voice (multipart):

```bash
curl -X POST https://vox.delo.sh/voices \
  -F name=alice -F display_name="Alice" \
  -F tags="female,english" \
  -F audio=@/path/to/alice.ogg
```

## Python client sketch

```python
import httpx

async def speak(text: str, voice: str | None = None, out: str = "out.wav") -> None:
    async with httpx.AsyncClient(timeout=60) as c:
        body = {"text": text}
        if voice:
            body["voice"] = voice
        r = await c.post("https://vox.delo.sh/synthesize", json=body)
        r.raise_for_status()
        with open(out, "wb") as f:
            f.write(r.content)
```

## TypeScript / Node client sketch

```typescript
export async function speak(text: string, voice?: string): Promise<Buffer> {
  const res = await fetch("https://vox.delo.sh/synthesize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  if (!res.ok) throw new Error(`vox ${res.status}: ${await res.text()}`);
  return Buffer.from(await res.arrayBuffer());
}
```
