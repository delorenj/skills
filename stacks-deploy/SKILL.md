---
name: stacks-deploy
description: >
  Generate Docker stack deployment entries for the stacks monorepo at ~/docker/stacks/.
  Use when: (1) deploying a new containerized service to the homelab,
  (2) restructuring an existing stack entry, (3) migrating a git repo's compose file
  to deployment-only, (4) adding Traefik reverse proxy routing for a service at *.delo.sh,
  (5) integrating a service into the top-level aggregator compose.yml.
---

# stacks-deploy

Generates minimal deployment stack entries from containerized git repos. Separates build concerns (git repo) from deployment topology (stacks monorepo) behind the delo.sh Traefik proxy.

## Invariants

- **No source code in stacks.** Config files, scripts, and .env only.
- **No submodules.** Links between repos are image references + mise tasks.
- **No `build:` in stacks compose files.** Everything uses `image:`.
- **Runtime data lives at `/home/delorenj/data/<service>/`**, not in stacks or git repos.
- **`network_mode: host` services cannot join the proxy network.** Use a companion service for Traefik routing.

## Workflow

### Step 1: Analyze Source Repo

Read the source repo's compose file(s), Dockerfile(s), and any deployment docs.

Identify for each service:
- Does it use `build:` or `image:`?
- What ports does it expose?
- What volumes does it need? (config files vs runtime data vs source mounts)
- Does it need special networking? (`network_mode: host`, `privileged`, GPU passthrough)
- Which service(s) are web-facing (need Traefik labels)?

### Step 2: Classify Deployment Mode

| Mode | When | Example |
|------|------|---------|
| **Image reference** | Custom code, needs `build:` in source repo | ssbnk-watcher |
| **Config-only** | Public base image + mounted configs | ssbnk-web (nginx:alpine) |
| **Hybrid** | Mix of custom and public images | ssbnk (watcher + nginx + alpine) |

For services with custom images, the source repo must publish the image (Docker Hub, GHCR, or local tag).

### Step 3: Extract Deployment Artifacts

From the source repo, identify files needed at deploy time:

**Copy to stacks entry:**
- Config files mounted into containers (nginx confs, prometheus configs, etc.)
- Scripts mounted as volumes (cron scripts, entrypoints)
- `.env.example` as template for `.env`

**Do NOT copy:**
- Source code, Dockerfiles, test files, docs, CI configs
- Compiled binaries, node_modules, build artifacts

**Create at `/home/delorenj/data/<service>/`:**
- Runtime data directories (databases, uploads, caches, logs)
- Any directory that containers write to at runtime

### Step 4: Determine Stacks Category

| Category | Purpose | Path |
|----------|---------|------|
| `utils` | Developer tools, internal services | `~/docker/stacks/utils/` |
| `websites` | Public-facing web applications | `~/docker/stacks/websites/` |
| `ai` | AI/ML services, agents | `~/docker/stacks/ai/` |
| `monitoring` | Observability, metrics, alerts | `~/docker/stacks/monitoring/` |
| `persistence` | Databases, search engines, caches | `~/docker/stacks/persistence/` |
| `media` | Media servers, streaming | `~/docker/stacks/media/` |

### Step 5: Generate Stack Entry

Create the directory structure:

```
~/docker/stacks/<category>/<service>/
  compose.yml        # image: references only
  .env               # runtime configuration
  [configs/]         # mounted config files
  [scripts/]         # mounted scripts
```

#### compose.yml Template

```yaml
services:
  <service-name>:
    image: <registry>/<image>:<tag>
    container_name: <service-name>
    restart: unless-stopped
    volumes:
      - /home/delorenj/data/<service>/<subdir>:/container/path
      - ./configs/some.conf:/etc/some.conf:ro
    environment:
      - KEY=${ENV_VAR}
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.<service>.entrypoints=websecure"
      - "traefik.http.routers.<service>.rule=Host(`<service>.delo.sh`)"
      - "traefik.http.routers.<service>.tls=true"
      - "traefik.http.routers.<service>.tls.certresolver=letsencrypt"
      - "traefik.http.services.<service>.loadbalancer.server.port=<port>"
      - "traefik.docker.network=proxy"

networks:
  proxy:
    external: true
```

#### Host Networking Pattern

When a service needs `network_mode: host` (clipboard, raw sockets, etc.), it CANNOT have Traefik labels or join the `proxy` network. Instead:

1. The host-networked service listens on a host port (e.g., 31243)
2. A companion web-facing service (e.g., nginx) joins the `proxy` network
3. The companion proxies API routes to `http://host.docker.internal:<port>`
4. The companion needs `extra_hosts: ["host.docker.internal:host-gateway"]`

### Step 6: Apply Traefik Integration

Standard label set (see `references/traefik-labels.md`). Additional patterns:

- **Auth-protected**: Add `traefik.http.routers.<svc>.middlewares=google-auth@file`
- **Multi-subdomain**: Define separate routers for each subdomain
- **Custom headers**: Define middleware in traefik dynamic config at `~/docker/core/traefik/traefik-data/dynamic/<service>.yml`

### Step 7: Update Aggregator

Each stacks category has a top-level `compose.yml` that uses `extends`:

```yaml
# ~/docker/stacks/<category>/compose.yml
services:
  <service-name>:
    extends:
      file: ./<service>/compose.yml
      service: <service-name>
```

**Limitations of `extends`:**
- Cannot extend services with `network_mode: host` or `privileged: true`
- Networks must be re-declared at the aggregator level
- Named volumes must be declared at the aggregator level

Services incompatible with `extends` should be noted in a comment and run standalone.

### Step 8: Generate Mise Tasks in Source Repo

For services with custom images, add to the source repo's `mise.toml`:

```toml
[tasks.build]
description = "Build the Docker image"
run = "docker build -t <user>/<image>:latest -f <dockerfile> <context>/"

[tasks.deploy]
description = "Pull and restart in stacks deployment"
run = """
cd ~/docker/stacks/<category>/<service>
docker compose pull <service-name>
docker compose up -d <service-name>
"""
```

## Reference Files

- `references/traefik-labels.md` - Label templates, middleware patterns, host-networking workaround
- `references/stacks-layout.md` - Monorepo structure, aggregator format, naming conventions
- `references/deployment-modes.md` - Mode comparison with real examples from existing stacks
