---
pipeline-status:
  - new
---
# Traefik Label Patterns

## Proxy Infrastructure

- Location: `/home/delorenj/docker/core/traefik/`
- Network: `proxy` (external Docker bridge, must pre-exist)
- Domain: `*.delo.sh`
- TLS: Let's Encrypt via Cloudflare DNS challenge
- Dashboard: `traefik.delo.sh` (Google OIDC protected)
- Dynamic configs (hot-reload): `/home/delorenj/docker/core/traefik/traefik-data/dynamic/*.yml`

## Standard Labels (minimum for any web-facing service)

```yaml
networks:
  - proxy
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.SERVICE.rule=Host(`SERVICE.delo.sh`)"
  - "traefik.http.routers.SERVICE.entrypoints=websecure"
  - "traefik.http.routers.SERVICE.tls=true"
  - "traefik.http.routers.SERVICE.tls.certresolver=letsencrypt"
  - "traefik.http.services.SERVICE.loadbalancer.server.port=PORT"
  - "traefik.docker.network=proxy"
```

Replace `SERVICE` with the router name (usually the service name) and `PORT` with the container's internal port.

## With Google OIDC Authentication

```yaml
labels:
  - "traefik.http.routers.SERVICE.middlewares=google-auth@file"
```

The `google-auth@file` middleware is defined in the traefik dynamic config. Authorized domains: `acd.consulting`, `delo.sh`. Authorized emails: `jaradd@gmail.com`.

## Multi-Subdomain (separate routers)

```yaml
labels:
  # Web UI
  - "traefik.http.routers.SERVICE-ui.rule=Host(`SERVICE.delo.sh`)"
  - "traefik.http.routers.SERVICE-ui.entrypoints=websecure"
  - "traefik.http.routers.SERVICE-ui.tls.certresolver=letsencrypt"
  - "traefik.http.services.SERVICE-ui.loadbalancer.server.port=UI_PORT"
  # API
  - "traefik.http.routers.SERVICE-api.rule=Host(`api.SERVICE.delo.sh`)"
  - "traefik.http.routers.SERVICE-api.entrypoints=websecure"
  - "traefik.http.routers.SERVICE-api.tls.certresolver=letsencrypt"
  - "traefik.http.services.SERVICE-api.loadbalancer.server.port=API_PORT"
```

**IMPORTANT:** Multi-level subdomains like `api.SERVICE.delo.sh` are NOT covered by
the `*.delo.sh` wildcard CNAME. You must create an explicit CNAME record via the
Cloudflare API. See `ecosystem-patterns/references/docker_patterns.md` for the
API examples and the DNS edit token location.

Prefer single-level subdomains (e.g., `SERVICE-api.delo.sh`) when possible to
avoid this extra step.

## Environment Variable Domain

Use env var substitution for the domain when it appears in multiple places:

```yaml
labels:
  - "traefik.http.routers.SERVICE.rule=Host(`${SERVICE_DOMAIN}`)"
```

## Host Networking Workaround

Services with `network_mode: host` CANNOT join Docker networks. Pattern:

1. The host-networked service exposes a port on the host (e.g., 31243)
2. A companion service (typically nginx) joins the `proxy` network
3. The companion proxies to `http://host.docker.internal:PORT`
4. The companion declares:
   ```yaml
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

## Non-Docker Services (Dynamic Config)

For LAN services not running in Docker, create a YAML file in the traefik dynamic config directory:

File: `~/docker/core/traefik/traefik-data/dynamic/SERVICE.yml`

```yaml
http:
  services:
    SERVICE:
      loadBalancer:
        servers:
          - url: "http://192.168.1.XX:PORT"
  routers:
    SERVICE:
      rule: "Host(`SERVICE.delo.sh`)"
      service: SERVICE
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
```
