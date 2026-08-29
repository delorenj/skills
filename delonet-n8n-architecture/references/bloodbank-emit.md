# Emitting bloodbank events from n8n

Read this when a workflow needs to publish a pipeline lifecycle event. This file
covers the **n8n-side wiring**; the authoritative envelope/schema/subject contract
lives in `bloodbank-integration` — do not duplicate or diverge from it here.

## Transport: which path from n8n?

This section is for events **originated by workflow execution**, such as
`audio.transcription.completed`. External Plane ingress is a different boundary:
the signed request enters the active `Plane → Bloodbank` workflow, the custom
node verifies the raw-body HMAC and normalizes provider data, then publishes the
canonical event NATS-direct. See `plane-webhook-ingress.md`; do not route Plane
through Bloodbank HTTP `/event`.

n8n runs as a **PM2 host process on `:5678` with no Dapr sidecar**, and NATS is
reachable on the host at `127.0.0.1:4222`. **Publish NATS-direct — do NOT use the
bloodbank HTTP ingress for pipeline events.**

- **NATS-direct (the correct path).** PUB the CloudEvents envelope to subject
  `bloodbank.evt.<domain>.<entity>.<action>` — the path the `event-toaster`
  and every JetStream consumer actually see. On the host this is a dependency-free
  stdlib-TCP publish; use the **`bb-emit` CLI** (`~/.local/bin/bb-emit`), which reads
  the `data` JSON on stdin and derives the envelope, subject, `ordering_key`, and a
  deterministic `correlationid` from `data.transcription_id`. From n8n: an
  `Execute Command` node piping the base64-decoded `data` into
  `bb-emit --type bloodbank.<domain>.<entity>.<action>`. bb-emit **rejects** a
  5-token `bloodbank.v1.*` type and exits 1 — it is not rewritten for you, and
  it now runs the finished envelope through `core/validate.assert_contract`
  before publishing, so a contract violation exits 1 instead of reaching NATS.
- **Do NOT use HTTP `/publish` or `/event` for pipeline events.** Those hit the
  **v2 RabbitMQ exchange**, and the v3 NATS catch-all (`event-toaster` → ntfy) does
  **not** see RabbitMQ-only events. HTTP is only for genuine v2 fan-out or when
  there is truly no path to NATS.
- **Dapr `/publish`** is unavailable (no sidecar).

The custom `n8n-nodes-bloodbank` node (→ node-catalog) should wrap exactly what
`bb-emit` does: pick a defined event, build + validate the envelope, PUB to the
bound subject. `bb-emit` is its host-side seed.

## Subject binding (load-bearing)

The NATS subject is the envelope's `type` with `evt` inserted after `bloodbank`:

```
type    : bloodbank.audio.transcription.completed
subject : bloodbank.evt.audio.transcription.completed      (evt=event, cmd=command, rpy=reply)
```

Never publish to a subject that doesn't match the envelope's `type`.

**There is no contract-version token.** The type is 4 tokens and the subject is
5; a `bloodbank.v1.*` type or a `bloodbank.evt.v1.*` subject is the retired
shape. `bb-emit` refuses a 5-token `--type` outright (exit 1) rather than
rewriting it, so a stale caller fails loudly instead of publishing where nothing
is bound. The `.v1` that survives is the **schema revision** in `schemaref`
(`bloodbank.<domain>.<entity>.<action>.v<n>`) — a different axis. See
bloodbank `docs/event-naming.md` §3.1 and §13.

## The audio events already exist — use them verbatim

Defined under `bloodbank/schemas/bloodbank/audio/`:
`file.received`, `transcription.start`, `transcription.started`,
`transcription.completed`, `transcription.failed`. Emit these; do not invent new
audio events without adding the schema first.

## Envelope shape (illustrative — schema is authoritative)

CloudEvents 1.0 + the 33GOD extension fields. For `audio.transcription.completed`:

`kind`, `actor` and `ordering_key` are not optional garnish — `assert_contract`
lists them in `REQUIRED_EVENT_FIELDS`, and `actor` needs a non-empty `type` and
`agent_id`. NATS core PUB validates nothing, so an envelope missing `actor` is
accepted by the bus and lands in Candystore with `actor IS NULL`, invisible to
every `actor->>'cli'` / `actor->>'agent_id'` read side. bb-emit fills it in for
you (`--actor-type` / `--actor-id` / `--actor`); a hand-built envelope must not
forget it.

```json
{
  "specversion": "1.0",
  "type": "bloodbank.audio.transcription.completed",
  "source": "n8n/inbox-transcribe",
  "subject": "bloodbank.evt.audio.transcription.completed",
  "id": "{{ $execution.id }}",
  "time": "{{ $now.toISO() }}",
  "datacontenttype": "application/json",
  "producer": "n8n",
  "service": "inbox-transcribe",
  "domain": "audio",
  "schemaref": "bloodbank.audio.transcription.completed.v1",
  "correlationid": "{{ $json.sourcePath }}",
  "kind": "event",
  "actor": {
    "type": "service",
    "agent_id": "bloodbank.service.inbox-transcribe",
    "cli": null,
    "provider": null,
    "model": null
  },
  "ordering_key": "transcription:{{ $json.sourcePath }}",
  "data": {
    "sourcePath": "{{ $json.sourcePath }}",
    "s3Uri": "{{ $json.s3Uri }}",
    "mdPath": "{{ $json.mdPath }}",
    "model": "{{ $json.model }}",
    "durationSec": "{{ $json.duration }}",
    "language": "{{ $json.lang }}",
    "speakers": "{{ $json.speakers }}"
  }
}
```

Build `data` to match the schema's `data` object exactly — pull the real field
names from `transcription.completed.json`, don't trust this sketch. Use one
stable `correlationid` (the source path or a run id) across `started` → `completed`
/`failed` so consumers can stitch the lifecycle together.

## Emit at the lifecycle boundaries

- `audio.transcription.started` — after the file is parsed, before/around archive.
- `audio.transcription.completed` — after the transcript is written and delivered.
- `audio.transcription.failed` — on the transcribe node's error output; include the
  failing stage and message. Wire this from the error branch, not a catch-all.

## Verify it actually landed

`bloodbank-event-toaster` subscribes to `bloodbank.evt.>` and forwards every
envelope to `https://ntfy.delo.sh/bloodbank`. Watch that topic while test-firing —
if your event doesn't appear there, it never reached NATS. This is also *why* a
direct ntfy node is redundant: the toaster already gives you the ping.
