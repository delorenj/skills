# Docker & Container Patterns

## Cloudflare Tunnel + Traefik Architecture

**Purpose:** Expose services externally without public IP, port forwarding, or DNS updates when switching networks.

### Architecture Overview

```
Internet → Cloudflare DNS (wildcard CNAME → Tunnel)
         → Cloudflare Edge (SSL termination)
         → Cloudflare Tunnel (outbound HTTPS)
         → Traefik (internal routing via Docker labels)
         → Services
```

**Benefits:**
- No public IP required (works through CGNAT)
- No port forwarding needed
- Survives network changes (router/AP mode switches)
- Automatic HTTPS at Cloudflare edge
- DDoS protection
- **Zero DNS management for new services** (wildcard CNAME covers all `*.delo.sh`)

### DNS Architecture (Wildcard CNAME)

**The wildcard `*.delo.sh` and root `delo.sh` are both CNAME records pointing to the tunnel.**
This means adding a new service requires ZERO DNS changes. Just add Traefik labels and the service is externally accessible.

**Limitation:** DNS wildcards only match ONE level. `*.delo.sh` matches `app.delo.sh` but NOT `api.app.delo.sh`. Multi-level subdomains (e.g., `api.hs.delo.sh`) require explicit CNAME records via the Cloudflare API.

**Current DNS state:**
- `*.delo.sh` → CNAME → `<tunnel-id>.cfargotunnel.com` (proxied)
- `delo.sh` → CNAME → `<tunnel-id>.cfargotunnel.com` (proxied, CNAME flattening)
- External services (intelliforia, mathflash, etc.) have their own A records

### Managing DNS via Cloudflare API

**API Token:** The token with DNS edit permissions is in `secrets.zsh` (the commented-out value `8uS4nHflVYMGq6m6YysHWQLKRVZMk83A-Z0gQOtg`). The active `CLOUDFLARE_API_TOKEN` is for Traefik's DNS challenge only and lacks DNS edit scope.

**Zone ID:** `eabc163cde3e31680f10fc313aecdda3`

**List DNS records:**
```python
import urllib.request, json
token = '<dns-edit-token>'
zone_id = 'eabc163cde3e31680f10fc313aecdda3'
req = urllib.request.Request(
    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?per_page=100',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
resp = json.loads(urllib.request.urlopen(req).read())
for r in sorted(resp['result'], key=lambda x: x['name']):
    if r['type'] in ('A', 'CNAME'):
        print(f"{r['name']:30s} {r['type']:6s} {r['content']}")
```

**Create a CNAME (for multi-level subdomains only):**
```python
data = json.dumps({
    'type': 'CNAME',
    'name': 'api.app.delo.sh',
    'content': '<tunnel-id>.cfargotunnel.com',
    'proxied': True,
    'ttl': 1
}).encode()
req = urllib.request.Request(
    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
    data=data,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    method='POST'
)
```

**Update a record (PUT with record ID):**
```python
req = urllib.request.Request(
    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}',
    data=data,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    method='PUT'
)
```

**Delete a record:**
```python
req = urllib.request.Request(
    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    method='DELETE'
)
```

### Directory Structure

```
~/docker/stacks/cloudflare-tunnel/
├── compose.yml           # Tunnel container
├── config.yml            # Ingress routing rules
├── credentials.json      # Tunnel credentials (from cloudflared)
├── .env                  # TUNNEL_TOKEN
├── ARCHITECTURE.md       # Architecture comparison docs
├── POST_MORTEM.md        # Migration post-mortem
└── QUICK_REFERENCE.md    # Quick reference
```

### Tunnel Configuration

**Tunnel ID:** `6dfd95af-6e2a-4833-84b8-e0a1fda5da4a`
**Tunnel Name:** `homelab-delosh`
**Host cert:** `~/.cloudflared/cert.pem`

**Ingress Rules (config.yml):**
```yaml
tunnel: 6dfd95af-6e2a-4833-84b8-e0a1fda5da4a
credentials-file: /etc/cloudflared/credentials.json

ingress:
  # Direct routing (bypasses Traefik, one less hop)
  - hostname: "holocene.delo.sh"
    service: http://holocene:80

  # Wildcard: everything else goes through Traefik
  - hostname: "*.delo.sh"
    service: https://traefik:443
    originRequest:
      noTLSVerify: true

  - hostname: "delo.sh"
    service: https://traefik:443
    originRequest:
      noTLSVerify: true

  - service: http_status:404
```

**Docker Compose:**
```yaml
services:
  cloudflare-tunnel:
    image: cloudflare/cloudflared:latest
    container_name: cloudflare-tunnel
    restart: unless-stopped
    command: tunnel --config /etc/cloudflared/config.yml run
    volumes:
      - ./config.yml:/etc/cloudflared/config.yml:ro
      - ./credentials.json:/etc/cloudflared/credentials.json:ro
    networks:
      - proxy

networks:
  proxy:
    external: true
```

### Adding a New Service (Zero DNS Steps)

For single-level subdomains (`app.delo.sh`), the wildcard CNAME handles DNS automatically. Just:

1. Add Traefik labels to your service's compose.yml
2. Ensure it's on the `proxy` network
3. `docker compose up -d`

That's it. No DNS changes, no tunnel config changes, no restarts.

```yaml
services:
  myapp:
    image: myapp:latest
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
      - "traefik.http.services.myapp.loadbalancer.server.port=3000"
      - "traefik.docker.network=proxy"
```

### Multi-Level Subdomains (Exception)

`*.delo.sh` does NOT match `api.app.delo.sh`. For multi-level subdomains, you must create an explicit CNAME via the Cloudflare API (see "Managing DNS via Cloudflare API" above).

Current exceptions:
- `api.hs.delo.sh` (Hindsight API)

### Routing Patterns

**Pattern 1: Through Traefik (Default, Recommended)**
- The wildcard tunnel config sends `*.delo.sh` to `traefik:443`
- Traefik routes based on Docker labels
- Use for: Almost everything

**Pattern 2: Direct to Container (Bypass Traefik)**
Add a specific hostname entry in `config.yml` ABOVE the wildcard:
```yaml
- hostname: "app.delo.sh"
  service: http://container-name:port
```
- Use for: Simple services that don't need Traefik middleware
- Requires: tunnel restart after config change

**Important: Order Matters in config.yml**
Most specific hostnames first, wildcard last.

### Troubleshooting

**523 Error (Origin Unreachable):**
```bash
docker ps | grep cloudflare
docker network inspect proxy | grep container-name
dig service.delo.sh  # Should return Cloudflare IPs
```

**525/526 SSL Errors:**
- Ensure `noTLSVerify: true` in tunnel config for Traefik routes
- Check Traefik has valid certs (acme.json)

**New service not accessible:**
1. Is the container on the `proxy` network?
2. Does it have `traefik.enable=true` label?
3. Is the Host rule correct?
4. Is it a multi-level subdomain? (needs explicit CNAME)

### Security Best Practices

1. **Tunnel credentials** (`credentials.json`) are secrets
2. **No public ports needed** for externally-accessible services
3. **Traefik handles internal SSL** (Let's Encrypt via DNS challenge), Cloudflare handles external
4. **Network isolation** via `proxy` network
5. **Service-to-service** communication uses internal Docker DNS, not public URLs
