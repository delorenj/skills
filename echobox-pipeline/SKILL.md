---
name: echobox-pipeline
description: Echobox transcription pipeline configuration and operations. Node-RED flow orchestrating file watch, MinIO upload, Fireflies transcription, and transcript output. Use when debugging the transcription pipeline, modifying watched directories, checking transcript output, or working with the echobox ledger.
---

# Echobox Transcription Pipeline

## Architecture

```
File Watch -> Hash/Dedup -> MinIO Upload -> Bloodbank Event
  -> Fireflies Upload -> Webhook -> Debounce -> Fetch Transcript
  -> Bloodbank Event -> Write CSV/MD to disk
```

Orchestrated by Node-RED (PM2 process), event backbone is Bloodbank (RabbitMQ).

## Key Paths

| What | Path |
|------|------|
| Flow definition | `/home/delorenj/code/33GOD/services/node-red-flow-orchestrator/flows/fireflies-bloodbank.json` |
| Runtime flow | `~/.node-red/flows.json` |
| PM2 ecosystem | `~/.node-red/ecosystem.config.js` |
| Subscriber scripts | `/home/delorenj/code/33GOD/services/node-red-flow-orchestrator/scripts/bloodbank_subscribe.py` |
| Start subscribers | `/home/delorenj/code/33GOD/services/node-red-flow-orchestrator/start-subscribers.sh` |
| Transcript output | `~/d/Transcripts/` (MD + CSV pairs) |
| BB envelope staging | `~/.node-red/bb/` |
| Subscriber logs | `~/.node-red/logs/subscriber-{upload,ready}.log` |

## Watch Directories

Configured in the `watch_recordings` node:
- `/home/delorenj/audio/inbox` (primary intake)
- `/home/delorenj/Music` (secondary, catches ad-hoc recordings)

Supported formats: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.mp4`, `.mov`, `.mkv`

Video files need manual audio extraction before intake:
```bash
ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 2 ~/audio/inbox/output.mp3
```

## Pipeline Stages (Bloodbank Events)

1. **`fireflies.transcript.upload`** - File hashed, uploaded to MinIO, presigned URL generated
2. **`fireflies.transcript.ready`** - Transcript fetched from Fireflies API, ready for output

## Webhook Debounce

The `prep_transcript_query` function node debounces progressive Fireflies webhooks using Node-RED flow context:
- Key: `clientReferenceId` (set during upload as `event_id`)
- Timeout: 120 seconds of no new webhooks
- Stores latest `meetingId` per key, fetches transcript only after debounce settles
- Flow context keys: `_webhook_timers`, `_webhook_pending`

## Echobox Ledger

Sidecar API for dedup and job tracking.

- Container: `33god-echobox-ledger` (port 18697)
- Database: PostgreSQL `echobox` on `host.docker.internal:5432`
- Dedup key: SHA256 content hash
- Statuses: `detected -> hashing -> uploading -> uploaded -> transcribing -> ready -> writing -> completed`
- Source: `/home/delorenj/code/33GOD/services/echobox/ledger/`

## RabbitMQ Connection

- Host process (PM2/subscribers): `amqp://delorenj:<password>@localhost:5673/`
- Docker containers: `amqp://delorenj:<password>@rabbitmq:5672/`
- Exchange: `bloodbank.events.v1`
- Queues: `node-red.fireflies.upload`, `node-red.fireflies.ready`

Note: host port is **5673** (mapped from container 5672).

## Common Operations

**Restart pipeline:**
```bash
pm2 restart node-red
```
Subscribers auto-start via Node-RED exec nodes on deploy.

**Manual subscriber restart:**
```bash
bash /home/delorenj/code/33GOD/services/node-red-flow-orchestrator/start-subscribers.sh
```

**Sync project flow to runtime:**
```bash
cp flows/fireflies-bloodbank.json ~/.node-red/flows.json
pm2 restart node-red
```

**Check subscriber health:**
```bash
tail -5 ~/.node-red/logs/subscriber-upload.log
tail -5 ~/.node-red/logs/subscriber-ready.log
```

## Holocene Dashboard

Echobox dashboard at `holocene.delo.sh/services` (proxied via nginx to ledger API at `/api/echobox/*`).
