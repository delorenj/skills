---
pipeline-status:
  - new
---
# Decisions

Branching answers to common env-var questions. Each section is independent — jump to the one that matches your current var.

## Database

### Stack ships its own Postgres (default)

Use the service name as host. Most opinionated stacks ship a `postgres` service in compose; reuse it.

```
DATABASE_URL=postgresql://<user>:<pass>@postgres:5432/<db>
```

- Username/password via op references (or shell fallback). Stack-internal DBs are isolated from the rest of the network so reusing default creds is fine.
- Database name: match the project (`calendso`, `chorescore`, `n8n`, etc.).
- If the stack also wants `DATABASE_DIRECT_URL` (Prisma + pgbouncer pattern), set it equal to `DATABASE_URL` unless an actual pooler is configured.

### Share the self-hosted external Postgres

When you want the data persisted in the central postgres (so it survives stack rebuilds, joins backups, etc.):

```
DATABASE_URL=postgresql://<user>:<pass>@host.docker.internal:5432/<db>
```

- Host MUST be `host.docker.internal` (NOT `192.168.1.12`, NOT `localhost`, NOT `postgres`).
- Add `extra_hosts: ["host.docker.internal:host-gateway"]` to the compose service if it isn't already.
- Create the DB and user first: `psql -h localhost -U postgres -c 'CREATE DATABASE <db>;'`.
- Either reuse `op://DeLoSecrets/PostgresLocal/{username,password}` (preferred for app-level access) or create a per-app role.
- Drop the in-stack `postgres` service from compose to avoid confusion.

### Pgbouncer / connection pooler

If the upstream stack documents pgbouncer-style pooling, point `DATABASE_URL` at the pooler and `DATABASE_DIRECT_URL` at the unpooled connection. There's no shared pgbouncer on big-chungus by default; spin one up only if the workload demands it.

## Redis

```
REDIS_URL=redis://redis:6379/0
```

Almost always stack-internal. If the stack needs a long-lived shared cache, run a dedicated `redis` core service rather than reusing one across stacks (eviction policies and DB-number conflicts cause subtle bugs).

## Hostnames & URLs

For any `*_URL`, `*_HOST`, `NEXT_PUBLIC_*_URL`:

| The URL is for… | Set to |
|---|---|
| The web app, public | `https://<service>.delo.sh` |
| The web app, local dev only | `http://localhost:<port>` |
| The API, public | `https://api.<service>.delo.sh` |
| Inter-container (DB, Redis, app↔api) | service name (`postgres`, `redis`, `calcom-api`) |
| Webhook callbacks the OUTSIDE world hits | `https://<service>.delo.sh/webhooks/...` |
| `ALLOWED_HOSTNAMES` / CORS allowlist | the public hostname, comma-separated, properly quoted |

## Ports

The default answer is "do not bind a host port." If the container only needs to be reached via Traefik (HTTPS at `<svc>.delo.sh`), join it to the `proxy` network and use Traefik labels — no `ports:` entry needed.

If you MUST bind a host port (e.g. raw TCP, non-HTTP protocol, debug):

- Pick a port in **13000–25000**.
- Confirm it's free: `ss -ltn | grep <port>` (no rows = free).
- Never assume free: `3000`, `3001`, `5432`, `6379`, `80`, `443`, `8080`, `8000`, `5000`, `9000`.
- Document the chosen port in the stack's README.

## Email / SMTP

For a service that needs to send notifications:

```
EMAIL_FROM=notifications@<service>.delo.sh
EMAIL_FROM_NAME=<Service Name>
EMAIL_SERVER_HOST=smtp.resend.com
EMAIL_SERVER_PORT=465
EMAIL_SERVER_USER=resend
EMAIL_SERVER_PASSWORD=op://DeLoSecrets/Resend API Key/credential
```

- Tuck the password in `.env.op`, leave a blank line in `.env`.
- DNS records for the from-address (`<service>.delo.sh` SPF/DKIM/DMARC) are managed in Cloudflare. Resend's onboarding will hand you the records — paste them into Cloudflare DNS for the `delo.sh` zone.

