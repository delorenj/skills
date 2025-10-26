---
name: bloodbank-n8n-event-driven-workflows
description: Use this skill when working on any event driven n8n workflow that subscribes to or publishes 33GOD Bloodbank events. This skill ensures standard conventions are adhered to across all event-driven workflows, with modularity maximized for robust and rapid expansion.
version: 2.0.0
dependencies:
  - n8n
  - RabbitMQ
  - ajv (JSON Schema validation)
references:
  - task-session-manager/docs/EVENT_ARCHITECTURE.md
category: Skill
aliases:
  - Claude Skill
  - claude-skill
  - Bloodbank Event Architecture
  - Task Lifecycle Events
domain: Bloodbank
subdomain: Event-Driven Architecture
tags:
  - n8n
  - event-driven-workflow
  - 33god/bloodbank
  - task-lifecycle
  - rabbitmq
  - event-sourcing
created: 2025-10-22
modified: 2025-01-26
---

# 33GOD Bloodbank Event-Driven Workflows for n8n

## Overview

The Bloodbank event architecture follows a **noun-verb naming convention** for all events:

```
{domain}.{noun}.{verb}
```

**Example**: `task.lifecycle.assigned`
- **Domain**: `task` (system boundary)
- **Noun**: `lifecycle` (entity being acted upon)
- **Verb**: `assigned` (action or state)

## Core Event Types

### Task Lifecycle Events

#### 1. task.lifecycle.assigned
**Purpose**: Request creation of a task execution session

**Routing Key**: `task.lifecycle.assigned`

**JSON Schema**:
```json
{
  "type": "object",
  "required": ["task_id", "working_dir", "agent_type", "correlation_id", "timestamp"],
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique task identifier"
    },
    "working_dir": {
      "type": "string",
      "description": "Absolute path to task working directory"
    },
    "agent_type": {
      "type": "string",
      "enum": ["claude-code", "gemini-cli", "custom"],
      "description": "Type of agent to execute the task"
    },
    "command": {
      "type": "string",
      "description": "Optional command to execute (defaults to agent type)"
    },
    "environment": {
      "type": "object",
      "additionalProperties": { "type": "string" },
      "description": "Environment variables for the session"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "normal", "high", "critical"],
      "default": "normal"
    },
    "correlation_id": {
      "type": "string",
      "description": "Correlation ID for distributed tracing"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "metadata": {
      "type": "object",
      "description": "Additional metadata"
    }
  }
}
```

#### 2. task.lifecycle.started
**Purpose**: Confirm session created and agent launched

**Routing Key**: `task.lifecycle.started`

**JSON Schema**:
```json
{
  "type": "object",
  "required": ["task_id", "session_id", "session_manager", "agent_pid", "started_at", "correlation_id"],
  "properties": {
    "task_id": { "type": "string", "format": "uuid" },
    "session_id": { "type": "string" },
    "session_manager": {
      "type": "string",
      "enum": ["tmux", "zellij"]
    },
    "agent_pid": { "type": "integer" },
    "agent_type": { "type": "string" },
    "working_dir": { "type": "string" },
    "started_at": { "type": "string", "format": "date-time" },
    "correlation_id": { "type": "string" },
    "parent_event_id": { "type": "string" },
    "metadata": { "type": "object" }
  }
}
```

#### 3. task.lifecycle.in_progress
**Purpose**: Report task execution progress updates

**Routing Key**: `task.lifecycle.in_progress`

**JSON Schema**:
```json
{
  "type": "object",
  "required": ["task_id", "progress_percentage", "current_activity", "elapsed_time_seconds", "updated_at"],
  "properties": {
    "task_id": { "type": "string", "format": "uuid" },
    "progress_percentage": { "type": "integer", "minimum": 0, "maximum": 100 },
    "current_activity": { "type": "string" },
    "files_modified": { "type": "array", "items": { "type": "string" } },
    "commands_executed": { "type": "integer" },
    "elapsed_time_seconds": { "type": "integer" },
    "updated_at": { "type": "string", "format": "date-time" },
    "correlation_id": { "type": "string" },
    "parent_event_id": { "type": "string" },
    "metadata": { "type": "object" }
  }
}
```

