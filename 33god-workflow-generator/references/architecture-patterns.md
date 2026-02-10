# 33GOD Architecture Patterns

## Core Principle: Separation of Concerns

**Services are islands, orchestrators are bridges. Bridges don't care what they're connecting.**

### Service Type Decision Matrix

| Workflow Characteristics | Tool Choice | Rationale |
|--------------------------|-------------|-----------|
| 1-2 steps, single protocol | Watchdog + Python | Simple adapter, no orchestration needed |
| 3-4 steps, minimal branching | FastAPI endpoint | Single protocol, minimal logic |
| 5+ steps, multiple protocols, branching | Node-RED | Multi-protocol orchestration with visual debugging |
| Heavy computation, domain logic | Python service | Testable, type-safe, version controlled |

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│ External Sources (Webhooks, File Watchers, APIs)   │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ Orchestration Layer (Node-RED)                      │
│ • Multi-protocol coordination                       │
│ • Conditional routing                               │
│ • Protocol translation (HTTP ↔ RabbitMQ ↔ S3)      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ Event Bus (Bloodbank/RabbitMQ)                      │
│ • Topic exchange: bloodbank.events.v1               │
│ • Routing keys: domain.resource.action             │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ Domain Services (Python/FastAPI/FastStream)        │
│ • Business logic                                    │
│ • Data transformation                               │
│ • Persistence                                       │
│ • Event publishing                                  │
└─────────────────────────────────────────────────────┘
```

## When to Use Node-RED

Node-RED is justified when orchestrating **multi-step, multi-protocol workflows with conditional logic**.

### Node-RED Use Cases

✅ **Good:** Complex orchestration (5+ steps, 3+ protocols)
- Filesystem → ffmpeg → MinIO → Fireflies API → RabbitMQ
- Webhook → API call → Transform → Conditional route → Queue + DB

❌ **Bad:** Simple adapters (1-2 steps)
- File watch → Queue (use Watchdog)
- Webhook → Transform → Queue (use FastAPI)

### Node-RED Value Proposition

1. **Visual debugging** - Inspect message payloads at each step
2. **Runtime modification** - Change flows without redeploying
3. **Multi-protocol integration** - Filesystem + HTTP + MQTT + RabbitMQ
4. **Built-in patterns** - Retry, circuit breaker, rate limiting

## When to Use Python Services

Python services handle **domain logic, data transformation, and business rules**.

### Python Service Use Cases

✅ **Always:**
- Data validation (Pydantic models)
- Business logic (transcript formatting, RAG ingestion)
- Persistence (database writes, file creation)
- Event publishing (domain events)

❌ **Never:**
- Protocol translation (Node-RED handles this)
- Simple file watching (Watchdog handles this)

## Event-Driven Patterns

### Event Naming Convention

```
<domain>.<resource>.<action>
```

Examples:
- `fireflies.transcript.upload`
- `fireflies.transcript.ready`
- `artifact.created`
- `agent.feedback.requested`

### Service Registration Pattern

Services are either:
1. **Event Producers** - Publish events (Node-RED, Python services)
2. **Event Consumers** - Subscribe to events (Python services via FastStream)

**Principle:** Domain services own domain events. Orchestration services are domain-agnostic.

Example:
- ✅ Fireflies service produces `fireflies.transcript.ready`
- ✅ Node-RED produces generic `file.detected` events
- ❌ Node-RED should NOT produce `fireflies.transcript.upload` (domain-specific)

### Decoupling via Configuration

Node-RED orchestration should be **configuration-driven**, not service-aware:

```yaml
# Bad: Service-aware
node-red-fireflies-orchestrator:
  description: "Handles Fireflies transcripts"

# Good: Configuration-driven
node-red-orchestrator:
  description: "File watching and webhook bridging"
  config:
    watch_dir: "/home/user/audio/inbox"
    routing_key: "fireflies.transcript.upload"
```

## Service Structure

### Python Service (FastStream Consumer)

```
service-name/
├── src/
│   ├── __init__.py
│   ├── consumer.py      # FastStream subscriber
│   ├── models.py        # Pydantic models
│   └── config.py        # Settings (vault_path, etc.)
├── tests/
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Node-RED Orchestrator

```
node-red-flow-orchestrator/
├── flows/
│   └── workflow-name.json
├── scripts/
│   ├── .venv/           # Python virtualenv for exec nodes
│   └── helper_script.py
├── mise.toml
└── README.md
```

## Architectural Trade-offs

### Control vs. Convenience

**Watchdog + Python:**
- ✅ Full control, version controlled, testable
- ❌ More code to write and maintain

**Node-RED:**
- ✅ Visual debugging, runtime modification, less code
- ❌ JSON flows harder to diff, requires UI access

**Decision:** Use Node-RED when multi-protocol orchestration justifies the trade-off.

### Stateless vs. Stateful Services

**Stateless (preferred):**
- Event consumers process events and publish new events
- No persistent connections
- Horizontal scaling

**Stateful (when necessary):**
- Long-running connections (WebSockets, file watchers)
- In-memory caching
- Document justification in registry.yaml

## Anti-Patterns

### ❌ Domain Logic in Node-RED

**Bad:**
```javascript
// Node-RED function node
const transcript = msg.payload;
const markdown = formatTranscript(transcript); // Domain logic
```

**Good:**
```python
# Python service
async def process_transcript(data: TranscriptData):
    markdown = _format_markdown(data)  # Domain logic in Python
```

### ❌ Service-Aware Orchestration

**Bad:**
```yaml
node-red-fireflies-handler:
  produces:
    - "fireflies.transcript.upload"
    - "fireflies.transcript.ready"
```

**Good:**
```yaml
node-red-orchestrator:
  capabilities:
    - "file-watch"
    - "webhook-bridge"
  # Domain events configured at runtime
```

### ❌ Duplicated Processing

**Bad:**
- Node-RED Tab 4 writes transcripts to CSV/MD
- Python service also writes transcripts to MD
- Two sources of truth, inconsistent formatting

**Good:**
- Node-RED publishes `fireflies.transcript.ready` event
- Python service handles ALL transcript processing
- Single source of truth

## Summary

- **Node-RED:** Multi-protocol orchestration (5+ steps, 3+ protocols)
- **Python Services:** Domain logic, validation, persistence
- **Watchdog:** Simple filesystem → queue adapters
- **Event Bus:** Decoupling layer, topic-based routing
- **Registry:** Service catalog and event topology documentation
