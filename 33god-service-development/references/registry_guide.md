# Registry Guide

The registry at `/home/delorenj/code/33GOD/services/registry.yaml` defines all services in the 33GOD ecosystem.

## Registry Schema

```yaml
version: "1.0"

exchange:
  name: "bloodbank.events.v1"
  type: "topic"
  durable: true

services:
  service-name:
    name: "service-name"
    description: "Brief service description"
    type: "event-consumer|event-producer|hybrid"
    queue_name: "service_queue_name"         # For consumers
    queue_names: ["queue1", "queue2"]        # For multi-queue consumers
    routing_keys:
      - "routing.key.pattern"
    produces:                                # Events this service publishes
      - "event.type"
    consumes:                                # Events this service listens to
      - "event.type"
    status: "active|planned|deprecated"
    owner: "33GOD|TeamName"
    tags:
      - "category"
      - "domain"
    endpoints:                               # Optional API endpoints
      api: "http://localhost:8080/api/v1"
      health: "http://localhost:8080/health"
      docs: "http://localhost:8080/docs"

event_subscriptions:
  routing.key.pattern:
    - "consumer-service-1"
    - "consumer-service-2"

topology:
  layer_name:
    - "service-name"
```

## Registry Entry Examples

### Event Consumer (Single Queue)

```yaml
fireflies-transcript-processor:
  name: "fireflies-transcript-processor"
  description: "Processes Fireflies transcript events, saves to DeLoDocs"
  type: "event-consumer"
  queue_name: "services.fireflies.transcript_processor"
  routing_keys:
    - "fireflies.transcript.ready"
  produces:
    - "artifact.created"
  status: "active"
  owner: "33GOD"
  tags:
    - "transcript"
    - "fireflies"
```

### Event Consumer (Multi-Queue)

```yaml
theboard-meeting-trigger:
  name: "theboard-meeting-trigger"
  description: "Creates TheBoard meetings from ecosystem trigger events"
  type: "event-consumer"
  queue_names:
    - "services.theboard.meeting_trigger"
    - "services.theboard.feature_brainstorm"
    - "services.theboard.architecture_review"
  routing_keys:
    - "theboard.meeting.trigger"
    - "feature.brainstorm.requested"
    - "architecture.review.needed"
  status: "active"
  owner: "33GOD"
  tags:
    - "theboard"
    - "trigger"
    - "faststream"
```

### Event Producer

```yaml
theboard-producer:
  name: "theboard-producer"
  description: "Multi-agent brainstorming system (event producer)"
  type: "event-producer"
  status: "active"
  owner: "33GOD"
  tags:
    - "theboard"
    - "brainstorming"
    - "producer"
  produces:
    - "theboard.meeting.created"
    - "theboard.meeting.started"
    - "theboard.meeting.completed"
  endpoints:
    health: "http://localhost:8000/health"
    docs: "http://localhost:8000/docs"
```

### Infrastructure Service (All Events)

```yaml
event-store-manager:
  name: "event-store-manager"
  description: "Persists all Bloodbank events to PostgreSQL"
  type: "event-consumer"
  queue_name: "event_store_manager_queue"
  routing_keys:
    - "#"  # Subscribe to ALL events
  produces:
    - "event_store.event.persisted"
    - "event_store.event.failed"
  status: "planned"
  owner: "33GOD"
  tags:
    - "infrastructure"
    - "persistence"
    - "postgresql"
  endpoints:
    api: "http://localhost:8080/api/v1"
    health: "http://localhost:8080/health"
```

## Topology Layers

Services are organized into logical layers for visualization in Candybar:

- **infrastructure**: Foundational services (event store, logging)
- **event_producers**: Active services that generate events
- **external_sources**: External systems (Fireflies, GitHub webhooks)
- **collectors**: Services that gather telemetry
- **processors**: Core business logic processors
- **orchestrators**: Workflow coordination services
- **notifiers**: Notification and integration services
- **error_handlers**: Error processing services

Place your service in the appropriate layer in the `topology` section.

## Event Subscriptions Mapping

For every routing key, list all consumers:

```yaml
event_subscriptions:
  fireflies.transcript.ready:
    - "fireflies-transcript-processor"
    - "fireflies-transcript-rag"

  llm.response:
    - "llm-collector"
    - "llm-cost-calculator"
```

This mapping is used by Candybar to visualize event flow.

## Naming Conventions

- **Service names**: `kebab-case` (e.g., `fireflies-transcript-processor`)
- **Queue names**: `snake_case` with optional namespace prefix (e.g., `services.fireflies.transcript_processor`)
- **Routing keys**: Hierarchical dot notation (e.g., `domain.entity.action`)
- **Event types**: Same as routing keys (e.g., `fireflies.transcript.ready`)