#### 4. task.lifecycle.completed
**Purpose**: Report successful task completion

**Routing Key**: `task.lifecycle.completed`

**JSON Schema**:
```json
{
  "type": "object",
  "required": ["task_id", "summary", "completed_at", "correlation_id"],
  "properties": {
    "task_id": { "type": "string", "format": "uuid" },
    "summary": { "type": "string" },
    "completed_at": { "type": "string", "format": "date-time" },
    "duration_seconds": { "type": "integer" },
    "files_modified": { "type": "array", "items": { "type": "string" } },
    "correlation_id": { "type": "string" },
    "parent_event_id": { "type": "string" },
    "metadata": { "type": "object" }
  }
}
```

#### 5. task.lifecycle.failed
**Purpose**: Report task or session failure

**Routing Key**: `task.lifecycle.failed`

**JSON Schema**:
```json
{
  "type": "object",
  "required": ["task_id", "reason", "error_details", "failed_at", "correlation_id"],
  "properties": {
    "task_id": { "type": "string", "format": "uuid" },
    "reason": {
      "type": "string",
      "enum": ["session_creation_failed", "agent_crashed", "timeout", "validation_error", "unknown"]
    },
    "error_details": { "type": "string" },
    "failed_at": { "type": "string", "format": "date-time" },
    "correlation_id": { "type": "string" },
    "parent_event_id": { "type": "string" },
    "metadata": { "type": "object" }
  }
}
```

#### 6. task.lifecycle.paused
**Purpose**: Indicate task execution paused

**Routing Key**: `task.lifecycle.paused`

**JSON Schema**:
```json
{
  "type": "object",
  "required": ["task_id", "reason", "paused_at", "correlation_id"],
  "properties": {
    "task_id": { "type": "string", "format": "uuid" },
    "reason": { "type": "string" },
    "paused_at": { "type": "string", "format": "date-time" },
    "correlation_id": { "type": "string" },
    "parent_event_id": { "type": "string" },
    "metadata": { "type": "object" }
  }
}
```

## Event Envelope (Optional)

Events may be wrapped in an envelope for additional routing metadata:

```json
{
  "event_type": "task.lifecycle.assigned",
  "routing_key": "task.lifecycle.assigned",
  "correlation_id": "req-123",
  "timestamp": "2025-01-26T00:00:00Z",
  "payload": {
    // ... actual event data ...
  }
}
```

## n8n Workflow Patterns

### Pattern 1: Consuming Task Events (RabbitMQ Trigger)

**Setup**:
1. Add **RabbitMQ Trigger** node
2. Configure connection to RabbitMQ
3. Set queue name: `task.lifecycle.assigned`
4. Set routing key: `task.lifecycle.assigned`
5. Enable manual acknowledgment

**Validation Node** (Code Node):
```javascript
// Load the schema for the event type
const taskAssignedSchema = {
  type: "object",
  required: ["task_id", "working_dir", "agent_type", "correlation_id", "timestamp"],
  properties: {
    task_id: { type: "string", format: "uuid" },
    working_dir: { type: "string" },
    agent_type: { type: "string", enum: ["claude-code", "gemini-cli", "custom"] },
    correlation_id: { type: "string" },
    timestamp: { type: "string", format: "date-time" }
  }
};

const Ajv = require('ajv');
const addFormats = require('ajv-formats');
const ajv = new Ajv();
addFormats(ajv);

const validate = ajv.compile(taskAssignedSchema);

// Get the incoming event
let event = $input.first().json;

// Handle envelope unwrapping
if (event.event_type && event.payload) {
  event = event.payload;
}

// Validate the event
const isValid = validate(event);

if (!isValid) {
  throw new Error("Event validation failed: " + JSON.stringify(validate.errors));
}

// Return validated event
return [{ json: event }];
```

### Pattern 2: Publishing Task Events (RabbitMQ Node)

**Setup**:
1. Add **Code Node** to build event
2. Add **RabbitMQ** send node
3. Configure exchange: `task.events` (topic)
4. Set routing key based on event type
5. Enable persistent delivery

