---
name: delonet-dotenv
description: Fill .env and .env.op for Docker Compose stacks on big-chungus (delonet, *.delo.sh). Splits non-secret literals into .env and 1Password references into .env.op (resolved via `op run`). Covers Postgres host selection (stack-internal vs host.docker.internal:5432), Traefik routing on the proxy network with Host(`<svc>.delo.sh`) labels, port-collision avoidance (avoid 3000, pick 13000-25000), default creds from op://DeLoSecrets/PostgresLocal, MinIO S3 at drive.delo.sh, Cloudflare-first DNS/Turnstile, Resend SMTP, service-themed from-addresses (notifications@<svc>.delo.sh). Use when populating env vars for a new docker-compose stack on big-chungus, deciding where a secret lives (op vault vs shell vs literal), wiring traefik for a *.delo.sh subdomain, or authoring .env.op 1Password references. Do NOT use for Vercel/Render/Fly/cloud-only deploys, GitHub Actions secrets, Kubernetes manifests, or non-delonet hosts.
pipeline-status:
  - new
---

# delonet-dotenv

> Choose-your-own-adventure for filling env vars on Jarad's big-chungus server. The body is a routing surface — every section ends with "for X, read references/Y.md". Stop reading the moment your decision is made.

## Operating principles

- **Two-file split.** Non-secrets go in `.env`. Secrets go in `.env.op` as `op://DeLoSecrets/<Item>/<field>` references; resolve at run time with `op run --env-file .env.op -- docker compose up`. Never paste raw secrets into `.env`.
- **delo.sh by default.** Public hostname = `<service>.delo.sh`. API subdomain = `api.<service>.delo.sh`. Cloudflare Tunnel routes both into Traefik — no port-forward, no public IP, no certs to manage.
- **Cloudflare wins ties.** Resend exists as SMTP fallback, but for DNS, Turnstile, R2, email routing, etc., Cloudflare beats every alternative.
- **Container-to-container by service name** (e.g. `postgres`, `redis`). LAN IPs in env files are stale and must be replaced (see [gotchas.md](references/gotchas.md)).
- **Port assumption is bug.** Big-chungus is busy. If the stack must bind a host port, pick something in 13000-25000. Better: skip the host bind and let Traefik route via the proxy network.

## Routing table

| You're filling… | Read |
|---|---|
| any env value (lookup the magic numbers: IPs, hostnames, paths, vault) | [references/constants.md](references/constants.md) |
| DB url, port, email host, S3 bucket, OAuth, brand strings | [references/decisions.md](references/decisions.md) |
| anything that looks like a secret/key/token/password | [references/secrets-vault.md](references/secrets-vault.md) |
| `NEXT_PUBLIC_WEBAPP_URL`, `*_URL`, `ALLOWED_HOSTNAMES`, port binding, traefik labels | [references/traefik-routing.md](references/traefik-routing.md) |
| stack won't start, 502, db connection refused, op resolves to empty | [references/gotchas.md](references/gotchas.md) |

## The 60-second decision tree

```
Encounter an env var. Ask in order:

1. Is it a SECRET? (key, token, password, api_key, encryption_key, webhook_secret)
   YES → put `op://DeLoSecrets/<Item>/<field>` in .env.op, leave .env blank.
         → If item doesn't exist in vault: create it with `op item create`.
         → For routine creds, reuse op://DeLoSecrets/PostgresLocal/{username,password}.
         → See secrets-vault.md.
   NO  → put the literal value in .env.

2. Is it a URL/hostname for THIS stack?
   Public-facing? → https://<service>.delo.sh   (api → https://api.<service>.delo.sh)
   Container-internal? → service name (postgres, redis, calcom, etc.)
   Same host on the LAN? → host.docker.internal (NOT 192.168.1.12, NOT localhost)
   See traefik-routing.md.

3. Is it a PORT?
   Container internal port? → leave at framework default.
   Host bind? → don't, unless absolutely required. If required: 13000-25000, never 3000/5432/6379/80/443/8080.

4. Is it a DATABASE_URL?
   Stack ships its own postgres? → postgresql://<user>:<pass>@postgres:5432/<db>  (stack-internal)
   Need to share an external postgres? → postgresql://<user>:<pass>@host.docker.internal:5432/<db>
   See decisions.md > database.

5. Is it an EMAIL FROM address?
   Service-themed: notifications@<service>.delo.sh, no-reply@<service>.delo.sh
   Personal: jaradd@gmail.com (only when the service legitimately speaks for Jarad).

