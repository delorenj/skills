# Registry Schema (registry.yaml)

## Purpose

The registry serves as the **service catalog** for the 33GOD ecosystem. It documents:
1. All event-consuming services
2. Event producers (Node-RED, services that publish events)
3. Event topology (which services subscribe to which events)
4. Service metadata (status, owner, endpoints)

## File Location

```
/home/delorenj/code/33GOD/services/registry.yaml
```

## Top-Level Structure

```yaml
version: "1.0"

exchange:
  name: "bloodbank.events.v1"
  type: "topic"
  durable: true

services:
  # Service definitions

event_subscriptions:
  # Event → Consumer mappings

topology:
  # Layer-based service organization
```

## Service Definition Schema

### Event Consumer Service

```yaml
services:
  service-name:
    name: "service-name"
    description: "What this service does"
    type: "event-consumer"
    queue_name: "services.domain.queue_name"
    routing_keys:
      - "domain.resource.action"
      - "domain.resource.another"
    produces:  # Optional: events this service publishes
      - "domain.resource.result"
    status: "active | planned | inactive"
    owner: "33GOD"
    tags:
      - "domain"
      - "feature"
    endpoints:  # Optional
      health: "http://localhost:8080/health"
      api: "http://localhost:8080/api/v1"
```

### Event Producer Service

```yaml
services:
  node-red-flow-orchestrator:
    name: "node-red-flow-orchestrator"
    description: "Node-RED workflow orchestration"
    type: "event-producer"  # or "orchestrator"
    status: "active"
    owner: "33GOD"
    tags:
      - "node-red"
      - "orchestration"
    produces:
      - "fireflies.transcript.upload"
      - "fireflies.transcript.ready"
    consumes:  # Optional: for exec node subscribers
      - "fireflies.transcript.upload"
    endpoints:
      ui: "http://localhost:1880"
      webhooks: "http://localhost:1880/webhooks/service-name"
    runtime:  # Optional: deployment info
      type: "pm2"
      config: "~/.node-red/ecosystem.config.js"
```

## Event Subscription Mapping

Maps event types to consuming services:

```yaml
event_subscriptions:
  domain.resource.action:
    - "service-one"
    - "service-two"

  fireflies.transcript.ready:
    - "fireflies-transcript-processor"
    - "fireflies-transcript-rag"
```

**Usage:** Candybar network visualization, service discovery

## Service Topology (Layer Organization)

```yaml
topology:
  # Layer 0: Infrastructure (capture everything)
  infrastructure:
    - "event-store-manager"

  # Layer 1: Event producers
  event_producers:
    - "theboard-producer"

  # Layer 2: External sources
  external_sources:
    - "fireflies"
    - "github"

  # Layer 3: Collectors
  collectors:
    - "llm-collector"
    - "agent-thread-collector"

  # Layer 4: Processors
  processors:
    - "fireflies-transcript-processor"
    - "agent-thread-analytics"

  # Layer 5: Orchestrators
  orchestrators:
    - "theboard-meeting-trigger"

  # Layer 6: Notifiers
  notifiers:
    - "fireflies-transcript-notifier"

  # Layer 7: Error handlers
  error_handlers:
    - "artifact-processor"
```

## Service Types

### event-consumer
Subscribes to events via RabbitMQ, processes them, optionally publishes new events.

**Examples:**
- fireflies-transcript-processor
- agent-feedback-router
- llm-collector

### event-producer
Publishes events to Bloodbank (may not consume events).

**Examples:**
- theboard-producer (FastAPI service publishing events)

### orchestrator
Node-RED or similar orchestration layer handling multi-protocol workflows.

**Examples:**
- node-red-flow-orchestrator

## Service Status Values

- `active` - Running in production
- `planned` - Designed but not implemented
- `inactive` - Temporarily disabled
- `deprecated` - Being phased out

## Queue Naming Convention

```
services.<domain>.<descriptive_name>
```

Examples:
- `services.fireflies.transcript_processor`
- `services.theboard.meeting_trigger`
- `services.agent.feedback_router`

For Node-RED exec node consumers:
```
node-red.<domain>.<descriptive_name>
```

## Routing Key Patterns

### Exact Match
```yaml
routing_keys:
  - "fireflies.transcript.ready"
```

### Wildcard Match
```yaml
routing_keys:
  - "theboard.meeting.#"  # All TheBoard meeting events
  - "*.*.error"           # All error events
```

## Multi-Queue Services (FastStream)

For services listening to multiple queues:

```yaml
services:
  theboard-meeting-trigger:
    type: "event-consumer"
    queue_names:  # Use queue_names (plural) instead of queue_name
      - "services.theboard.meeting_trigger"
      - "services.theboard.feature_brainstorm"
      - "services.theboard.architecture_review"
    routing_keys:
      - "theboard.meeting.trigger"
      - "feature.brainstorm.requested"
      - "architecture.review.needed"
```

## Optional Fields

### Endpoints
```yaml
endpoints:
  health: "http://localhost:8080/health"
  api: "http://localhost:8080/api/v1"
  docs: "http://localhost:8080/docs"
  websocket: "ws://localhost:8080/api/v1/stream"
  ui: "http://localhost:1880"
  webhooks: "http://localhost:1880/webhooks/endpoint"
```

### Runtime
```yaml
runtime:
  type: "pm2 | docker | systemd"
  config: "path/to/config"
  data_dir: "path/to/data"
  flows_source: "path/to/flows"  # For Node-RED
```

### Produces
```yaml
produces:
  - "domain.resource.created"
  - "domain.resource.failed"
```

## Registry Update Workflow

1. **Create service** - Implement Python service or Node-RED flow
2. **Add to registry** - Add service definition under `services:`
3. **Add event mappings** - Add to `event_subscriptions:` for each event consumed
4. **Add to topology** - Place in appropriate layer
5. **Commit** - Git commit with message describing service

## Complete Example

```yaml
services:
  my-new-service:
    name: "my-new-service"
    description: "Processes domain events and publishes results"
    type: "event-consumer"
    queue_name: "services.domain.my_service"
    routing_keys:
      - "domain.resource.created"
      - "domain.resource.updated"
    produces:
      - "domain.resource.processed"
      - "domain.resource.failed"
    status: "active"
    owner: "33GOD"
    tags:
      - "domain"
      - "processing"
    endpoints:
      health: "http://localhost:8080/health"

event_subscriptions:
  domain.resource.created:
    - "my-new-service"
  domain.resource.updated:
    - "my-new-service"

topology:
  processors:
    - "my-new-service"
```

## Best Practices

1. **Be descriptive** - Service descriptions should explain what AND why
2. **Tag appropriately** - Tags enable filtering and discovery
3. **Document endpoints** - Include all HTTP endpoints for monitoring
4. **Status accuracy** - Keep status field up to date
5. **Routing key specificity** - Use specific routing keys, avoid `#` unless necessary
6. **Queue name uniqueness** - Each queue should have a unique, descriptive name
7. **Update topology** - Place services in correct architectural layer
8. **Event subscriptions** - Always update event_subscriptions when adding routing_keys
