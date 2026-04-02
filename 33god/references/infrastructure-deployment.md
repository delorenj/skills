---
pipeline-status:
  - new
---
# Infrastructure & Deployment

Use this for deploying 33GOD services, configuring networking, and managing external access.

## Architecture Overview

33GOD uses **Cloudflare Tunnel** + **Traefik** for external service access:

```
Internet → Cloudflare DNS (CNAME)
         → Cloudflare Edge (SSL/DDoS)
         → Cloudflare Tunnel (outbound)
         → Traefik (routing) OR Direct to Service
         → 33GOD Services
```

## Key Components

### Cloudflare Tunnel
- **Location:** `~/docker/stacks/cloudflare-tunnel/`
- **Purpose:** External access without public IP or port forwarding
- **Benefits:** Survives network changes, works through CGNAT

### Traefik
- **Purpose:** Reverse proxy, SSL termination, routing
- **Network:** `proxy` (shared with tunnel and services)
- **Dashboard:** `https://traefik.delo.sh`

### Proxy Network
- **Name:** `proxy`
- **Services:** All 33GOD services that need external access
- **DNS:** Docker internal DNS resolves container names

## Adding a New 33GOD Service

### Step 1: Add to Compose

**Option A: Include (for external dependencies like Plane)**
```yaml
# ~/code/33GOD/compose.yml
include:
  - path: ./plane/compose.yml
  - path: ./newservice/compose.yml
```

**Option B: Direct (for simple services)**
```yaml
# ~/code/33GOD/compose.yml
services:
  newservice:
    image: newservice:latest
    container_name: 33god-newservice
    networks:
      - 33god-network
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.newservice.rule=Host(`newservice.delo.sh`)"
      - "traefik.http.routers.newservice.entrypoints=websecure"
      - "traefik.http.routers.newservice.tls.certresolver=letsencrypt"
```

### Step 2: Configure Tunnel Routing

**Direct routing (simple):**
```yaml
# ~/docker/stacks/cloudflare-tunnel/config.yml
- hostname: "newservice.delo.sh"
  service: http://newservice:port
```

**Through Traefik (complex):**
```yaml
# ~/docker/stacks/cloudflare-tunnel/config.yml
- hostname: "newservice.delo.sh"
  service: https://traefik:443
  originRequest:
    noTLSVerify: true
```

### Step 3: Add DNS Route
```bash
cd ~/docker/stacks/cloudflare-tunnel
cloudflared tunnel route dns <tunnel-id> newservice.delo.sh
docker compose restart
```

### Step 4: Test
```bash
curl -I https://newservice.delo.sh
```

## Common Patterns

### Service with Internal + External API

Like Plane: Frontend at `plane.delo.sh`, API at `plane.delo.sh/api/`

```yaml
# Frontend service
services:
  frontend:
    environment:
      - NEXT_PUBLIC_API_BASE_URL=https://plane.delo.sh/api
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.plane.rule=Host(`plane.delo.sh`)"
      - "traefik.http.services.plane.loadbalancer.server.port=3000"
  
  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.plane-api.rule=Host(`plane.delo.sh`) && PathPrefix(`/api/`)"
      - "traefik.http.services.plane-api.loadbalancer.server.port=8000"
```

### Service Requiring Direct Container Access

Like Holocene: Direct to container, no Traefik labels

```yaml
# Tunnel config
- hostname: "holocene.delo.sh"
  service: http://holocene:80

# Service compose
services:
  holocene:
    networks:
      - proxy
    # No Traefik labels
```

## Network Switching (Xfinity ↔ RS7000)

The tunnel survives network changes. To verify:

```bash
# Check current public IP
curl -4 ifconfig.me

# Switch router/network

# Test services (should still work)
curl -I https://plane.delo.sh
curl -I https://holocene.delo.sh

# No DNS updates needed!
```

## Troubleshooting

### Service Not Accessible

1. **Check container is running:**
   ```bash
   docker ps | grep service-name
   ```

2. **Check on proxy network:**
   ```bash
   docker network inspect proxy | grep service-name
   ```

3. **Test internal connectivity:**
   ```bash
   docker exec cloudflare-tunnel wget -qO- http://service-name:port
   ```

4. **Check tunnel config:**
   ```bash
   cat ~/docker/stacks/cloudflare-tunnel/config.yml
   ```

5. **Verify DNS:**
   ```bash
   dig service.delo.sh
   # Should return Cloudflare IPs (104.x.x.x, 172.x.x.x)
   ```

### 523 Error (Origin Unreachable)

- Tunnel not running: `docker restart cloudflare-tunnel`
- Service not on proxy network
- Container name mismatch in config

### 525/526 SSL Errors

- Routing to Traefik without `noTLSVerify: true`
- Traefik SSL certificate issue
- Cloudflare SSL/TLS mode mismatch

## Migration from Port Forwarding

1. Set up Cloudflare Tunnel (see ecosystem-patterns skill)
2. Update DNS from A record to CNAME (tunnel)
3. Remove router port forwarding
4. Update service compose files to use `proxy` network
5. Add Traefik labels (if using Traefik routing)
6. Test all services

## References

- Full tunnel docs: `~/docker/stacks/cloudflare-tunnel/POST_MORTEM.md`
- Quick reference: `~/docker/stacks/cloudflare-tunnel/QUICK_REFERENCE.md`
- Docker patterns: `ecosystem-patterns/references/docker_patterns.md`
