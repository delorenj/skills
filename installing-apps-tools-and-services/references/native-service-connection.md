---
pipeline-status:
  - new
---
# Native Service Connection Patterns

Connecting Docker containers to native (host-installed) services like PostgreSQL, Redis, Neo4j, and (Non-native) Qdrant.

## Core Concept

Instead of running databases in Docker containers, connect to the host's native installations using `host.docker.internal`.

## Benefits

1. **Single Source of Truth:** One database for all services (containerized and native)
2. **Performance:** No container overhead for database
3. **Persistence:** Data survives container restarts/rebuilds
4. **Tooling:** Use native database tools (psql, redis-cli, etc.)
5. **Backups:** Centralized backup strategy for all data

## Connection Patterns

### PostgreSQL

**Environment Variable:**

```yaml
services:
  app:
    environment:
      - DATABASE_URL=postgresql://${DEFAULT_USERNAME}:${DEFAULT_PASSWORD}@host.docker.internal:5432/dbname
```

**Connection String Format:**

```
postgresql://username:password@host.docker.internal:5432/database
```

**Common Variable Names:**

- DEFAULT_USERNAME (this is set globally to 'delorenj')
- DEFAULT_PASSWORD (set globally, found in `$ZC/secrets.zsh`)
- `DATABASE_URL`
- `POSTGRES_URL`
- `DB_URL`
- `PG_CONNECTION_STRING`

**Create Database:**

```bash
# Connect to postgres
psql -U delorenj -d postgres

# Create database
CREATE DATABASE myapp;

# Create user (if needed)
CREATE USER myapp WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE myapp TO myapp;

# Exit
\q
```

**Test Connection from Container:**

```bash
# Start container
docker compose up -d

# Test connection
docker compose exec app psql $DATABASE_URL -c "SELECT 1"
```

### Redis

**Environment Variable:**

```yaml
services:
  app:
    environment:
      - REDIS_URL=redis://host.docker.internal:6379
      # With database selection
      - REDIS_URL=redis://host.docker.internal:6379/0
```

**Connection String Format:**

```
redis://[username[:password]@]host.docker.internal:6379[/database]
```

**Common Variable Names:**

- `REDIS_URL`
- `REDIS_HOST` (with separate port)
- `CACHE_URL`

**Test Connection:**

```bash
# From host
redis-cli ping

# From container
docker compose exec app redis-cli -u $REDIS_URL ping
```

### Qdrant (Vector Database)

**Environment Variable:**

```yaml
services:
  app:
    environment:
      - QDRANT_URL=http://host.docker.internal:6333
      - QDRANT_HOST=host.docker.internal
      - QDRANT_PORT=6333
```

**Connection Formats:**

```
# HTTP API
http://host.docker.internal:6333

# gRPC (if enabled)
grpc://host.docker.internal:6334
```

**Common Variable Names:**

- `QDRANT_URL`
- `QDRANT_HOST` + `QDRANT_PORT`
- `VECTOR_DB_URL`

**Test Connection:**

```bash
# Check health
curl http://localhost:6333/health

# From container
docker compose exec app curl http://host.docker.internal:6333/health
```

### Neo4j (Graph Database)

**Environment Variable:**

```yaml
services:
  app:
    environment:
      - NEO4J_URI=bolt://host.docker.internal:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
```

**Connection String Format:**

```
bolt://host.docker.internal:7687
neo4j://host.docker.internal:7687
```

**Common Variable Names:**

- `NEO4J_URI`
- `NEO4J_BOLT_URL`
- `GRAPH_DB_URL`

**Test Connection:**

```bash
# From host (requires neo4j-driver)
cypher-shell -a bolt://localhost:7687 -u neo4j -p password

# From container
docker compose exec app cypher-shell -a bolt://host.docker.internal:7687 -u neo4j -p $NEO4J_PASSWORD
```

## Multi-Service Example

```yaml
services:
  app:
    image: myapp:latest
    container_name: myapp
    restart: unless-stopped
    networks:
      - proxy
    environment:
      # PostgreSQL
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
      # Redis
      - REDIS_URL=redis://host.docker.internal:6379/0
      # Qdrant
      - QDRANT_URL=http://host.docker.internal:6333
      # Neo4j
      - NEO4J_URI=bolt://host.docker.internal:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"

networks:
  proxy:
    external: true
```

## Environment File Pattern

**`.env` file:**

```bash
# PostgreSQL
POSTGRES_PASSWORD=your_postgres_password
DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp

# Redis
REDIS_URL=redis://host.docker.internal:6379/0

# Qdrant
QDRANT_URL=http://host.docker.internal:6333

# Neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_URI=bolt://host.docker.internal:7687
NEO4J_USER=neo4j

# Application
API_KEY=your_api_key
SECRET_KEY=your_secret_key
```

