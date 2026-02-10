# Docker Compose Patterns

Common Docker Compose configurations for ecosystem integration.

## Basic Service Pattern

```yaml
services:
  app:
    image: myapp:latest
    container_name: myapp
    restart: unless-stopped
    networks:
      - proxy
    environment:
      - NODE_ENV=production
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
      - "traefik.http.services.myapp.loadbalancer.server.port=3000"

networks:
  proxy:
    external: true
```

## Service with Native Database Connection

```yaml
services:
  app:
    image: myapp:latest
    container_name: myapp
    restart: unless-stopped
    networks:
      - proxy
    environment:
      # Connect to native PostgreSQL
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
      # Connect to native Redis
      - REDIS_URL=redis://host.docker.internal:6379
      # Connect to containerized Qdrant
      - QDRANT_URL=http://qdrant
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"

networks:
  proxy:
    external: true
```

## Service with Volume Persistence

```yaml
services:
  app:
    image: myapp:latest
    container_name: myapp
    restart: unless-stopped
    networks:
      - proxy
    volumes:
      # Named volume for data persistence
      - myapp-data:/app/data
      # Bind mount for configuration
      - ./config:/app/config:ro
    environment:
      - DATA_DIR=/app/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"

volumes:
  myapp-data:
    driver: local

networks:
  proxy:
    external: true
```

## Multi-Service Application

```yaml
services:
  api:
    image: myapp-api:latest
    container_name: myapp-api
    restart: unless-stopped
    networks:
      - proxy
      - backend
    environment:
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp-api.rule=Host(`api.myapp.delo.sh`)"
      - "traefik.http.routers.myapp-api.entrypoints=websecure"
      - "traefik.http.routers.myapp-api.tls.certresolver=letsencrypt"

  worker:
    image: myapp-worker:latest
    container_name: myapp-worker
    restart: unless-stopped
    networks:
      - backend
    environment:
      - REDIS_URL=redis://host.docker.internal:6379
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
    depends_on:
      - api

  frontend:
    image: myapp-frontend:latest
    container_name: myapp-frontend
    restart: unless-stopped
    networks:
      - proxy
    environment:
      - API_URL=https://api.myapp.delo.sh
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
    depends_on:
      - api

networks:
  proxy:
    external: true
  backend:
    internal: true
```

## Service with Build Configuration

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
      args:
        - BUILD_VERSION=${VERSION}
    image: delorenj/myapp:${VERSION:-latest}
    container_name: myapp
    restart: unless-stopped
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"

networks:
  proxy:
    external: true
```

## Service with Health Checks

```yaml
services:
  app:
    image: myapp:latest
    container_name: myapp
    restart: unless-stopped
    networks:
      - proxy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    environment:
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"

networks:
  proxy:
    external: true
```

## Service with Resource Limits

```yaml
services:
  app:
    image: myapp:latest
    container_name: myapp
    restart: unless-stopped
    networks:
      - proxy
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 512M
    environment:
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"

networks:
  proxy:
    external: true
```

## Port Allocation Guidelines

### Avoid These Common Ports

Never use these ports as they're likely already in use:

- 3000 (common dev server)
- 8000, 8080, 8888 (common HTTP)
- 5000 (Flask default)
- 4200 (Angular dev)
- 5173 (Vite dev)
- 3001, 3002 (common alternatives)

### Recommended Port Ranges

If you must expose ports, use random ports in these ranges:

- 8400-8499 (custom HTTP services)
- 9200-9299 (custom services)
- 7100-7199 (custom services)
- 10001-19999 (high-range custom services)

### Best Practice

Prefer Traefik labels over exposed ports:

```yaml
# DON'T
services:
  app:
    ports:
      - "3000:3000"  # ❌ Port conflict likely

# DO
services:
  app:
    labels:
      - "traefik.enable=true"  # ✅ Access via domain
      - "traefik.http.routers.app.rule=Host(`app.delo.sh`)"
```

## Network Patterns

### External Proxy Network (Required)

All HTTP services must join the `proxy` network:

```yaml
networks:
  proxy:
    external: true
```

### Internal Backend Network (Optional)

For inter-service communication without Traefik:

```yaml
services:
  api:
    networks:
      - proxy # For external access
      - backend # For worker communication

  worker:
    networks:
      - backend # Only internal communication

networks:
  proxy:
    external: true
  backend:
    internal: true # No external access
```

## Environment Variable Patterns

### Secrets from File

```yaml
services:
  app:
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
```

### Inline Environment

```yaml
services:
  app:
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
      - REDIS_URL=redis://host.docker.internal:6379
      - API_KEY=${OPENAI_API_KEY}
```

## Volume Patterns

### Named Volume

```yaml
services:
  app:
    volumes:
      - app-data:/app/data

volumes:
  app-data:
    driver: local
```

### Bind Mount (Preferred)

```yaml
services:
  app:
    volumes:
      - ./app:/app
      - ./config:/app/config:ro # Read-only
```

### Multiple Volumes

```yaml
services:
  app:
    volumes:
      - app-data:/app/data
      - app-logs:/app/logs
      - ./config:/app/config:ro

volumes:
  app-data:
  app-logs:
```

## Dependency Patterns

### Simple Dependencies

```yaml
services:
  api:
    image: api:latest

  worker:
    image: worker:latest
    depends_on:
      - api
```

### Dependencies with Conditions

```yaml
services:
  api:
    image: api:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]

  worker:
    image: worker:latest
    depends_on:
      api:
        condition: service_healthy
```

## Common Service Examples

### FastAPI Application

```yaml
services:
  api:
    image: myapi:latest
    container_name: myapi
    restart: unless-stopped
    networks:
      - proxy
    environment:
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapi
      - REDIS_URL=redis://host.docker.internal:6379
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapi.rule=Host(`api.delo.sh`)"
      - "traefik.http.routers.myapi.entrypoints=websecure"
      - "traefik.http.routers.myapi.tls.certresolver=letsencrypt"
      - "traefik.http.services.myapi.loadbalancer.server.port=8000"

networks:
  proxy:
    external: true
```

### React/Vite Frontend

```yaml
services:
  frontend:
    image: myfrontend:latest
    container_name: myfrontend
    restart: unless-stopped
    networks:
      - proxy
    environment:
      - VITE_API_URL=https://api.delo.sh
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myfrontend.rule=Host(`app.delo.sh`)"
      - "traefik.http.routers.myfrontend.entrypoints=websecure"
      - "traefik.http.routers.myfrontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.myfrontend.loadbalancer.server.port=80"

networks:
  proxy:
    external: true
```
