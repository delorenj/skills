#!/usr/bin/env bash
# spa-host — host a static site at a *.delo.sh subdomain using the "domipacolypse"
# one-off pattern: an nginx:alpine container on the external `proxy` network with
# Traefik labels. Traefik terminates TLS (Let's Encrypt via Cloudflare DNS-01) and
# the Cloudflare Tunnel's wildcard `*.delo.sh` ingress routes to it. No DNS or tunnel
# edits are needed for a single-label subdomain — a wildcard DNS record already exists.
#
# Usage: spa-host.sh <domain> <static-dir> [--down]
#   <domain>      e.g. lego.delo.sh
#   <static-dir>  absolute path to a dir containing index.html (bind-mounted read-only)
#   --down        tear the host down instead of bringing it up
#
# Env overrides (rarely needed):
#   SPA_HOST_STACKS_DIR   where stacks live   (default: ~/docker/stacks/websites)
#   SPA_HOST_PROXY_NET    traefik network     (default: proxy)
set -euo pipefail

DOMAIN="${1:-}"
SRC="${2:-}"
ACTION="up"
[ "${3:-}" = "--down" ] && ACTION="down"
[ "${2:-}" = "--down" ] && { ACTION="down"; SRC=""; }

if [ -z "$DOMAIN" ]; then
  echo "usage: spa-host.sh <domain> <static-dir> [--down]" >&2
  exit 2
fi

STACKS="${SPA_HOST_STACKS_DIR:-$HOME/docker/stacks/websites}"
PROXY_NET="${SPA_HOST_PROXY_NET:-proxy}"
TUNNEL_CFG="$HOME/docker/core/cloudflare-tunnel/config.yml"

# Derive a docker-safe stack/router name: strip the .delo.sh zone, dots -> dashes.
NAME="$(printf '%s' "$DOMAIN" | sed -E 's/\.delo\.sh$//; s/[^a-zA-Z0-9]+/-/g' | tr 'A-Z' 'a-z')"
[ -n "$NAME" ] || NAME="site"
DIR="$STACKS/$NAME"

# ---- teardown ----
if [ "$ACTION" = "down" ]; then
  if [ -f "$DIR/compose.yml" ]; then
    docker compose -f "$DIR/compose.yml" down
    echo "✓ stopped $DOMAIN. Stack dir left at $DIR (rm -rf it to fully remove)."
  else
    echo "nothing to do — no stack at $DIR" >&2
  fi
  exit 0
fi

# ---- validate source ----
if [ -z "$SRC" ]; then
  echo "✗ need a static-dir to host. usage: spa-host.sh <domain> <static-dir>" >&2
  exit 2
fi
SRC="$(readlink -f "$SRC")"
[ -d "$SRC" ] || { echo "✗ static dir not found: $SRC" >&2; exit 1; }
[ -f "$SRC/index.html" ] || echo "⚠ no index.html in $SRC — nginx will 403 at '/'."

# ---- nested-subdomain guard (tunnel wildcard *.delo.sh matches ONE label only) ----
UNDER_ZONE="${DOMAIN%.delo.sh}"
if printf '%s' "$UNDER_ZONE" | grep -q '\.'; then
  PARENT="${UNDER_ZONE#*.}.delo.sh"
  echo "⚠ '$DOMAIN' is NESTED. The tunnel's '*.delo.sh' ingress only matches one label."
  echo "  Add this to $TUNNEL_CFG (above the http_status:404 catch-all) and restart the tunnel:"
  echo "    - hostname: \"*.$PARENT\""
  echo "      service: https://traefik:443"
  echo "      originRequest:"
  echo "        noTLSVerify: true"
  echo "  Otherwise DNS won't route to Traefik."
fi

# ---- preconditions ----
docker network inspect "$PROXY_NET" >/dev/null 2>&1 || {
  echo "✗ external docker network '$PROXY_NET' not found — is Traefik up?" >&2; exit 1; }

if [ -f "$DIR/compose.yml" ]; then
  echo "ℹ stack '$NAME' already exists at $DIR — updating it in place."
fi

# ---- write the stack (domipacolypse pattern) ----
mkdir -p "$DIR"
cat > "$DIR/compose.yml" <<YAML
services:
  ${NAME}-web:
    image: nginx:alpine
    container_name: ${NAME}-web
    restart: unless-stopped
    volumes:
      # Live read-only bind-mount — edits deploy on refresh, no rebuild
      - ${SRC}:/usr/share/nginx/html:ro
    networks:
      - ${PROXY_NET}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.${NAME}.rule=Host(\`${DOMAIN}\`)"
      - "traefik.http.routers.${NAME}.entrypoints=websecure"
      - "traefik.http.routers.${NAME}.tls.certresolver=letsencrypt"
      - "traefik.http.services.${NAME}.loadbalancer.server.port=80"
      - "traefik.docker.network=${PROXY_NET}"

networks:
  ${PROXY_NET}:
    external: true
YAML
echo "✓ wrote $DIR/compose.yml  ($DOMAIN → $SRC)"

# ---- bring it up ----
docker compose -f "$DIR/compose.yml" up -d
echo

# ---- verify (Let's Encrypt DNS-01 can take ~90-120s on first issue) ----
echo "→ https://$DOMAIN  (polling for a valid cert; first issue can take ~2 min)…"
for i in $(seq 1 24); do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "https://$DOMAIN" 2>/dev/null || echo 000)"
  if [ "$code" = "200" ] || [ "$code" = "304" ]; then
    echo "✓ live — HTTP $code at https://$DOMAIN"
    exit 0
  fi
  sleep 8
done
echo "⚠ not returning 200 yet (last: HTTP ${code:-000}). The container is up; the cert may"
echo "  still be minting. Re-check in a minute:  curl -I https://$DOMAIN"
echo "  Traefik logs:  docker logs traefik 2>&1 | grep -i -E 'acme|$NAME' | tail"
