# FastStream Implementation Patterns

33GOD services use FastStream for event consumption (per ADR-0002). This guide covers the standard patterns.

## Basic Consumer Structure

```python
"""
Service Name - FastStream Consumer

Subscribes to routing.key.pattern events and processes them.
"""

import logging
from typing import Any, Dict

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue, ExchangeType

from event_producers.config import settings as bloodbank_settings
from event_producers.events.base import EventEnvelope
from event_producers.rabbit import Publisher

from .config import settings
from .models import PayloadModel

logger = logging.getLogger(__name__)

# Initialize broker and FastStream app
broker = RabbitBroker(bloodbank_settings.rabbit_url)
app = FastStream(broker)

# Initialize publisher for outgoing events
publisher = Publisher()


@app.after_startup
async def startup():
    """Initialize on app startup."""
    await publisher.start()
    logger.info("Service started")


@app.after_shutdown
async def shutdown():
    """Cleanup on app shutdown."""
    await publisher.stop()
    logger.info("Service shutdown")


@broker.subscriber(
    queue=RabbitQueue(
        name="service_queue_name",
        routing_key="routing.key.pattern",
        durable=True,
    ),
    exchange=RabbitExchange(
        name=bloodbank_settings.exchange_name,
        type=ExchangeType.TOPIC,
        durable=True,
    ),
)
async def handle_event(message_dict: Dict[str, Any]):
    """
    Handle routing.key.pattern events.

    Unwraps EventEnvelope, processes payload, performs work.
    Follows ADR-0002: explicit envelope unwrapping pattern.
    """
    # Unwrap EventEnvelope
    envelope = EventEnvelope(**message_dict)

    logger.info(
        "Received event: %s (correlation: %s)",
        envelope.event_type,
        envelope.event_id,
    )

    try:
        # Parse payload into Pydantic model
        data = PayloadModel.model_validate(envelope.payload)

        # Process the event
        await process_event(data)

        logger.info("Successfully processed: %s", data.id)

    except Exception as e:
        logger.error(
            "Error processing event: %s",
            e,
            exc_info=True,
        )
        # Optional: publish failure event
        # await publish_failure_event(envelope, str(e))


async def process_event(data: PayloadModel):
    """Business logic for event processing."""
    # Your processing logic here
    pass
```

## Multi-Queue Consumer

For services that listen to multiple queues (different routing keys with separate queues):

```python
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue, ExchangeType

broker = RabbitBroker(bloodbank_settings.rabbit_url)
app = FastStream(broker)

exchange = RabbitExchange(
    name=bloodbank_settings.exchange_name,
    type=ExchangeType.TOPIC,
    durable=True,
)

@broker.subscriber(
    queue=RabbitQueue(
        name="services.domain.queue1",
        routing_key="domain.event1",
        durable=True,
    ),
    exchange=exchange,
)
async def handle_event1(message_dict: Dict[str, Any]):
    envelope = EventEnvelope(**message_dict)
    # Handle event1
    pass

@broker.subscriber(
    queue=RabbitQueue(
        name="services.domain.queue2",
        routing_key="domain.event2",
        durable=True,
    ),
    exchange=exchange,
)
async def handle_event2(message_dict: Dict[str, Any]):
    envelope = EventEnvelope(**message_dict)
    # Handle event2
    pass
```

## Publishing Events

To publish events back to Bloodbank:

```python
from event_producers.rabbit import Publisher
from event_producers.events.base import create_envelope, Source, TriggerType

publisher = Publisher()

async def publish_result_event(data: Any):
    """Publish a result event to Bloodbank."""
    envelope = create_envelope(
        event_type="domain.result.created",
        payload=data,
        source=Source(
            service="my-service-name",
            version="1.0.0",
        ),
        trigger=TriggerType.SYSTEM,
    )

    await publisher.publish_event(
        routing_key="domain.result.created",
        envelope=envelope,
    )
```

## EventEnvelope Structure

All Bloodbank events are wrapped in EventEnvelope:

```python
from event_producers.events.base import EventEnvelope

# EventEnvelope fields:
envelope = EventEnvelope(
    event_id="uuid",           # Unique event ID
    event_type="routing.key",  # Event type (same as routing key)
    timestamp="ISO datetime",   # Event creation time
    payload={...},             # Event data (dict)
    source={...},              # Source metadata
    trigger="user|system|scheduled",
    correlation_id="uuid",     # Optional: chain events
)
```

## Payload Models

Define Pydantic models for type safety:

```python
# src/models.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TranscriptData(BaseModel):
    """Fireflies transcript payload."""
    transcript_id: str = Field(..., description="Fireflies transcript ID")
    title: str = Field(..., description="Meeting title")
    date: datetime = Field(..., description="Meeting date")
    transcript_url: str = Field(..., description="URL to full transcript")
    summary: Optional[str] = Field(None, description="Meeting summary")

    class Config:
        json_schema_extra = {
            "example": {
                "transcript_id": "abc123",
                "title": "Sprint Planning",
                "date": "2025-01-23T10:00:00Z",
                "transcript_url": "https://fireflies.ai/...",
                "summary": "Discussed Q1 roadmap",
            }
        }
```

## Configuration

Use Pydantic BaseSettings for configuration:

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    """Service-specific settings."""
    vault_path: Path = Path.home() / "DeLoDocs"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="SERVICE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
```

## Running the Service

```bash
# Development
uv run faststream run src.consumer:app

# Production with workers
uv run faststream run src.consumer:app --workers 4

# With live reload
uv run faststream run src.consumer:app --reload
```

## Error Handling

Follow these patterns for robust error handling:

```python
@broker.subscriber(...)
async def handle_event(message_dict: Dict[str, Any]):
    envelope = EventEnvelope(**message_dict)

    try:
        data = PayloadModel.model_validate(envelope.payload)
        await process_event(data)

    except ValidationError as e:
        # Payload validation failed
        logger.error("Invalid payload: %s", e, exc_info=True)
        await publish_validation_error(envelope, e)

    except FileNotFoundError as e:
        # Expected error - log and continue
        logger.warning("File not found: %s", e)

    except Exception as e:
        # Unexpected error - log with full trace
        logger.error(
            "Unexpected error processing %s: %s",
            envelope.event_type,
            e,
            exc_info=True,
        )
        await publish_failure_event(envelope, e)
```

## Logging

Use structured logging with correlation IDs:

```python
logger.info(
    "Processing event",
    extra={
        "event_id": envelope.event_id,
        "event_type": envelope.event_type,
        "correlation_id": envelope.correlation_id,
    }
)
```

## Legacy Pattern (Deprecated)

Old services used `EventConsumer` base class. Do NOT use this pattern for new services:

```python
# DEPRECATED - Do not use
from services.base import EventConsumer

class MyConsumer(EventConsumer):
    queue_name = "my_queue"
    routing_keys = ["my.routing.key"]

    @EventConsumer.event_handler("my.routing.key")
    async def handle_event(self, envelope: EventEnvelope):
        pass
```

Migrate to FastStream pattern shown above.