6. Is it an S3 bucket / object storage?
   → MinIO at https://drive.delo.sh, bucket = <service>-<purpose>, region = us-east-1.
   → Credentials: op://DeLoSecrets/DeLoDrive (MinIO)/{access_key,secret_key} or $MINIO_ACCESS_KEY.

7. Is it telemetry / analytics / Sentry / Posthog?
   → Leave blank unless the user explicitly asks for it. Self-hosted = no third-party telemetry.

8. Is it OAuth (Google / Microsoft / etc.)?
   → Leave blank for first boot. Backfill after the stack is verified up.
   → When ready: op://DeLoSecrets/Google/* etc.
```

## Constants you'll need every time

| Concept | Value |
|---|---|
| Host | `big-chungus` |
| LAN IP | `192.168.1.12` (LAN only — prefer `host.docker.internal`) |
| Tailscale | `100.66.29.76` / `big-chungus.burro-salmon.ts.net` |
| Public domain root | `delo.sh` (Cloudflare zone) |
| Reverse proxy | Traefik at `~/docker/core/traefik` |
| Public-facing network | `proxy` (external: true) — required for *.delo.sh |
| Cloudflare Tunnel | routes `*.delo.sh` → Traefik (no public IP) |
| Default user/pass | `$DEFAULT_USERNAME` / `$DEFAULT_PASSWORD` (also `op://DeLoSecrets/PostgresLocal/*`) |
| 1Password vault | `DeLoSecrets` |
| Op file pattern | `op://DeLoSecrets/<ItemName>/<fieldName>` |
| Op runner | `op run --env-file .env.op -- <cmd>` |
| Shell secrets fallback | `~/.config/zshyzsh/secrets.zsh` (legacy — migrate to op when seen) |
| Personal email | `jaradd@gmail.com` |
| MinIO S3 API | `https://s3.delo.sh` (web console at `drive.delo.sh`) |

Full table with provenance and edge cases: [constants.md](references/constants.md).

## Cross-cutting rules

- **Secrets must NEVER live in `.env`.** If a key looks secret-shaped (`*_KEY`, `*_SECRET`, `*_TOKEN`, `*_PASSWORD`, `*_DSN`, `DATABASE_URL` containing a password), it goes in `.env.op` only.
- **Generate on demand.** `NEXTAUTH_SECRET`, `*_ENCRYPTION_KEY`, `CRON_API_KEY`, etc. → `openssl rand -base64 32` (or 24 for AES256). Store generated values in op as a new item, then reference.
- **`.env.op` is committable.** It contains references, not secrets. `.env` is `.gitignore`d.
- **Quote ALLOWED_HOSTNAMES correctly.** Cal-style: `'"calendar.delo.sh","localhost:3000"'` (outer single, inner double, comma-separated).
- **Traefik label presence ⇒ proxy network membership.** Always pair them. A container with traefik labels but not on the `proxy` network is invisible to Traefik.
- **Don't invent items in op.** If `op item get "<Name>" --vault DeLoSecrets` fails, create the item with `op item create` — don't guess at field names.

## Workflow

1. Read the stack's `.env.example` (or upstream env documentation). Identify every var.
2. For each var, run the 60-second decision tree above. When uncertain, jump to the matching reference.
3. Write non-secrets into `.env`. Write op:// references into `.env.op`.
4. If the stack needs to be reachable at `<service>.delo.sh`, drop a `docker-compose.override.yml` per [traefik-routing.md](references/traefik-routing.md).
5. Verify: `op run --env-file .env.op -- env | grep -E '^(DATABASE|NEXTAUTH|CALENDSO|...)'` — all secrets resolve to non-empty values.
6. Bring up: `op run --env-file .env.op -- docker compose up -d`.
7. Curl the public URL: `curl -I https://<service>.delo.sh`. Expect 200 or a framework-appropriate redirect.

## Out of scope

- **Vercel, Render, Fly, AWS, GCP env management.** Those are platform-managed; this skill is for big-chungus self-hosting only. Use the platform's secret manager.
- **GitHub Actions / CI secrets.** Use `gh secret set` and the repo's secrets UI; don't commit `.env.op` references for CI use cases.
- **Kubernetes manifests / Helm values.** Use SealedSecrets, External Secrets Operator, or the cluster's secret store.
- **Non-DeLoNET environments** (work laptops, customer machines, ephemeral dev VMs). The constants in this skill assume `big-chungus.burro-salmon.ts.net`.
- **Generating the docker-compose itself from scratch.** That's the `stacks-deploy` skill's job. This skill assumes a compose file already exists.
- **Shell-level secret loading via `secrets.zsh`.** Treated as legacy fallback; this skill migrates secrets toward op.
