# Deployment Modes

## Mode 1: Image Reference

The source repo builds and publishes a Docker image. The stacks entry references it.

**When to use**: Custom application code that compiles into a container.

**Source repo responsibilities**:
- Dockerfile
- CI/CD pipeline (GitHub Actions) to build and push
- mise tasks for local build/tag/push/deploy

**Stacks entry contains**:
- `compose.yml` with `image: delorenj/<service>:latest`
- `.env` with runtime config
- No source code, no Dockerfile

**Example**: ssbnk-watcher
```yaml
# stacks compose.yml
ssbnk-watcher:
  image: delorenj/ssbnk-watcher:latest
```
```toml
# source repo mise.toml
[tasks.build]
run = "docker build -t delorenj/ssbnk-watcher:latest -f watcher/Dockerfile watcher/"
[tasks.deploy]
run = "cd ~/docker/stacks/utils/ssbnk && docker compose pull ssbnk-watcher && docker compose up -d ssbnk-watcher"
```

## Mode 2: Config-Only

A public base image with config files mounted in. No custom image needed.

**When to use**: Standard software (nginx, redis, postgres) with custom configuration.

**Source repo responsibilities**: None (or maintains config as reference).

**Stacks entry contains**:
- `compose.yml` with `image: nginx:alpine` (or similar)
- Config files in subdirectories
- `.env` with runtime config

**Example**: ssbnk-web
```yaml
ssbnk-web:
  image: nginx:alpine
  volumes:
    - ./web/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./web/default.conf:/etc/nginx/conf.d/default.conf:ro
```

## Mode 3: Hybrid

Multiple services where some need custom images and others use public images.

**When to use**: Applications with distinct components (web server + app server + workers).

**Stacks entry**: mix of `image: delorenj/...` and `image: nginx:alpine` etc.

**Example**: ssbnk (3 services)
- `ssbnk-web`: config-only (nginx:alpine + mounted configs)
- `ssbnk-watcher`: image-reference (delorenj/ssbnk-watcher:latest)
- `ssbnk-cleanup`: config-only (alpine:latest + mounted script)

## Mode 4: Baked Image

A custom image with environment-specific configuration baked in at build time. Tighter coupling with the personal environment but simpler runtime config.

**When to use**: Services where:
- Runtime config is complex and rarely changes
- You want zero-config deployment (`docker compose up` with no .env)
- The service is personal-use only (not distributable)

**Source repo responsibilities**:
- Dockerfile with `COPY` for configs instead of volume mounts
- `ARG`/`ENV` for build-time customization
- mise tasks for build with env-specific args

**Stacks entry contains**:
- `compose.yml` with `image: delorenj/<service>:delo` (custom tag)
- Minimal or no `.env`

**Example** (hypothetical):
```dockerfile
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf
ENV SSBNK_DOMAIN=ss.delo.sh
```
```yaml
ssbnk-web:
  image: delorenj/ssbnk-web:delo
  # No config mounts needed, everything baked in
```

## Decision Matrix

| Factor | Image Ref | Config-Only | Hybrid | Baked |
|--------|-----------|-------------|--------|-------|
| Custom code | Yes | No | Some | Yes |
| Config complexity | Low | High | Mixed | High (at build) |
| Distributable | Yes | N/A | Partial | No |
| Runtime simplicity | Medium | Medium | Medium | High |
| Build pipeline needed | Yes | No | Yes | Yes |
| Config change = rebuild | No | No | No | Yes |
