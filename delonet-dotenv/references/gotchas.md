---
pipeline-status:
  - new
---
# Gotchas

Failure modes ranked by frequency. Each entry uses the four-part structure: **Symptom → Cause → Fix → Prevention**.

---

## 1. `op://` reference resolves to empty

**Symptom.** Container logs show `Error: NEXTAUTH_SECRET is required` (or any "missing required env var") even though `.env.op` references it.

**Cause.** One of:
- Item title in `.env.op` doesn't match the actual item in DeLoSecrets (case, parens, spaces).
- Field name doesn't match (commonly `password` vs `credential`, `api_key` vs `api_token`).
- The field exists but is empty in the vault.
- `op` CLI is signed out (`op account list` returns nothing).

**Fix.**
```bash
op read "op://DeLoSecrets/<Item>/<field>"   # should print the value
op item get "<Item>" --vault DeLoSecrets --format json | jq '.fields[] | {label,id}'
op signin   # if signed out
```

**Prevention.** Always run `op read` against each new reference before the first `docker compose up`.

---

## 2. Port 3000 collision on big-chungus

**Symptom.** `docker compose up` fails with `Error starting userland proxy: bind 0.0.0.0:3000 failed: port is already allocated`.

**Cause.** Big-chungus already runs something on 3000. Common offenders: an older n8n, a leftover dev server, another stack.

**Fix.** Either remove the host port binding entirely (let Traefik route via the proxy network — preferred) or remap to a high port:

```yaml
# docker-compose.override.yml
services:
  app:
    ports: []                       # preferred: no host bind
    # OR
    ports:
      - "13000:3000"                # remap to known-free high port
```

Then `ss -ltn | grep 13000` to confirm 13000 is free before binding.

**Prevention.** Never assume a low/common port is free. Default to no host bind + Traefik.

---

## 3. `host.docker.internal` doesn't resolve inside container

**Symptom.** App can't reach external Postgres at `host.docker.internal:5432`. Logs: `getaddrinfo ENOTFOUND host.docker.internal`.

**Cause.** On Linux, `host.docker.internal` is NOT automatic — Docker Desktop adds it, but plain Docker Engine on big-chungus doesn't.

**Fix.** Add to the service in compose:

```yaml
services:
  app:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

`host-gateway` is a Docker Engine magic string that resolves to the host's bridge IP at container start.

**Prevention.** Always pair `host.docker.internal` references in env with `extra_hosts` in compose.

---

## 4. LAN IP hardcoded — works today, breaks tomorrow

**Symptom.** Service worked from one container but not another, or stopped working after a router reboot.

**Cause.** A `192.168.1.12` (or worse, stale `10.0.0.12`) was hardcoded in env. Containers on Docker bridge networks may or may not route to the LAN; the IP changes if the router gives a different lease.

**Fix.** Replace with the right abstraction:
- Same host → `host.docker.internal` (with `extra_hosts`).
- Same compose stack → service name (`postgres`, `redis`).
- Cross-machine on tailnet → MagicDNS (`<machine>.burro-salmon.ts.net`).
- Across the public internet → `<svc>.delo.sh`.

**Prevention.** Grep for `192.168.` and `10.0.0.` in every .env you touch and replace.

---

## 5. Traefik labels but container is invisible

**Symptom.** `https://<svc>.delo.sh` returns `404 page not found` (Traefik default) or `502 Bad Gateway`.

**Cause.** Container isn't on the `proxy` network OR the `loadbalancer.server.port` doesn't match the port the app actually listens on.

**Fix.** Verify both:

```bash
docker inspect <container> --format '{{json .NetworkSettings.Networks}}' | jq 'keys'
# proxy must be in the list

docker exec <container> netstat -tlnp 2>/dev/null \
  || docker exec <container> ss -tlnp \
  || docker logs <container> | grep -i 'listening on'
# confirm the actual listen port matches what you put in the loadbalancer label
```

