# Docker & Container Patterns

## Stack Organization Philosophy

**Principle:** Domain-based organization for services, using docker-compose as the primary orchestration tool.

**Base Directory:** `~/docker/stacks/`

## Standard Stack Structure

```
~/docker/stacks/
├── ai/                          # AI/ML services and tools
│   ├── firecrawl/
│   ├── dify/
│   ├── qdrant/
│   ├── weaviate/
│   └── letta/
├── monitoring/                  # Observability stack
│   ├── grafana/
│   ├── prometheus/
│   ├── loki/
│   └── glances/
├── databases/                   # Data persistence layer
│   ├── postgres/
│   ├── mysql/
│   ├── redis/
│   └── neo4j/
├── utilities/                   # Infrastructure tools
│   ├── portainer/
│   ├── traefik/
│   ├── watchtower/
│   └── rustdesk-server/
└── development/                 # Dev-specific services
    ├── openhands/
    └── sandbox-environments/
```

## Docker Compose Patterns

### Standard Service Definition

```yaml
version: '3.8'

services:
  service-name:
    image: owner/image:tag
    container_name: descriptive-name
    restart: unless-stopped
    environment:
      - ENV_VAR=value
    volumes:
      - /host/path:/container/path
      - named-volume:/data
    ports:
      - "host-port:container-port"
    networks:
      - network-name
    depends_on:
      - dependency-service

networks:
  network-name:
    driver: bridge

volumes:
  named-volume:
```

### Common Patterns

**1. Service with Portainer Management**
```yaml
services:
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - portainer_data:/data
    ports:
      - "9000:9000"
```

**2. AI Service Pattern (with runtime container)**
```yaml
services:
  openhands:
    image: docker.all-hands.dev/all-hands-ai/openhands:0.12
    container_name: openhands-app
    restart: unless-stopped
    environment:
      - SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.12-nikolaik
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "3000:3000"
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

**3. Database Service Pattern**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: project-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
```

## Naming Conventions

### Container Names
- **Pattern:** `{project}-{service}-{environment}`
- **Examples:**
  - `chorescore-web-dev`
  - `33god-api-prod`
  - `concierge-postgres-local`

### Volume Names
- **Pattern:** `{project}_{service}_data`
- **Examples:**
  - `chorescore_postgres_data`
  - `portainer_data`
  - `qdrant_storage`

### Network Names
- **Pattern:** `{project}_network` or `{stack}_network`
- **Examples:**
  - `chorescore_network`
  - `monitoring_network`
  - `ai_stack_network`

## Common Commands (By Frequency)

### Daily Operations
```bash
# Start services in detached mode
docker-compose up -d

# View logs (follow mode)
docker-compose logs -f

# View logs for specific service
docker-compose logs -f service-name

# Restart services
docker-compose restart

# Stop services
docker-compose down

# List running containers
docker-compose ps

# Execute command in running container
docker-compose exec service-name bash
docker-compose exec service-name sh
```

### Weekly Maintenance
```bash
# Rebuild services
docker-compose build
docker-compose build --no-cache

# Force stop containers
docker-compose kill

# Remove stopped containers
docker-compose rm

# View resource usage
docker-compose top

# Clean up orphaned containers
docker-compose down --remove-orphans
```

### Monthly Operations
```bash
# Validate compose file
docker-compose config

# List images used
docker-compose images

# Clean up system
docker system prune -a
docker volume prune
docker image prune
```

## Environment Variable Management

### .env File Structure
```bash
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=app_db
DB_USER=app_user
DB_PASSWORD=${SECURE_PASSWORD}

# API Keys
API_KEY=${SECURE_API_KEY}
OPENAI_API_KEY=${OPENAI_KEY}

# Application Config
APP_ENV=development
LOG_LEVEL=info
PORT=3000

# External Services
REDIS_URL=redis://redis:6379
SUPABASE_URL=${SUPABASE_PROJECT_URL}
```

## Docker Desktop Integration

**Preference:** Use Docker Desktop for local development
- GUI for container management
- Built-in Kubernetes (optional)
- Volume management
- Extension ecosystem

**Recommended Extensions:**
- Portainer for advanced management
- Logs Explorer for better log viewing
- Resource Usage for monitoring

## Multi-Stack Orchestration

### Managing Multiple Related Stacks

**Pattern:** Use project-specific compose files with shared networks

```yaml
# Stack 1: Backend Services (backend/docker-compose.yml)
services:
  api:
    networks:
      - shared-network
      - backend-internal

networks:
  shared-network:
    external: true
  backend-internal:
    driver: bridge

# Stack 2: Frontend Services (frontend/docker-compose.yml)
services:
  web:
    networks:
      - shared-network
      - frontend-internal

networks:
  shared-network:
    external: true
  frontend-internal:
    driver: bridge
```

## Troubleshooting Patterns

### Common Issues & Solutions

**Build Failures:**
```bash
# Clear build cache
docker-compose build --no-cache

# Check logs during build
docker-compose up --build

# Verify Dockerfile syntax
docker-compose config
```

**Network Issues:**
```bash
# Recreate networks
docker-compose down
docker network prune
docker-compose up -d

# Check network connectivity
docker-compose exec service-name ping other-service
```

**Volume Permissions:**
```bash
# Fix volume permissions (Linux)
docker-compose exec service-name chown -R user:group /path

# Alternative: Run as specific user
user: "${UID}:${GID}"
```

## Best Practices

1. **Always use named volumes** for persistent data
2. **Pin image versions** to avoid breaking changes
3. **Use health checks** for critical services
4. **Separate secrets** into environment files
5. **Document dependencies** in depends_on
6. **Use restart policies** for production services
7. **Implement resource limits** for production deployments
8. **Network isolation** for security

## Deployment Patterns

### Development
```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src  # Live reload
    environment:
      - NODE_ENV=development
```

### Production
```yaml
services:
  app:
    image: registry/app:${VERSION}
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Integration with Other Tools

### With Mise (Tool Version Management)
```bash
# .mise.toml
[tools]
docker-compose = "latest"

[tasks.docker]
alias = "dc"
run = "docker-compose"

[tasks."docker:up"]
run = "docker-compose up -d"

[tasks."docker:logs"]
run = "docker-compose logs -f"
```

### With Make
```makefile
# Makefile
.PHONY: up down logs rebuild

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
```

## Security Considerations

1. **Never commit secrets** to version control
2. **Use .env files** excluded from git
3. **Implement non-root users** in containers
4. **Scan images** for vulnerabilities
5. **Limit network exposure** with proper network segmentation
6. **Use read-only volumes** where possible
7. **Implement proper firewall rules** for exposed ports

## Performance Optimization

### Resource Limits
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Volume Optimization
- Use bind mounts for development
- Use named volumes for production
- Consider volume drivers for distributed systems
- Implement volume backups for critical data

### Network Optimization
- Use bridge networks for single-host
- Consider overlay networks for multi-host
- Minimize cross-network communication
- Implement DNS resolution for service discovery
