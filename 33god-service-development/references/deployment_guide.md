# Deployment Guide

Deployment and configuration for 33GOD services.

## Project Structure

```
services/my-service/
├── src/
│   ├── __init__.py
│   ├── consumer.py      # FastStream app
│   ├── config.py        # Settings
│   └── models.py        # Pydantic models
├── tests/
│   └── test_consumer.py
├── pyproject.toml       # Dependencies
├── Dockerfile           # Container definition
├── .env.example         # Example environment vars
└── README.md
```

## Dependencies (pyproject.toml)

```toml
[project]
name = "my-service"
version = "0.1.0"
description = "Service description"
requires-python = ">=3.12"

dependencies = [
    "faststream[rabbit]>=0.5.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    # Add service-specific dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[tool.uv.sources]
bloodbank = { path = "../../bloodbank", editable = true }
```

## Configuration (src/config.py)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    """Service-specific settings."""

    # Service identification
    service_name: str = "my-service"
    service_version: str = "1.0.0"

    # Paths
    vault_path: Path = Path.home() / "DeLoDocs"
    log_level: str = "INFO"

    # Service-specific settings
    max_retries: int = 3
    timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_prefix="MYSERVICE_",  # Environment variable prefix
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
```

## Environment Variables

Create `.env.example` for documentation:

```bash
# Service Configuration
MYSERVICE_SERVICE_NAME=my-service
MYSERVICE_SERVICE_VERSION=1.0.0

# Paths
MYSERVICE_VAULT_PATH=/home/user/DeLoDocs
MYSERVICE_LOG_LEVEL=INFO

# Service-specific
MYSERVICE_MAX_RETRIES=3
MYSERVICE_TIMEOUT_SECONDS=30

# Bloodbank (inherited from bloodbank package)
RABBIT_URL=amqp://guest:guest@localhost:5672/
BLOODBANK_EXCHANGE_NAME=bloodbank.events.v1
```

Users copy to `.env` and customize:

```bash
cp .env.example .env
# Edit .env with actual values
```

## Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./
COPY ../bloodbank ../bloodbank

# Install dependencies
RUN uv pip install --system -e .

# Copy service code
COPY src/ ./src/

# Run FastStream
CMD ["faststream", "run", "src.consumer:app"]
```

## Docker Compose

For local development with RabbitMQ:

```yaml
version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest

  my-service:
    build: .
    depends_on:
      - rabbitmq
    environment:
      RABBIT_URL: amqp://guest:guest@rabbitmq:5672/
      MYSERVICE_VAULT_PATH: /vault
    volumes:
      - ${HOME}/DeLoDocs:/vault
      - ../bloodbank:/app/bloodbank:ro
    restart: unless-stopped
```

## Local Development

### Setup

```bash
cd services/my-service

# Create virtual environment and install deps
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
```

### Running Locally

```bash
# Start RabbitMQ (if not running)
docker compose up -d rabbitmq

# Run service with live reload
uv run faststream run src.consumer:app --reload

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Production Deployment

### Build Container

```bash
cd services/my-service
docker build -t 33god/my-service:latest .
```

### Run Container

```bash
docker run -d \
  --name my-service \
  -e RABBIT_URL=amqp://user:pass@rabbitmq:5672/ \
  -e MYSERVICE_VAULT_PATH=/vault \
  -v /path/to/vault:/vault \
  --restart unless-stopped \
  33god/my-service:latest
```

### Health Checks

For services with HTTP endpoints, add health checks:

```python
# src/consumer.py
from fastapi import FastAPI
from faststream.rabbit.fastapi import RabbitRouter

api = FastAPI()
router = RabbitRouter()

@api.get("/health")
async def health():
    return {"status": "healthy"}

api.include_router(router)
app = router.app  # FastStream app
```

Then in Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1
```

## Logging

Configure structured logging:

```python
# src/consumer.py
import logging
import sys

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
```

For JSON logging in production:

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": settings.service_name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
```

## Monitoring

### Metrics

FastStream provides built-in Prometheus metrics:

```python
from faststream import FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker(
    url=bloodbank_settings.rabbit_url,
    # Enable metrics
    middlewares=[
        PrometheusMiddleware()
    ]
)
```

### Observability

Key metrics to track:
- Message processing rate
- Error rate
- Processing latency
- Queue depth

Use RabbitMQ management UI for queue monitoring:
- http://localhost:15672 (guest/guest)

## Troubleshooting

### Service won't start

Check:
1. RabbitMQ is running: `docker ps | grep rabbitmq`
2. Connection string is correct: `echo $RABBIT_URL`
3. Bloodbank path is correct: `ls ../bloodbank`

### Events not being received

Check:
1. Queue exists in RabbitMQ: Visit management UI
2. Queue binding is correct: Check routing key matches registry
3. Service is running: `docker ps` or check logs

### High memory usage

- Reduce worker count: `--workers 1`
- Check for memory leaks in processing logic
- Monitor with: `docker stats my-service`

## Maintenance

### Updating Dependencies

```bash
# Update all dependencies
uv pip compile pyproject.toml -o requirements.txt
uv pip sync requirements.txt

# Update specific package
uv pip install --upgrade package-name
```

### Database Migrations

If service uses a database:

```bash
# Using Alembic
uv run alembic upgrade head
```

### Graceful Shutdown

FastStream handles SIGTERM gracefully:

```bash
# Send shutdown signal
docker stop my-service

# Force kill if needed
docker kill my-service
```