**Build Event Node** (Code Node):
```javascript
// Build a task.lifecycle.started event
const event = {
  task_id: $json.task_id,
  session_id: $json.session_id,
  session_manager: $json.session_manager || "tmux",
  agent_pid: $json.agent_pid,
  agent_type: $json.agent_type || "claude-code",
  working_dir: $json.working_dir,
  started_at: new Date().toISOString(),
  correlation_id: $json.correlation_id,
  parent_event_id: $json.message_id,
  metadata: $json.metadata || {}
};

// Optional: Wrap in envelope
const envelope = {
  event_type: "task.lifecycle.started",
  routing_key: "task.lifecycle.started",
  correlation_id: event.correlation_id,
  timestamp: event.started_at,
  payload: event
};

return [{ json: envelope }];
```

**RabbitMQ Send Node Configuration**:
- Exchange: `task.events`
- Exchange Type: `topic`
- Routing Key: `{{ $json.routing_key }}`
- Options:
  - Persistent: `true`
  - Content-Type: `application/json`

### Pattern 3: Event Correlation Chain

**Track events across workflow**:

```javascript
// Extract correlation context
const correlationContext = {
  correlation_id: $json.correlation_id,
  task_id: $json.task_id,
  parent_event_id: $execution.id,
  trace: [
    ...($json.metadata?.trace || []),
    {
      workflow_id: $workflow.id,
      execution_id: $execution.id,
      node_name: $node.name,
      timestamp: new Date().toISOString()
    }
  ]
};

// Pass to next event
return [{
  json: {
    ...$json,
    correlation_id: correlationContext.correlation_id,
    parent_event_id: correlationContext.parent_event_id,
    metadata: {
      ...($json.metadata || {}),
      trace: correlationContext.trace
    }
  }
}];
```

### Pattern 4: Error Handling with Failed Events

**Catch errors and publish task.lifecycle.failed**:

```javascript
// In an Error Trigger or IF node checking for errors
const failedEvent = {
  task_id: $json.task_id,
  reason: $json.error?.reason || "unknown",
  error_details: $json.error?.message || JSON.stringify($json.error),
  failed_at: new Date().toISOString(),
  correlation_id: $json.correlation_id,
  parent_event_id: $execution.id,
  metadata: {
    workflow_id: $workflow.id,
    node_name: $json.error?.node || "unknown",
    stack_trace: $json.error?.stack
  }
};

return [{ json: failedEvent }];
```

## RabbitMQ Setup

### Exchange Configuration

```javascript
// Declare the topic exchange (idempotent)
const exchange = {
  name: "task.events",
  type: "topic",
  durable: true,
  autoDelete: false,
  internal: false
};
```

### Queue Configuration

```javascript
// Declare queues for different consumers
const queues = [
  {
    name: "task.session.assigned",
    durable: true,
    exclusive: false,
    autoDelete: false,
    bindings: [
      { routing_key: "task.lifecycle.assigned" }
    ]
  },
  {
    name: "task.lifecycle.monitor",
    durable: true,
    exclusive: false,
    autoDelete: false,
    bindings: [
      { routing_key: "task.lifecycle.*" }  // Subscribe to all lifecycle events
    ]
  },
  {
    name: "task.lifecycle.failures",
    durable: true,
    exclusive: false,
    autoDelete: false,
    bindings: [
      { routing_key: "task.lifecycle.failed" }
    ]
  }
];
```

## Best Practices

### 1. Always Validate Events

```javascript
// Use JSON Schema validation for all incoming events
const Ajv = require('ajv');
const addFormats = require('ajv-formats');
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

const validate = ajv.compile(schema);
if (!validate(event)) {
  // Log validation errors
  console.error("Validation errors:", validate.errors);
  throw new Error("Invalid event schema");
}
```

### 2. Preserve Correlation IDs

```javascript
// Always pass correlation_id through the event chain
const newEvent = {
  ...eventData,
  correlation_id: $json.correlation_id || generateUUID(),
  parent_event_id: $json.message_id || $execution.id
};
```

### 3. Handle Envelopes Gracefully

```javascript
// Support both wrapped and unwrapped events
function unwrapEvent(data) {
  if (data.event_type && data.payload) {
    return data.payload;
  }
  return data;
}

const event = unwrapEvent($input.first().json);
```

