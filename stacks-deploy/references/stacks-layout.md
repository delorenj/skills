# Stacks Monorepo Layout

## Location

`/home/delorenj/docker/stacks/`

## Categories

```
docker/stacks/
  utils/          # Developer tools, internal services
  monitoring/     # Grafana, cAdvisor, alertmanager
  websites/       # Public web apps (chorescore, plane, etc.)
  ai/             # AI/ML services (hindsight, etc.)
  persistence/    # Databases, Qdrant, Redis
  media/          # Media servers
  minio/          # Object storage
  pgadmin/        # Database admin
```

Each category has a top-level `compose.yml` aggregator that uses `extends` to pull in child services.

## Stack Entry Structure

Minimal entry (config-only mode):
```
<category>/<service>/
  compose.yml
  .env
```

Typical entry (with mounted configs):
```
<category>/<service>/
  compose.yml
  .env
  web/           # or configs/, etc.
    nginx.conf
    default.conf
  scripts/
    entrypoint.sh
```

## Runtime Data Convention

Runtime data (databases, uploads, caches) lives at:
```
/home/delorenj/data/<service>/
```

NOT in the stacks directory. NOT in the git repo.

## Aggregator Format

Each category's top-level `compose.yml`:

```yaml
version: '3.5'

services:
  service-a:
    extends:
      file: ./service-a/compose.yml
      service: service-a
  service-b:
    extends:
      file: ./service-b/compose.yml
      service: service-b

networks:
  proxy:
    external: true

volumes:
  service-a-data:
```

### Extends Limitations

The `extends` mechanism does NOT support:
- `network_mode` (host, none, container:)
- `privileged: true`
- `depends_on` (sometimes)

Services with these must be excluded from the aggregator and run standalone:
```yaml
  # service-x excluded: network_mode: host incompatible with extends
  # Run standalone: cd service-x && docker compose up -d service-x
```

## Naming Conventions

- **Container names**: `<service>` or `<service>-<component>` (e.g., `ssbnk-web`, `ssbnk-watcher`)
- **Router names** (traefik): match the container name
- **Image names**: `delorenj/<service>:latest` for custom images
- **Volume names**: `<service>_data` or `<service>-<purpose>`
- **Network names**: `proxy` (external), `<service>-internal` (private)

## Existing Examples

| Stack | Mode | Services |
|-------|------|----------|
| nats | image + config | nats (nats:2.10-alpine) |
| adguard | image + config dirs | adguard (adguard/adguardhome) |
| marker | pure image | marker-api (savatar101/marker-api:0.3) |
| ssbnk | hybrid | ssbnk-web (nginx), ssbnk-watcher (custom), ssbnk-cleanup (alpine) |
| rustdesk | multi-service image | hbbs + hbbr (rustdesk-server) |
