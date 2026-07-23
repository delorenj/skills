---
name: spa-host
description: >
  Host a static site / SPA at a *.delo.sh subdomain on the homelab (big-chungus) using
  the proven "domipacolypse" one-off pattern — an nginx:alpine container on the external
  `proxy` network with Traefik labels, fronted by the Cloudflare Tunnel. Use when the user
  wants to publish, deploy, host, or "put online" a static site / built front-end at a
  delo.sh subdomain, point a delo.sh subdomain at a folder, spin up a quick one-off web
  host, or take one down. Triggers: "host X at foo.delo.sh", "spa-host foo.delo.sh",
  "deploy this static site to delo.sh", "serve ./dist at a subdomain".
---

# spa-host — one-off static hosting at `*.delo.sh`

Publishes a folder of static files at `https://<name>.delo.sh` in one step, using Jarad's
existing homelab ingress. This is **personal-infra tooling** — it assumes big-chungus with
Traefik + the Cloudflare Tunnel running. It is intentionally global (not tied to any repo).

## How the plumbing works (why this is a one-liner)

```
Internet → Cloudflare (wildcard *.delo.sh DNS, proxied)
         → Cloudflare Tunnel  (ingress: *.delo.sh → https://traefik:443)
         → Traefik            (routes by Host label, terminates TLS via Let's Encrypt DNS-01)
         → your nginx:alpine container  (on the `proxy` network, serving your folder)
```

Because a **wildcard `*.delo.sh` DNS record** and a **wildcard `*.delo.sh` tunnel ingress**
already exist, a *single-label* subdomain like `lego.delo.sh` needs **no DNS and no tunnel
changes** — dropping the labeled container on the `proxy` network is enough. Traefik mints a
real cert on first request via the Cloudflare **DNS-01** challenge (so the origin never has to
be publicly reachable). The reference example is `~/docker/stacks/websites/domipacolypse/`.

## Prerequisites (verify, don't assume)

- `docker` reachable, and the external network exists: `docker network inspect proxy`
- Traefik + tunnel up: `docker ps | grep -E 'traefik|cloudflare-tunnel'`
- The subdomain resolves (wildcard): `getent hosts <name>.delo.sh` → Cloudflare IPs.
- The folder to serve exists and contains `index.html`.

## Usage

The work is done by `spa-host.sh` (next to this file). It is idempotent — re-running updates
the stack in place.

```bash
~/.claude/skills/spa-host/spa-host.sh <domain> <static-dir>
# e.g.
~/.claude/skills/spa-host/spa-host.sh lego.delo.sh /home/delorenj/code/legofirst/apps/web
```

Tear a host down:

```bash
~/.claude/skills/spa-host/spa-host.sh <domain> --down
```

## What the script does

1. Derives a docker-safe stack/router name from the domain (`lego.delo.sh` → `lego`).
2. Guards against **nested** subdomains (`x.y.delo.sh`) — the wildcard ingress matches only
   one label, so it prints the exact tunnel-ingress rule to add + reminds you to restart the
   tunnel. Single-label subdomains need nothing extra.
3. Writes `~/docker/stacks/websites/<name>/compose.yml` from the domipacolypse template
   (nginx:alpine, read-only bind-mount of `<static-dir>` → `/usr/share/nginx/html`, on the
   `proxy` network, with the five Traefik labels: enable, Host rule, websecure entrypoint,
   letsencrypt certresolver, loadbalancer port 80, docker network proxy).
4. `docker compose up -d`.
5. Polls `https://<domain>` until it returns 200 (first cert issue can take ~90–120s because
   Traefik's resolver has `delayBeforeCheck: 90`).

The bind-mount is **live** — editing files in `<static-dir>` updates the site on refresh, no
rebuild. Perfect for a static SPA whose per-deploy config (e.g. a git-ignored `config.js`)
lives right in that folder.

## When driving this as an LLM

1. Get the two args. If the user gave only a domain, ask for (or infer) the static dir — the
   folder containing `index.html` (a repo's `apps/web`, a build's `dist/`, etc.).
2. Run the script. Relay its ✓/⚠ output.
3. If it ends on ⚠ (cert still minting), wait ~60s and `curl -I https://<domain>` once more
   before reporting; only escalate to Traefik logs if it still isn't 200.
4. Report the live URL. Never paste secrets; the folder's `config.js`/`.env` are the user's.

## Notes & guardrails

- **Single base zone: `delo.sh`.** For a different zone, this pattern doesn't apply as-is.
- **Don't publish someone else's or sensitive content** without the user's ok — this makes it
  publicly reachable on the internet.
- **Teardown** stops the container but leaves the stack dir; `rm -rf ~/docker/stacks/websites/<name>`
  to remove it entirely.
- If `getent hosts <domain>` doesn't resolve, the wildcard DNS record may be missing — add a
  proxied CNAME `<name>` → `<tunnel-id>.cfargotunnel.com` in Cloudflare (tunnel id in
  `~/docker/core/cloudflare-tunnel/config.yml`).