### 4. Use Persistent Messages

```javascript
// Always set persistent delivery for important events
// In RabbitMQ node options:
{
  persistent: true,
  deliveryMode: 2,
  contentType: "application/json"
}
```

### 5. Implement Idempotency

```javascript
// Check if event was already processed
const eventId = `${$json.task_id}-${$json.event_type}-${$json.timestamp}`;
const processed = await checkIfProcessed(eventId);

if (processed) {
  console.log("Event already processed, skipping");
  return [];
}

// Process event...

// Mark as processed
await markAsProcessed(eventId);
```

### 6. Error Recovery

```javascript
// Implement retry logic with exponential backoff
const maxRetries = 3;
const retryCount = $json.metadata?.retry_count || 0;

if (retryCount >= maxRetries) {
  // Publish to dead letter queue
  return [{ json: { ...$json, dlq: true } }];
}

// Retry with backoff
const delay = Math.pow(2, retryCount) * 1000;
await sleep(delay);

return [{
  json: {
    ...$json,
    metadata: {
      ...($json.metadata || {}),
      retry_count: retryCount + 1
    }
  }
}];
```

## Common Workflows

### Workflow 1: Task Orchestration Monitor

**Purpose**: Monitor all task lifecycle events and update dashboard

**Nodes**:
1. **RabbitMQ Trigger** → `task.lifecycle.*`
2. **Switch** → Route by event type
3. **Update Dashboard** → Per event type
4. **Log to Database** → Audit trail

### Workflow 2: Task Session Creator

**Purpose**: Create terminal sessions for assigned tasks

**Nodes**:
1. **RabbitMQ Trigger** → `task.lifecycle.assigned`
2. **Validate Event** → Schema validation
3. **HTTP Request** → Call Task Session Manager API
4. **Publish Started/Failed** → Based on result

### Workflow 3: Task Completion Notifier

**Purpose**: Send notifications when tasks complete or fail

**Nodes**:
1. **RabbitMQ Trigger** → `task.lifecycle.{completed,failed}`
2. **Format Message** → Create notification
3. **Slack/Email** → Send notification
4. **Update Metrics** → Track completion rates

### Workflow 4: Progress Aggregator

**Purpose**: Aggregate progress updates and compute overall status

**Nodes**:
1. **RabbitMQ Trigger** → `task.lifecycle.in_progress`
2. **Update State** → Store latest progress
3. **Calculate Overall** → Compute aggregate metrics
4. **Publish Update** → Broadcast to subscribers

## Testing Events

### Test Event Generator (Code Node)

```javascript
// Generate test task.lifecycle.assigned event
const testEvent = {
  task_id: "550e8400-e29b-41d4-a716-446655440000",
  working_dir: "/tmp/test-task",
  agent_type: "claude-code",
  command: "echo 'test'",
  environment: {
    DEBUG: "true"
  },
  priority: "normal",
  correlation_id: "test-" + Date.now(),
  timestamp: new Date().toISOString(),
  metadata: {
    test: true,
    generated_by: "n8n-test-node"
  }
};

return [{ json: testEvent }];
```

## Migration from Old Events

If migrating from existing event structures:

```javascript
// Adapter for old event format
function migrateOldEvent(oldEvent) {
  return {
    task_id: oldEvent.id || generateUUID(),
    working_dir: oldEvent.directory || "/tmp",
    agent_type: oldEvent.agent || "claude-code",
    correlation_id: oldEvent.requestId || generateUUID(),
    timestamp: oldEvent.created_at || new Date().toISOString(),
    metadata: {
      migrated: true,
      original_format: oldEvent
    }
  };
}

const newEvent = migrateOldEvent($json);
```

## References

- **Task Session Manager**: `/task-session-manager/docs/EVENT_ARCHITECTURE.md`
- **Event Types**: `/task-session-manager/pkg/events/types.go`
- **RabbitMQ Documentation**: https://www.rabbitmq.com/
- **n8n Documentation**: https://docs.n8n.io/
- **JSON Schema**: https://json-schema.org/

## Version History

- **2.0.0** (2025-01-26): Incorporated task lifecycle event architecture
- **1.0.0** (2025-10-22): Initial Bloodbank event skill