For receive-only (forms, reply-to inboxes): use Cloudflare Email Routing — no app config needed.

## Object storage / S3

When a stack wants S3 (Daily Video recordings, user uploads, document storage, etc.):

```
<PREFIX>_BUCKET_NAME=<service>-<purpose>      # e.g. cal-video, chorescore-uploads
<PREFIX>_BUCKET_REGION=us-east-1               # MinIO ignores it; SDKs require it
<PREFIX>_S3_ENDPOINT=https://s3.delo.sh        # S3-compatible API endpoint
<PREFIX>_ACCESS_KEY_ID=op://DeLoSecrets/DeLoDrive (MinIO)/accessKey
<PREFIX>_SECRET_ACCESS_KEY=op://DeLoSecrets/DeLoDrive (MinIO)/secretKey
```

Create the bucket: `mc mb local/<service>-<purpose>` (or via the MinIO web console at `https://drive.delo.sh`). The web console is at `drive.delo.sh`; the S3 API is at `s3.delo.sh` — pass `s3.delo.sh` to SDKs.

If the stack requires AWS-style IAM `AssumeRole`, MinIO can't do that — pick a different approach (presigned URLs, direct credentials).

## OAuth (Google / Microsoft / etc.)

Default: leave blank. Most stacks degrade gracefully and you can backfill once the app is up and you can log in via password.

When ready:

- **Google**: console at `console.cloud.google.com`. Set up OAuth consent (Internal if it's just for delonet users), create credentials, store as `op://DeLoSecrets/Google/<service>-{client_id,client_secret}`.
- **Microsoft**: Azure portal → Entra ID → App Registrations.

Redirect URIs go to `https://<service>.delo.sh/api/auth/callback/<provider>`.

## Telemetry / analytics / Sentry / Posthog / Intercom

Default: blank. Self-hosted = no third-party telemetry beans spilled. If a stack hard-requires a value:

- Use a self-hosted alternative if available (e.g. self-hosted Posthog at `posthog.delo.sh` if you stand one up).
- Otherwise leave at the upstream default and accept the warning at boot.

## Brand strings

| Var pattern | Value |
|---|---|
| `*_APP_NAME` / `BRAND_NAME` | The service's name, capitalized as it should appear in UI (e.g. `Calendar`, not `Cal.diy`). |
| `*_COMPANY_NAME` | `delonet` (or service-specific if the user has registered a brand). |
| `*_SUPPORT_EMAIL` | `support@<service>.delo.sh` (or `jaradd@gmail.com` for personal). |
| `*_PRIVACY_URL` / `*_TERMS_URL` | Blank by default. Add when the user explicitly wants legal pages. |

## Cloudflare Turnstile (anti-bot)

Off by default for self-hosted use. To enable:

```
NEXT_PUBLIC_CLOUDFLARE_SITEKEY=op://DeLoSecrets/Cloudflare (delonet)/turnstile_sitekey
CLOUDFLARE_TURNSTILE_SECRET=op://DeLoSecrets/Cloudflare (delonet)/turnstile_secret
```

Sitekey is technically public but storing it in op keeps the surface uniform.

## Cron / webhook secrets

`CRON_API_KEY`, `WEBHOOK_TOKEN`, etc. — generate fresh and store in op:

```bash
val=$(openssl rand -base64 32)
op item create --vault DeLoSecrets --category 'API Credential' \
  --title "<Service> CRON_API_KEY" credential="$val"
# then in .env.op:
# CRON_API_KEY=op://DeLoSecrets/<Service> CRON_API_KEY/credential
```

## Encryption keys

`*_ENCRYPTION_KEY`, `NEXTAUTH_SECRET`:

- 32 bytes for AES256 → `openssl rand -base64 24`
- 32 chars random → `openssl rand -base64 32`
- Generate ONCE per environment. Rotating these invalidates existing sessions, encrypted credentials, and webhook history. Treat as durable.

## Trigger.dev / async tasker

Off by default (`ENABLE_ASYNC_TASKER=false`). Cal.diy and similar stacks fall back to inline execution, which is fine for self-hosted single-tenant use.
