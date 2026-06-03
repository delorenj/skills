---
pipeline-status:
  - new
---
# Traefik routing (making `<svc>.delo.sh` work)

How a container becomes reachable at `https://<service>.delo.sh`.

## The pipeline

```
Browser → Cloudflare → Cloudflare Tunnel → Traefik (proxy network) → your container
```

Each hop is already wired. The container only needs to:

1. Be on the Docker network named `proxy`.
2. Carry the right Traefik labels.

No host port binding, no firewall rules, no certs. Cloudflare terminates TLS at its edge; Traefik terminates TLS again on the host (cert managed via Cloudflare DNS-01 challenge).

## Minimum labels

```yaml
services:
  myapp:
    # ... image, env, etc.
    networks:
      - stack       # the project's internal network
      - proxy       # required for Traefik to see it
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myservice.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls=true"
      - "traefik.http.services.myapp.loadbalancer.server.port=3000"
      - "traefik.docker.network=proxy"

networks:
  stack:        # internal, project-defined
  proxy:
    external: true
```

Substitutions:

- `myapp` → unique router/service name (router and service names must match for the simple case).
- `myservice.delo.sh` → public hostname.
- `3000` → the port the container LISTENS on internally (NOT a host bind port).

## Multiple hostnames (e.g. web + api in one stack)

```yaml
services:
  web:
    networks: [stack, proxy]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`myservice.delo.sh`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls=true"
      - "traefik.http.services.web.loadbalancer.server.port=3000"
      - "traefik.docker.network=proxy"

  api:
    networks: [stack, proxy]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.myservice.delo.sh`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls=true"
      - "traefik.http.services.api.loadbalancer.server.port=80"
      - "traefik.docker.network=proxy"
```

Each container gets its own router+service name pair (`web`, `api`), and its own `Host(...)` rule.

## docker-compose.override.yml pattern

When you don't want to fork the upstream `docker-compose.yml` (e.g. cal.diy), drop a sibling `docker-compose.override.yml` containing only the network + label overrides. Compose merges them automatically.

```yaml
# docker-compose.override.yml
services:
  calcom:
    networks:
      - stack
      - proxy
    ports: []   # remove any conflicting host port bind from upstream
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.calcom.rule=Host(`calendar.delo.sh`)"
      - "traefik.http.routers.calcom.entrypoints=websecure"
      - "traefik.http.routers.calcom.tls=true"
      - "traefik.http.services.calcom.loadbalancer.server.port=3000"
      - "traefik.docker.network=proxy"

networks:
  proxy:
    external: true
```

The override file is also `.gitignore`d-friendly if the stack is upstream-tracked, OR committable if the repo is your own deployment fork.

## Cloudflare Tunnel routes

`*.delo.sh` (wildcard) is already routed to Traefik in `~/docker/stacks/cloudflare-tunnel/config.yml`. New subdomains "just work" without editing the tunnel config — Traefik handles the host-based routing.

If a new subdomain doesn't resolve (`curl https://<new>.delo.sh` returns 1003 / no route), check:

1. Cloudflare DNS — there must be a CNAME for `<new>.delo.sh` pointing to the tunnel hostname (`<tunnel-id>.cfargotunnel.com`). Most are covered by a wildcard `*.delo.sh` CNAME; if missing, add it.
2. Tunnel config — only edit if you need a non-wildcard custom route.

## Verification

```bash
# Container on proxy network?
docker network inspect proxy | jq '.[].Containers | keys'

# Traefik sees the router?
curl -s http://192.168.1.12:8080/api/http/routers | jq '.[] | select(.name | contains("<myapp>")) | .name + " " + .status'

# Public reachable?
curl -I https://<myservice>.delo.sh
```

Healthy responses: `200`, `301`, `302`, `401` (auth), `404` (route exists, app returned 404). Bad: `502 Bad Gateway` (container down or wrong internal port), `503` (no Traefik service for this rule), DNS failure (Cloudflare/tunnel issue).

## ALLOWED_HOSTNAMES quoting (Cal-style apps)

A common Next.js / Cal.diy gotcha:

```
ALLOWED_HOSTNAMES='"calendar.delo.sh","localhost:3000"'
```

Outer single quotes preserve the string. Inner double quotes are part of the value (the app parses it as a JSON-ish array of strings). Comma-separated. No spaces around commas.

## When NOT to use Traefik

- Pure container-to-container traffic (db, redis): use the project network + service name. No proxy network.
- Tailscale-only services (visible only to your tailnet): expose via Tailscale Serve or a Tailscale sidecar instead of Traefik. Out of scope for this skill.
