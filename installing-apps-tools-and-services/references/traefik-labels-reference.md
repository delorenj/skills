---
pipeline-status:
  - new
---
# Traefik Labels Reference

Common Traefik label patterns for Docker service integration.

## Basic HTTP Service

### Minimal Configuration

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
```

### With Custom Port

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.services.myapp.loadbalancer.server.port=8080"
```

## Advanced Routing

### Path-Based Routing

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`delo.sh`) && PathPrefix(`/myapp`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
```

### Multiple Hosts

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`) || Host(`app.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
```

### Path and Host

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`delo.sh`) && (PathPrefix(`/api`) || PathPrefix(`/v1`))"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
```

## Middlewares

### Strip Prefix

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`delo.sh`) && PathPrefix(`/myapp`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.middlewares.myapp-strip.stripprefix.prefixes=/myapp"
  - "traefik.http.routers.myapp.middlewares=myapp-strip"
```

### Add Prefix

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.middlewares.myapp-prefix.addprefix.prefix=/api"
  - "traefik.http.routers.myapp.middlewares=myapp-prefix"
```

### CORS Headers

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`api.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.middlewares.myapp-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS"
  - "traefik.http.middlewares.myapp-cors.headers.accesscontrolalloworigin=*"
  - "traefik.http.middlewares.myapp-cors.headers.accesscontrolallowheaders=*"
  - "traefik.http.routers.myapp.middlewares=myapp-cors"
```

### Basic Auth

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`admin.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.middlewares.myapp-auth.basicauth.users=admin:$$apr1$$H6uskkkW$$IgXLP6ewTrSuBkTrqE8wj/"
  - "traefik.http.routers.myapp.middlewares=myapp-auth"
```

### Rate Limiting

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`api.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.middlewares.myapp-ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.myapp-ratelimit.ratelimit.burst=50"
  - "traefik.http.routers.myapp.middlewares=myapp-ratelimit"
```

### Redirect to HTTPS

```yaml
labels:
  - "traefik.enable=true"
  # HTTP router (redirect)
  - "traefik.http.routers.myapp-http.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp-http.entrypoints=web"
  - "traefik.http.routers.myapp-http.middlewares=myapp-https-redirect"
  # HTTPS router
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  # Redirect middleware
  - "traefik.http.middlewares.myapp-https-redirect.redirectscheme.scheme=https"
```

### Chain Multiple Middlewares

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  # Define middlewares
  - "traefik.http.middlewares.myapp-strip.stripprefix.prefixes=/api"
  - "traefik.http.middlewares.myapp-cors.headers.accesscontrolalloworigin=*"
  - "traefik.http.middlewares.myapp-ratelimit.ratelimit.average=100"
  # Chain them
  - "traefik.http.routers.myapp.middlewares=myapp-strip,myapp-cors,myapp-ratelimit"
```

## WebSocket Support

### Basic WebSocket

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`ws.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.services.myapp.loadbalancer.server.port=8080"
```

