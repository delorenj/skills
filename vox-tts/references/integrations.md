# Integrations

One service, one contract, multiple consumers. All integrations speak to `https://vox.delo.sh`.

## MCP-capable agents (Hermes, OpenClaw, Claude Code)

FastMCP is mounted at `/mcp/` (trailing slash required). Tools exposed:

- `speak(text, voice=None, cfg=2.0, steps=10)` → base64 WAV
- `list_voices_tool()` → list of saved voices

### Hermes

**Hermes v0.8.0 CLI bug:** `hermes mcp add` drops to interactive chat when invoked without a TTY. Work around by editing the config directly.

```bash
scripts/register_mcp.sh hermes
```

Manual equivalent:

```bash
python3 -c "
import yaml, pathlib
p = pathlib.Path.home() / '.hermes/config.yaml'
cfg = yaml.safe_load(p.read_text()) or {}
cfg.setdefault('mcp_servers', {})['vox'] = {'url': 'https://vox.delo.sh/mcp/'}
p.write_text(yaml.safe_dump(cfg, sort_keys=False))
"
hermes mcp test vox     # should report 2 tools discovered
```

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

Restart Claude Code after editing. Tools show up namespaced as `vox:speak` and `vox:list_voices_tool`.

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
