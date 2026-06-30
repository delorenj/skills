---
pipeline-status:
  - new
---
# Docker service provisioning

Use this reference when adding a new self-hosted service to the DeLoNET Docker environment.

## Decision tree

- HTTP service: use the Traefik-routed pattern.
- Raw TCP/UDP service: expose direct host ports and open the firewall.

## Standard scaffold

```
stacks/utils/<service>/
  compose.yml
  .env
  .env.example
  data/
```

## Durable checks

1. `docker compose config`
2. `docker compose pull`
3. `docker compose up -d`
4. `docker compose ps`
5. `docker compose logs --tail=20`
6. protocol-specific port or health verification
7. parent compose wiring check

## Service-specific gotchas

- Flatpak apps often store config in `~/.var/app/...`, not `~/.config/...`.
- RustDesk server provisioning also requires a RustDesk client on the target machine.
- Flatpak sandboxing may block `127.0.0.1`; prefer the host LAN IP for clients.
