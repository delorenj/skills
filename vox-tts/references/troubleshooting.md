# Troubleshooting

Observed failure modes and their fixes, ordered by how often they bite.

## Telegram rejects the voice note / sends it as a file

**Symptom:** `sendVoice` returns 400 `Bad Request: WEBPAGE_CURL_FAILED` or Telegram shows a file icon with no waveform.

**Causes, in order:**

1. **Passed a WAV URL where OGG/Opus is required.** Use `speak_url` (returns `.ogg`), not `speak` or `/synthesize` (both return WAV). Telegram voice-notes require OGG/Opus at 48 kHz mono.
2. **Cache URL expired.** Default TTL is 3600s (`VOX_AUDIO_TTL_SECONDS`). If the agent held the URL longer, resynthesize.
3. **URL unreachable.** Telegram fetches from its own datacenters. Verify from outside the LAN: `curl -I https://vox.delo.sh/audio/<id>.ogg`. Must be 200 with `content-type: audio/ogg`.
4. **Trying to `sendVoice` a WAV via OpenClaw `message send`.** The channel adapter only converts when the URL extension matches. Keep `.ogg`.

## Fallback engine never engages

**Symptom:** VoxCPM2 errors (OOM, CUDA fault), but `engine` in the response is still `"voxcpm"` and the request fails.

**Cause:** `ELEVENLABS_API_KEY` is not set in the container env. `GET /healthz` confirms:

```json
{"engines":[{"name":"voxcpm","available":true},
            {"name":"elevenlabs","available":false}]}
```

**Fix:** export `ELEVENLABS_API_KEY` on the host (or in the stack `.env`) and `docker compose up -d` to restart. Key lives in 1password DeLoSecrets.

## Audio URL returns 404

**Symptom:** `GET /audio/<id>.ogg` → 404 shortly after synthesis.

**Causes:**

1. Cache TTL expired. Check mtime: `docker exec vox ls -la /data/audio-cache/`.
2. Container restarted and the bind mount was reset. Less common; re-synthesize.
3. The cache id contains non-hex characters (path traversal guard kicks in, returns 404). Only hex uuids are valid; if you see this, something is generating bad ids client-side.



## MCP client gets 400 Bad Request

**Symptom:** Agent (Hermes / OpenClaw / Claude Code) reports `Client error '400 Bad Request' for url 'https://vox.delo.sh/mcp/'` on connection test.

**Cause:** Client is hitting `https://vox.delo.sh/mcp` (no trailing slash). FastAPI 307-redirects to `/mcp/`, and HTTPX's default behavior on 307 is to convert POST to GET and drop the body. FastMCP rejects the GET.

**Fix:** Register with the trailing slash: `https://vox.delo.sh/mcp/`. That skips the redirect entirely.

## OOM / CUDA out of memory during synthesis

**Symptom:** `torch.OutOfMemoryError: CUDA out of memory. Tried to allocate X GiB` in container logs.

**Most common causes, in order:**

1. **Reference audio too long.** The model encodes the full reference into GPU memory. A 7-minute ref = 14+ GB extra activation. The service auto-trims to 30s on ingest via `POST /voices`, but raw `reference_wav_path` passed through the Python API or CLI bypasses this. Keep refs short.
2. **Ollama sharing the GPU.** `nvidia-smi` will show ollama holding 5-6 GB. Stop the specific model (`ollama stop <name>`) or set `OLLAMA_KEEP_ALIVE=0` in its systemd env.
3. **Runaway concurrent requests.** The default `concurrency_limit=1` prevents this from within the Gradio-based web UI but not across direct HTTP calls. Rate-limit on the caller side.

**Diagnostic commands:**

```bash
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
docker logs vox --tail 50 | grep -E 'MEM|OutOfMemory'
```

## Container crash-loops at startup with inductor error

**Symptom:** `torch._dynamo.exc.BackendCompilerFailed: backend='inductor' raised: RuntimeError: Failed to find C compiler.`

**Cause:** `VOX_OPTIMIZE=1` triggers `torch.compile`, which needs `gcc` at runtime. The `nvidia/cuda:*-runtime` base image doesn't ship one.

**Fix:** Ensure the Dockerfile installs `gcc g++` via apt. The shipped Dockerfile does; this only bites if someone forks it.

## First request after restart takes 15+ seconds

**Expected.** With `VOX_OPTIMIZE=1`, torch.compile JITs the graph on the first forward pass. Warmup is ~45-60s total, first real request another ~15s, steady-state ~2s per call.

**Options:**

- Wait (recommended)
- Flip `VOX_OPTIMIZE=0` in `compose.yml` if startup speed matters more than inference throughput
- Add a keepalive ping to the healthcheck that hits `/synthesize` once after boot

## HTTP returns 307 Temporary Redirect on `/mcp`

Same as the first entry; trailing-slash issue. Not a bug, just FastAPI route normalization.

## Voice profile missing on disk

**Symptom:** `POST /synthesize` with an existing voice name returns 500 with `voice file missing on disk`.

**Cause:** postgres row exists but the WAV was deleted from `~/docker/stacks/utils/vox/voices/`. The bind-mounted directory is the source of truth for bytes; postgres only holds metadata.

**Fix:** Either restore the WAV (rsync from backup) or re-upload via `POST /voices` with the same `name` to overwrite.

## Output audio sounds garbled / wrong voice

Things to try in order:

1. **Increase `cfg`** (2.5, 3.0) — pushes the model to adhere more strictly to the reference / description
2. **Increase `steps`** (15, 20) — more diffusion iterations
3. **Clean the reference** — `denoise: true` applies ZipEnhancer; useful for phone / field recordings
4. **Shorten the text** — very long passages can drift mid-generation; chunk into sentences and concatenate

## Traefik route not forwarding (502)

**Check:**

```bash
docker logs traefik --tail 50 | grep vox
docker network inspect proxy | grep vox   # container must be on proxy network
curl -I https://vox.delo.sh/healthz        # should be 200
docker exec vox curl -s http://localhost:8000/healthz  # internal baseline
```

If internal works but Traefik doesn't, the proxy label set in `compose.yml` probably got corrupted. Full set required:

```
traefik.enable=true
traefik.http.routers.vox.rule=Host(`vox.delo.sh`)
traefik.http.routers.vox.entrypoints=websecure
traefik.http.routers.vox.tls.certresolver=letsencrypt
traefik.http.services.vox.loadbalancer.server.port=8000
traefik.docker.network=proxy
```
