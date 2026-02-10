# Bloodbank Event Patterns

## EventEnvelope Structure

All events in 33GOD are wrapped in `EventEnvelope[T]` where `T` is the payload type.

```python
from event_producers.events.base import EventEnvelope, create_envelope, Source, TriggerType

envelope = create_envelope(
    event_type="domain.resource.action",
    payload={"key": "value"},
    source=Source(
        host="service-name",
        type=TriggerType.AGENT,  # or MANUAL, HOOK, FILE_WATCH, SCHEDULED
        app="service-name"
    ),
    correlation_ids=[parent_event_id]  # Optional, for causation tracking
)
```

## Event Naming Convention

```
<domain>.<resource>.<action>
```

### Examples from Registry

```yaml
fireflies.transcript.upload     # Upload initiated
fireflies.transcript.ready      # Transcript available
fireflies.transcript.processed  # Processing complete
fireflies.transcript.failed     # Processing error

agent.thread.prompt             # Agent received prompt
agent.thread.response           # Agent responded
agent.thread.error              # Agent error

artifact.created                # New artifact created
artifact.ingestion.failed       # Artifact ingestion error

theboard.meeting.created        # Meeting started
theboard.meeting.completed      # Meeting finished
```

## Publishing Events

### From Python Service (FastStream)

```python
from event_producers.rabbit import Publisher
from event_producers.events.base import create_envelope, Source, TriggerType

# Initialize publisher
publisher = Publisher()
await publisher.start()

# Create envelope
envelope = create_envelope(
    event_type="artifact.created",
    payload={
        "artifact_type": "transcript",
        "file_path": "/path/to/file.md",
        "source": "fireflies"
    },
    source=Source(
        host="service-name",
        type=TriggerType.AGENT,
        app="service-name"
    )
)

# Publish
await publisher.publish(
    routing_key="artifact.created",
    body=envelope.model_dump(mode="json")
)
```

### From Node-RED

Node-RED uses the `bb` CLI tool via exec nodes:

```javascript
// Node-RED function node: Build envelope
const envelope = {
  event_type: 'fireflies.transcript.upload',
  event_id: generateUUID(),
  timestamp: new Date().toISOString(),
  version: '1.0.0',
  source: {
    host: 'node-red',
    type: 'file_watch',
    app: 'node-red'
  },
  correlation_ids: [],
  payload: {
    media_file: presignedUrl,
    title: fileName,
    created_at: new Date().toISOString()
  }
};

// Write envelope to file
msg.payload = JSON.stringify(envelope);
msg.filename = `/tmp/event-${envelope.event_id}.json`;
return msg;
```

Then execute:
```bash
bb publish <routing-key> --envelope-file <path>
```

## Consuming Events

### Python Service (FastStream)

```python
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue, ExchangeType
from event_producers.config import settings
from event_producers.events.base import EventEnvelope

broker = RabbitBroker(settings.rabbit_url)
app = FastStream(broker)

@broker.subscriber(
    queue=RabbitQueue(
        name="services.domain.queue_name",
        routing_key="domain.resource.action",
        durable=True,
    ),
    exchange=RabbitExchange(
        name=settings.exchange_name,  # bloodbank.events.v1
        type=ExchangeType.TOPIC,
        durable=True,
    ),
)
async def handle_event(message_dict: Dict[str, Any]):
    # Unwrap envelope
    envelope = EventEnvelope(**message_dict)

    # Parse payload
    payload = MyPayloadModel.model_validate(envelope.payload)

    # Process event
    await process(payload)
```

### Node-RED (Exec Subscriber)

```javascript
// Exec node command:
${SCRIPTS_DIR}/.venv/bin/python -u ${SCRIPTS_DIR}/bloodbank_subscribe.py \
  --routing-key domain.resource.action \
  --queue node-red.domain.queue_name
```

Output is streamed as JSON envelopes, one per line.

## Correlation Tracking

Track causation chains across events:

```python
# Parent event
parent_envelope = create_envelope(
    event_type="fireflies.transcript.upload",
    payload={...},
    source=Source(...)
)

# Child event references parent
child_envelope = create_envelope(
    event_type="fireflies.transcript.ready",
    payload={...},
    source=Source(...),
    correlation_ids=[parent_envelope.event_id]  # Causation link
)
```

## Event Payload Patterns

### Resource Created/Updated

```python
{
    "id": "resource-123",
    "resource_type": "transcript",
    "created_at": "2026-01-20T12:00:00Z",
    "metadata": {
        "title": "Meeting Notes",
        "source": "fireflies"
    }
}
```

### Resource Failed

```python
{
    "resource_id": "resource-123",
    "error_type": "validation_error",
    "error_message": "Invalid transcript format",
    "retry_count": 2
}
```

### Artifact Created

```python
{
    "artifact_type": "transcript | document | image | data",
    "source": "fireflies | manual | agent",
    "file_path": "/absolute/path/to/artifact",
    "metadata": {
        "title": "Artifact Title",
        "created_at": "2026-01-20T12:00:00Z"
    }
}
```

## Exchange Configuration

All events publish to the Bloodbank exchange:

```yaml
exchange:
  name: "bloodbank.events.v1"
  type: "topic"
  durable: true
```

Topic routing allows wildcard subscriptions:
- `fireflies.transcript.*` - All Fireflies transcript events
- `*.*.ready` - All "ready" events across domains
- `#` - All events (use sparingly)

## Best Practices

1. **Use typed payloads** - Define Pydantic models for payload validation
2. **Include correlation IDs** - Track causation chains for debugging
3. **Make events immutable** - Never modify event content after publishing
4. **Use descriptive routing keys** - Follow `domain.resource.action` convention
5. **Version payloads** - Add optional fields for backward compatibility
6. **Log event IDs** - Include `event_id` in all logs for traceability
7. **Idempotent consumers** - Handle duplicate events gracefully
8. **Publish after persistence** - Only publish events after successful database writes
