# Testing Guide

Testing strategies for 33GOD services.

## Test Structure

```
services/my-service/
├── src/
│   ├── consumer.py
│   ├── config.py
│   └── models.py
├── tests/
│   ├── __init__.py
│   ├── test_consumer.py
│   ├── test_models.py
│   └── conftest.py  # Shared fixtures
└── pyproject.toml
```

## Basic Test Pattern

```python
# tests/test_consumer.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from event_producers.events.base import EventEnvelope, Source, TriggerType
from src.consumer import handle_event, process_event
from src.models import PayloadModel


@pytest.fixture
def sample_envelope():
    """Create a sample EventEnvelope for testing."""
    return EventEnvelope(
        event_id="test-event-123",
        event_type="domain.event.happened",
        timestamp=datetime.now().isoformat(),
        payload={
            "id": "payload-123",
            "data": "test data",
        },
        source=Source(
            service="test-service",
            version="1.0.0",
        ),
        trigger=TriggerType.SYSTEM,
    )


@pytest.fixture
def sample_payload():
    """Create a sample payload model for testing."""
    return PayloadModel(
        id="payload-123",
        data="test data",
    )


@pytest.mark.asyncio
async def test_handle_event_success(sample_envelope):
    """Test successful event handling."""
    # Arrange
    message_dict = sample_envelope.model_dump()

    # Mock the process_event function
    with patch("src.consumer.process_event", new_callable=AsyncMock) as mock_process:
        # Act
        await handle_event(message_dict)

        # Assert
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0][0]
        assert call_args.id == "payload-123"


@pytest.mark.asyncio
async def test_handle_event_validation_error(sample_envelope):
    """Test handling of invalid payload."""
    # Arrange - Create invalid payload
    sample_envelope.payload = {"invalid": "data"}
    message_dict = sample_envelope.model_dump()

    # Act & Assert - Should not raise, but log error
    await handle_event(message_dict)


@pytest.mark.asyncio
async def test_process_event(sample_payload):
    """Test the core processing logic."""
    # Mock external dependencies
    with patch("src.consumer.some_external_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"status": "success"}

        # Act
        await process_event(sample_payload)

        # Assert
        mock_call.assert_called_once_with(sample_payload.data)
```

## Testing with Publisher

Mock the Publisher for services that publish events:

```python
@pytest.mark.asyncio
async def test_publishes_result_event(sample_payload):
    """Test that service publishes result event."""
    with patch("src.consumer.publisher") as mock_publisher:
        mock_publisher.publish_event = AsyncMock()

        # Act
        await process_event(sample_payload)

        # Assert
        mock_publisher.publish_event.assert_called_once()
        call_kwargs = mock_publisher.publish_event.call_args.kwargs

        assert call_kwargs["routing_key"] == "domain.result.created"
        assert "envelope" in call_kwargs
```

## Testing File Operations

For services that write to the Vault:

```python
@pytest.mark.asyncio
async def test_saves_to_vault(sample_payload, tmp_path):
    """Test that service saves file to Vault."""
    # Use tmp_path fixture for temporary directory
    with patch("src.config.settings.vault_path", tmp_path):
        # Act
        await process_event(sample_payload)

        # Assert
        output_file = tmp_path / "expected_output.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "expected content" in content
```

## Mocking External APIs

For services that call external APIs:

```python
@pytest.mark.asyncio
async def test_external_api_call(sample_payload):
    """Test handling of external API calls."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "response"}
        mock_get.return_value = mock_response

        # Act
        await process_event(sample_payload)

        # Assert
        mock_get.assert_called_once()
```

## Testing Error Scenarios

Test error handling paths:

```python
@pytest.mark.asyncio
async def test_handles_processing_error(sample_payload):
    """Test graceful error handling."""
    with patch("src.consumer.some_external_call", side_effect=Exception("API Error")):
        # Should not raise, but log error
        await process_event(sample_payload)


@pytest.mark.asyncio
async def test_handles_file_not_found(sample_payload):
    """Test handling of missing files."""
    with patch("pathlib.Path.read_text", side_effect=FileNotFoundError("Missing file")):
        # Should not crash
        await process_event(sample_payload)
```

## Conftest Fixtures

Share common fixtures in `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
from datetime import datetime
from event_producers.events.base import EventEnvelope, Source, TriggerType


@pytest.fixture
def base_envelope():
    """Base EventEnvelope for all tests."""
    return EventEnvelope(
        event_id="test-event",
        event_type="test.event",
        timestamp=datetime.now().isoformat(),
        payload={},
        source=Source(service="test", version="1.0.0"),
        trigger=TriggerType.SYSTEM,
    )


@pytest.fixture
def mock_publisher():
    """Mock Publisher instance."""
    with patch("src.consumer.publisher") as mock:
        mock.publish_event = AsyncMock()
        yield mock
```

## Running Tests

```bash
# Run all tests
cd services/my-service
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_consumer.py

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/test_consumer.py::test_handle_event_success
```

## Test Coverage Goals

Aim for:
- 80%+ coverage for `src/consumer.py`
- 100% coverage for `src/models.py` (validate all fields)
- Core business logic paths tested
- Error handling paths tested

## Integration Testing

For local integration tests with real RabbitMQ:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_event_flow():
    """Test full event processing with real RabbitMQ (requires running instance)."""
    from event_producers.rabbit import Publisher

    publisher = Publisher()
    await publisher.start()

    try:
        # Publish test event
        envelope = create_test_envelope()
        await publisher.publish_event("test.event", envelope)

        # Wait and verify processing
        await asyncio.sleep(2)
        # Check results...

    finally:
        await publisher.stop()
```

Run integration tests separately:

```bash
# Skip integration tests by default
uv run pytest -m "not integration"

# Run only integration tests
uv run pytest -m integration
```

## Mocking Best Practices

1. **Mock at the boundary**: Mock external calls (API, filesystem, database), not internal functions
2. **Use AsyncMock for async functions**: Ensures proper async handling
3. **Verify call arguments**: Use `assert_called_with()` or inspect `call_args`
4. **Test both success and failure paths**: Ensure error handling works
5. **Use fixtures for reusable test data**: Keep tests DRY