**Reference in compose:**

```yaml
services:
  app:
    env_file:
      - .env
```

## Secrets Management

**Load from secrets.zsh:**

```bash
# In ~/.config/zshyzsh/secrets.zsh
export POSTGRES_PASSWORD="actual_password"
export NEO4J_PASSWORD="actual_password"
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Create .env from secrets:**

```bash
# Generate .env
cat > .env << EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
NEO4J_PASSWORD=${NEO4J_PASSWORD}
OPENAI_API_KEY=${OPENAI_API_KEY}
DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapp
REDIS_URL=redis://host.docker.internal:6379
QDRANT_URL=http://host.docker.internal:6333
NEO4J_URI=bolt://host.docker.internal:7687
EOF
```

## Database Initialization

### PostgreSQL Database Setup

```bash
# 1. Create database
psql -U delorenj -d postgres -c "CREATE DATABASE myapp"

# 2. Create tables (if needed)
psql -U delorenj -d myapp -f schema.sql

# 3. Verify
psql -U delorenj -d myapp -c "\dt"
```

### Redis Database Selection

```bash
# Select database (0-15)
redis-cli SELECT 0

# Or specify in URL
REDIS_URL=redis://host.docker.internal:6379/5
```

### Qdrant Collection Creation

```bash
# Create collection via API
curl -X PUT http://localhost:6333/collections/myapp \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'

# Verify
curl http://localhost:6333/collections/myapp
```

## Troubleshooting

### Connection Refused

**Check service is running:**

```bash
# PostgreSQL
systemctl status postgresql

# Redis
systemctl status redis

# Neo4j
systemctl status neo4j

# Qdrant
systemctl status qdrant
```

**Check service is listening:**

```bash
# Check ports
ss -tulpn | grep -E '(5432|6379|6333|7687)'
```

**Restart if needed:**

```bash
sudo systemctl restart postgresql redis neo4j qdrant
```

### Authentication Failed

**PostgreSQL:**

```bash
# Check pg_hba.conf allows host connections
sudo vi /etc/postgresql/*/main/pg_hba.conf

# Should have line like:
# host    all             all             172.17.0.0/16           md5

# Reload config
sudo systemctl reload postgresql
```

**Redis:**

```bash
# Check redis.conf for password
sudo vi /etc/redis/redis.conf

# Look for:
# requirepass your_password
```

**Neo4j:**

```bash
# Reset password
neo4j-admin set-initial-password new_password
```

### DNS Resolution Failed

**Test host.docker.internal:**

```bash
# From container
docker compose exec app ping host.docker.internal

# Should resolve to host IP
```

**Alternative (if host.docker.internal doesn't work):**

```yaml
services:
  app:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### Firewall Issues

**Check firewall allows local connections:**

```bash
# Ubuntu/Debian
sudo ufw status

# Allow from Docker network (if needed)
sudo ufw allow from 172.17.0.0/16
```

## Best Practices

1. **Use Environment Variables:** Don't hardcode connection strings
2. **Load Secrets Safely:** Never commit .env files to git
3. **Create Dedicated Databases:** One database per application
4. **Use Connection Pooling:** Configure max connections in app
5. **Health Checks:** Verify database connectivity in container health checks
6. **Backup Strategy:** Regular backups of native databases
7. **Monitor Connections:** Watch for connection leaks

## Health Check Examples

### PostgreSQL Health Check

```yaml
services:
  app:
    healthcheck:
      test:
        [
          "CMD",
          "pg_isready",
          "-h",
          "host.docker.internal",
          "-U",
          "delorenj",
          "-d",
          "myapp",
        ]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Redis Health Check

```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "redis-cli", "-h", "host.docker.internal", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Custom Health Check Script

```yaml
services:
  app:
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import psycopg2; psycopg2.connect('${DATABASE_URL}')",
        ]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Common Application Patterns

### FastAPI with PostgreSQL

```yaml
services:
  api:
    image: myapi:latest
    environment:
      - DATABASE_URL=postgresql://delorenj:${POSTGRES_PASSWORD}@host.docker.internal:5432/myapi
      - REDIS_URL=redis://host.docker.internal:6379
```

### n8n with PostgreSQL

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=host.docker.internal
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=delorenj
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
```

### React/Vite (no direct database)

```yaml
services:
  frontend:
    image: myfrontend:latest
    environment:
      # Frontend calls API, API connects to database
      - VITE_API_URL=https://api.delo.sh
```
