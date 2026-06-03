---
pipeline-status:
  - new
---
# Constants

Hard data. No prose. Look up the value, return to your task.

## Host & network

| Concept | Value | Notes |
|---|---|---|
| Host name | `big-chungus` | Primary server. |
| LAN IP | `192.168.1.12` | Subnet `192.168.1.0/24` (Netgear RS700 at `.1`). Don't hardcode in compose. |
| Tailscale IPv4 | `100.66.29.76` | For machine-to-machine over the tailnet. |
| Tailscale MagicDNS | `big-chungus.burro-salmon.ts.net` | Tailnet name = `burro-salmon.ts.net`. |
| Docker host bridge | `host.docker.internal` | How a container reaches the host (e.g. external postgres at 5432). |
| Subnet | `192.168.1.0/24` | If you see `10.0.0.x` in any config it is stale Xfinity-era data — replace. |

## Public surface

| Concept | Value | Notes |
|---|---|---|
| Domain root | `delo.sh` | Cloudflare-managed zone. |
| Service URL | `https://<service>.delo.sh` | Cal example: `https://calendar.delo.sh`. |
| API URL | `https://api.<service>.delo.sh` | Cal example: `https://api.calendar.delo.sh`. |
| Cloudflare Tunnel ID | `6dfd95af-6e2a-4833-84b8-e0a1fda5da4a` | Routes `*.delo.sh` and apex → Traefik. |
| Tunnel config | `~/docker/stacks/cloudflare-tunnel/config.yml` | If a route is missing, edit here. |
| Reverse proxy | Traefik at `~/docker/core/traefik` | Compose at `compose.yml`, dynamic at `traefik-data/dynamic/`. |

## Docker networks

| Network | Purpose | Declaration in stack compose |
|---|---|---|
| `proxy` | Traefik-attached. Required for any container that needs `<svc>.delo.sh` exposure. | `networks: { proxy: { external: true } }` and attach the service. |
| stack-internal (per project) | DB ↔ app, redis ↔ app, etc. | Whatever the project calls it (`stack`, `default`, etc.); fine to keep. |

A container can join multiple networks. The web tier almost always joins both its stack network AND `proxy`.

## 1Password (DeLoSecrets vault)

| Concept | Value |
|---|---|
| Vault name | `DeLoSecrets` |
| Vault ID | `ogoabqae7c6xgdbl5wccfwcnke` |
| Reference syntax | `op://DeLoSecrets/<ItemName>/<fieldName>` |
| Op runner | `op run --env-file .env.op -- <cmd>` |
| Op resolve test | `op run --env-file .env.op -- env \| grep <KEY>` |

### Known reusable items

| Item | Common fields | Use for |
|---|---|---|
| `PostgresLocal` | `username` (=delorenj), `password` | Default DB creds; reuse for any "first user" requirement. |
| `Resend API Key` | `credential` | SMTP fallback when Cloudflare email routing is overkill. |
| `Cloudflare (delonet)` | `api_token`, `dns_api_token`, `zone_id`, `email` | DNS, Turnstile, Tunnel auth. |
| `DeLoDrive (MinIO)` | `access_key`, `secret_key` | S3 buckets for video, uploads, etc. |
| `Twilio` | `account_sid`, `auth_token` | SMS, voice (Cal.ai). |
| `Stripe` | `secret_key`, `webhook_secret`, `publishable_key` | Billing, only when explicitly needed. |
| `Google` | `client_id`, `client_secret`, `api_key` | Google Calendar, OAuth login. |
| `Hindsight` | `api_key` | Memory recall. |
| `Tailscale` | `auth_key` | New machine join. |

> Verify field names with `op item get "<Item>" --vault DeLoSecrets --format json` — don't guess.

### Default credentials

For services that just need "a user" (admin seed, db init, basic auth):

```
op://DeLoSecrets/PostgresLocal/username   →  delorenj
op://DeLoSecrets/PostgresLocal/password   →  (the canonical default)
```

Shell fallback (legacy, exported by `~/.config/zshyzsh/secrets.zsh`):

```
$DEFAULT_USERNAME   = delorenj
$DEFAULT_PASSWORD   = (same as PostgresLocal/password)
$RESEND_API_KEY
$MINIO_ACCESS_KEY   = delorenj
$MINIO_SECRET_KEY   = (same as DEFAULT_PASSWORD)
```

When you see a value referenced via `$VAR` in an existing stack, prefer migrating to `op://` going forward.

## Object storage (MinIO)

| Concept | Value |
|---|---|
| S3 API endpoint | `https://s3.delo.sh` (the real S3-compatible URL) |
| Web console | `https://drive.delo.sh` (browser only — do NOT pass to SDKs) |
| Default region | `us-east-1` (MinIO ignores it but most SDKs require *something*) |
| Credentials | `op://DeLoSecrets/DeLoDrive (MinIO)/accessKey` + `secretKey`, or `$MINIO_ACCESS_KEY`/`$MINIO_SECRET_KEY` |
| Bucket naming | `<service>-<purpose>`, lowercase, hyphens. Examples: `cal-video`, `chorescore-uploads`, `n8n-binary`. |

## Email

| Use | Approach | Notes |
|---|---|---|
| Service "from" address | `notifications@<service>.delo.sh` (or `no-reply@<service>.delo.sh`) | Service-themed, not personal. |
| Service "from" name | `<Service Name>` (e.g. `Calendar`, `ChoreScore`) | Brand-aligned. |
| Personal | `jaradd@gmail.com` | Only when the service legitimately speaks for Jarad. |
| SMTP host | `smtp.resend.com` | Port `465`, secure `true`. |
| SMTP user | `resend` | Literal string `resend`. |
| SMTP password | `op://DeLoSecrets/Resend API Key/credential` | API key. |
| Inbound mail | Cloudflare Email Routing | Configure in Cloudflare zone settings, not in app env. |

## Filesystem layout (delonet)

| Path | Purpose |
|---|---|
| `~/docker/core/<svc>` | Core infra (traefik, postgres, redis, etc.) |
| `~/docker/stacks/<svc>` | Application stacks |
| `~/code/<repo>` | Active development |
| `~/.config/zshyzsh/` (= `$ZC`) | Shell config & legacy secrets (`secrets.zsh`) |
| `~/.local/bin/` | Symlinked scripts from `$ZC/scripts/` |
