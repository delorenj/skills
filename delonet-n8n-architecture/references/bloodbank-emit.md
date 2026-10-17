# Emitting bloodbank events from n8n

Read this when a workflow needs to publish a pipeline lifecycle event. This file
covers the **n8n-side wiring**; the authoritative envelope/schema/subject contract
lives in `bloodbank-integration` — do not duplicate or diverge from it here.

## Transport: which path from n8n?

This section is for events **originated by workflow execution** — outcomes of
work the workflow itself owns. One whole domain is off-limits here: the **Wax
audio lifecycle is owned by Wax**, which emits its own `bloodbank.audio.*`
events as the pipeline owner; see "Wax audio events" below before wiring
anything audio. External Plane ingress is a different boundary:
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
  `correlationid` from the data. From n8n: an
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

The custom `n8n-nodes-bloodbank` **Bloodbank** node (→ node-catalog) does exactly
what `bb-emit` does in-process: pick a defined event from the generated dropdown,
build + validate the envelope, PUB to the bound subject. Prefer it; `bb-emit`
behind an Execute Command is the transitional fallback.

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

## Wax audio events — consume, never synthesize

The audio lifecycle schemas (`bloodbank/schemas/bloodbank/audio/`:
`file.received`, `transcription.start`, `transcription.started`,
`transcription.completed`, `transcription.failed`) are **emitted by Wax**, the
pipeline owner, not by n8n. A workflow cannot truthfully report capture,
archival, transcription, or pass state it does not own — hand-building an
`audio.*` envelope from workflow data fabricates the record. A workflow that
needs to react to the audio lifecycle (toast on completion, file a ticket per
`intake.detected`, …) **subscribes** with a Bloodbank Trigger node on the
matching subject. Schema changes or additions go through `bloodbank-integration`;
operating the emitting pipeline is `wax-pipeline` / HeyMa's Wax docs.

## Envelope shape (illustrative — schema is authoritative)

CloudEvents 1.0 + the 33GOD extension fields, for any event your workflow owns:

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
  "type": "bloodbank.<domain>.<entity>.<action>",
  "source": "n8n/<workflow-slug>",
  "subject": "bloodbank.evt.<domain>.<entity>.<action>",
  "id": "{{ $execution.id }}",
  "time": "{{ $now.toISO() }}",
  "datacontenttype": "application/json",
  "producer": "n8n",
  "service": "<workflow-slug>",
  "domain": "<domain>",
  "schemaref": "bloodbank.<domain>.<entity>.<action>.v<n>",
  "correlationid": "<one stable id for the whole lifecycle>",
  "kind": "event",
  "actor": {
    "type": "service",
    "agent_id": "bloodbank.service.<workflow-slug>",
    "cli": null,
    "provider": null,
    "model": null
  },
  "ordering_key": "<entity>:<stable key>",
  "data": { "…": "fields from the event's schema file, exactly" }
}
```

Build `data` to match the schema's `data` object exactly — pull the real field
names from the event's schema JSON, don't trust this sketch. Use one
stable `correlationid` (a source path or a run id) across `started` → `completed`
/`failed` so consumers can stitch the lifecycle together.

## Emit at the boundaries of work the workflow owns

Emit when the workflow itself completes or fails a unit of work it owns —
`started` when work begins, `completed` when its artifact is durably written,
`failed` from the error branch (not a catch-all) with the failing stage and
message. The same boundaries inside another system (Wax audio, Plane ingress)
are that system's to emit — subscribe instead of synthesizing.

## Verify it actually landed

`bloodbank-event-toaster` subscribes to `bloodbank.evt.>` and logs one line per
non-muted event (`toasted:`, `digested:` or `rate-limited:`) in
`docker logs bloodbank-event-toaster`; a toast on `https://ntfy.delo.sh/bloodbank`
is best-effort. No log line means the event never reached NATS; the Candystore
row (`GET http://127.0.0.1:8683/events`) is the durable proof. This is also *why*
a direct ntfy node is redundant for a pipeline event.