### WebSocket with Path

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`app.delo.sh`) && PathPrefix(`/ws`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.services.myapp.loadbalancer.server.port=8080"
```

## Multiple Services/Ports

### Two Services on Different Ports

```yaml
labels:
  # Web interface
  - "traefik.enable=true"
  - "traefik.http.routers.myapp-web.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp-web.entrypoints=websecure"
  - "traefik.http.routers.myapp-web.tls.certresolver=letsencrypt"
  - "traefik.http.routers.myapp-web.service=myapp-web"
  - "traefik.http.services.myapp-web.loadbalancer.server.port=80"
  # API
  - "traefik.http.routers.myapp-api.rule=Host(`api.myapp.delo.sh`)"
  - "traefik.http.routers.myapp-api.entrypoints=websecure"
  - "traefik.http.routers.myapp-api.tls.certresolver=letsencrypt"
  - "traefik.http.routers.myapp-api.service=myapp-api"
  - "traefik.http.services.myapp-api.loadbalancer.server.port=8080"
```

## Health Checks

### Custom Health Check

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.services.myapp.loadbalancer.server.port=8080"
  - "traefik.http.services.myapp.loadbalancer.healthcheck.path=/health"
  - "traefik.http.services.myapp.loadbalancer.healthcheck.interval=10s"
```

## Load Balancing

### Sticky Sessions

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.services.myapp.loadbalancer.sticky.cookie=true"
  - "traefik.http.services.myapp.loadbalancer.sticky.cookie.name=myapp_session"
```

## Common Patterns

### API with CORS and Rate Limiting

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.api.rule=Host(`api.delo.sh`)"
  - "traefik.http.routers.api.entrypoints=websecure"
  - "traefik.http.routers.api.tls.certresolver=letsencrypt"
  - "traefik.http.services.api.loadbalancer.server.port=8000"
  # CORS
  - "traefik.http.middlewares.api-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS"
  - "traefik.http.middlewares.api-cors.headers.accesscontrolalloworigin=https://app.delo.sh"
  - "traefik.http.middlewares.api-cors.headers.accesscontrolallowheaders=*"
  # Rate limiting
  - "traefik.http.middlewares.api-ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.api-ratelimit.ratelimit.burst=50"
  # Apply middlewares
  - "traefik.http.routers.api.middlewares=api-cors,api-ratelimit"
```

### Admin Dashboard with Auth

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.admin.rule=Host(`admin.delo.sh`)"
  - "traefik.http.routers.admin.entrypoints=websecure"
  - "traefik.http.routers.admin.tls.certresolver=letsencrypt"
  # Basic auth (password: admin)
  - "traefik.http.middlewares.admin-auth.basicauth.users=admin:$$apr1$$H6uskkkW$$IgXLP6ewTrSuBkTrqE8wj/"
  - "traefik.http.routers.admin.middlewares=admin-auth"
```

### Frontend with API Proxy

```yaml
labels:
  - "traefik.enable=true"
  # Frontend
  - "traefik.http.routers.app.rule=Host(`app.delo.sh`)"
  - "traefik.http.routers.app.entrypoints=websecure"
  - "traefik.http.routers.app.tls.certresolver=letsencrypt"
  - "traefik.http.routers.app.service=app-frontend"
  - "traefik.http.services.app-frontend.loadbalancer.server.port=80"
  # API proxy at /api
  - "traefik.http.routers.app-api.rule=Host(`app.delo.sh`) && PathPrefix(`/api`)"
  - "traefik.http.routers.app-api.entrypoints=websecure"
  - "traefik.http.routers.app-api.tls.certresolver=letsencrypt"
  - "traefik.http.routers.app-api.service=app-backend"
  - "traefik.http.services.app-backend.loadbalancer.server.port=8000"
  - "traefik.http.middlewares.app-api-strip.stripprefix.prefixes=/api"
  - "traefik.http.routers.app-api.middlewares=app-api-strip"
```

## Debugging

### Enable Access Logs

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  # Enable access logs for this router
  - "traefik.http.routers.myapp.middlewares=myapp-logger"
  - "traefik.http.middlewares.myapp-logger.accesslog=true"
```

### Test Without TLS

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.delo.sh`)"
  - "traefik.http.routers.myapp.entrypoints=web"  # HTTP instead of websecure
```

## Label Naming Convention

```
traefik.http.routers.<router-name>.<config-key>
traefik.http.services.<service-name>.<config-key>
traefik.http.middlewares.<middleware-name>.<config-key>
```

**Router Name:** Usually the service name (e.g., `myapp`)
**Service Name:** Usually `<router-name>` or `<router-name>-<purpose>` (e.g., `myapp-web`)
**Middleware Name:** Usually `<router-name>-<function>` (e.g., `myapp-cors`)

## Quick Reference

### Essential Labels

```yaml
traefik.enable=true  # Enable Traefik for this container
traefik.http.routers.<name>.rule  # Routing rule
traefik.http.routers.<name>.entrypoints  # Entry point (web/websecure)
traefik.http.routers.<name>.tls.certresolver  # Certificate resolver
traefik.http.services.<name>.loadbalancer.server.port  # Backend port
```

### Common Entry Points

- `web` - HTTP (port 80)
- `websecure` - HTTPS (port 443)

### Common Resolvers

- `letsencrypt` - Let's Encrypt certificates
