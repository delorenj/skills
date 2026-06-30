---
pipeline-status:
  - new
---
# Self-hosted agent infrastructure

Use this reference for the user's hosted agent support stack: Honcho, Traefik migration, and JWT admin access.

## Honcho

- Compose root: `~/docker/stacks/ai/honcho/`
- Services: `api`, `deriver`, `redis`
- Database: external PostgreSQL with pgvector
- Auth: HS256 JWTs controlled by `AUTH_JWT_SECRET`

## JWT structure

- `t`: timestamp
- `exp`: expiry
- `ad`: admin flag
- `w`: workspace
- `p`: peer
- `s`: session

Admin tokens should set `ad: true` and a long but explicit expiry.

## Compose-to-Traefik migration

1. Remove raw host port binds from the external service.
2. Attach the service to the `proxy` network.
3. Add Traefik router/service labels.
4. Keep internal-only services off the proxy network.
5. Redeploy and verify network membership and HTTPS reachability.

## Architecture reminder

Internet -> Cloudflare DNS/Tunnel -> Traefik -> services on `proxy`