**Prevention.** When adding traefik labels, always pair them with the proxy network attachment AND verify the internal listen port (don't guess).

---

## 6. `ALLOWED_HOSTNAMES` parse error

**Symptom.** App boots but every page returns `Hostname not allowed` or similar.

**Cause.** Quoting is wrong. The value is parsed as a JSON-ish list of double-quoted strings.

**Fix.**

```
# Right:
ALLOWED_HOSTNAMES='"calendar.delo.sh","localhost:3000"'

# Wrong (no inner quotes):
ALLOWED_HOSTNAMES='calendar.delo.sh,localhost:3000'

# Wrong (whitespace):
ALLOWED_HOSTNAMES='"calendar.delo.sh", "localhost:3000"'
```

**Prevention.** Copy the format from the upstream `.env.example` and keep its quoting style.

---

## 7. Cloudflare DNS not propagated → `<svc>.delo.sh` 1003

**Symptom.** `curl https://<new>.delo.sh` returns Cloudflare 1003 ("Direct IP access not allowed") or NXDOMAIN.

**Cause.** New subdomain isn't covered by the wildcard CNAME, or the wildcard has been replaced by explicit per-subdomain entries that don't include this one.

**Fix.** In Cloudflare DNS for `delo.sh`, ensure either:
- A wildcard `*  CNAME  <tunnel-id>.cfargotunnel.com` (proxied), OR
- An explicit `<new>  CNAME  <tunnel-id>.cfargotunnel.com` (proxied) for this service.

**Prevention.** Confirm wildcard is intact when adding new subdomains. Tunnel ID is `6dfd95af-6e2a-4833-84b8-e0a1fda5da4a`.

---

## 8. Stale postgres data on rebuild

**Symptom.** After `docker compose down && docker compose up`, app complains about missing tables OR runs migrations against schema from a previous incompatible version.

**Cause.** The named volume (`database-data:`) persisted across the rebuild. If the upstream container changed major Postgres versions, the data dir is incompatible.

**Fix.** Decide intent:
- Want to keep data (production-ish): pin the postgres image to the version that wrote the data dir, or do a proper `pg_dump` → upgrade → `pg_restore`.
- Want a fresh DB (dev/first boot): `docker compose down -v` to drop volumes, then `docker compose up`.

**Prevention.** Pin postgres image major version explicitly (`postgres:16` not `postgres`). Treat the `-v` flag as destructive.

---

## 9. Secret accidentally committed in `.env`

**Symptom.** `git log -p .env` shows a secret value, or GitHub push protection rejects the push.

**Cause.** `.env` was edited with literal secret values instead of going through `.env.op`.

**Fix immediately.**
1. Rotate the secret in 1Password and at the source (Stripe, Resend, etc.).
2. Move it to `.env.op` as an op reference.
3. Purge from git history: `git rm --cached .env && git commit && git filter-repo --invert-paths --path .env` (or BFG).
4. Force-push the cleaned history (only if the user explicitly asks; this is destructive).

**Prevention.** `.env` must be in `.gitignore` (verify: `git check-ignore -v .env`). Treat any `*_KEY`/`*_SECRET`/`*_TOKEN` line in `.env` as an immediate refactor target.

---

## 10. Parking an upstream service behind a profile breaks `depends_on`

**Symptom.** After moving an upstream service (e.g. `database`) behind `profiles: ["inbuilt-db"]` in your override, `docker compose config` fails with `service "X" depends on undefined service "database": invalid compose project`.

**Cause.** Compose merges `depends_on` as a union — your override's `depends_on` is ADDED to upstream's, not replaced. Upstream's `depends_on: { database: ... }` still references the now-gated service, which is "undefined" without the profile flag.

**Fix.** Use the `!override` YAML tag (Compose v2.20+) to fully replace `depends_on`, not merge:

```yaml
services:
  calcom-api:
    depends_on: !override
      redis:
        condition: service_started

  calcom:
    depends_on: !override []   # zero dependencies
```

The `!override` tag tells the merger to take this value WHOLE instead of unioning with upstream. `!reset` only resets to default (often empty), but cannot be combined with a new value in the same key.

**Prevention.** Any time you `profiles:` an upstream service into hiding, audit ALL other services' `depends_on:` for references to it and `!override` them.

---

## 11. Stale shell vars shadow `.env` for compose build args

**Symptom.** Docker images bake in WRONG values for `NEXT_PUBLIC_*` build args (e.g. URLs point at `http://localhost:3000` after `docker compose build`) even though `.env` has the right values. `compose config` shows `build.args.X: http://localhost:3000` while `environment.X: https://calendar.delo.sh`.

**Cause.** Compose interpolates `${VAR}` against the SHELL ENVIRONMENT first, falling back to `.env` only if unset. A prior `yarn dev` session, an `mise` task, an opencode/claude-code shell, or any helper that exports `NEXT_PUBLIC_WEBAPP_URL` (or any other `${VAR}` referenced in compose's `build.args`) into the parent shell will silently override `.env`. The `environment:` section uses `env_file:` directly so it's NOT affected — only `${VAR}` interpolation is.

**Fix.** Re-source `.env` into the shell explicitly before invoking compose:

```bash
set -a && source .env && set +a && op run --env-file .env.op -- docker compose up -d
```

Or wrap it in a project script (`scripts/up.sh`) so the dance is a single command for users.

**Prevention.** Always use the `set -a; source .env; set +a;` prefix when running compose under `op run`. Don't rely on bare shells to be clean. If you see `compose config` showing different values for `build.args.X` vs `environment.X`, that's the smoking gun.

---

## 11. `op run` doesn't see the references

**Symptom.** `op run --env-file .env.op -- env | grep MY_KEY` shows `MY_KEY=op://DeLoSecrets/...` (the literal reference, not the resolved value).

**Cause.** Either:
- The op CLI is too old (`op --version` < 2.0).
- Not signed in to the right account (`op account list` shows zero or wrong accounts).
- File contains BOM or CRLF line endings → op parser treats lines as literals.

**Fix.**
```bash
op --version                # need >= 2.0; current at 2.31.1+ on big-chungus
op account list             # verify the right account
file .env.op                # should report ASCII text, no BOM
dos2unix .env.op            # if CRLF
```

**Prevention.** Author `.env.op` in a Unix-mode editor (vim, lazyvim, VSCode set to LF).
