#!/usr/bin/env bash
# DeLoHome preflight — "what is actually working right now", in one command.
#
# Everything in this house fails in a way that looks like something else: a panel that is
# merely asleep looks unreachable, a missing credential looks like a broken domain, and a
# stale IP looks like a dead device. This separates those before you start debugging the
# wrong layer.
#
# Read-only. Sends nothing to any device beyond a TCP connect and an unauthenticated read.

set -uo pipefail

REPO="${DELOHOME_REPO:-$HOME/code/DeLoHome}"
ok=0 warn=0 bad=0

c_ok()   { printf '  \033[32m ok \033[0m %s\n' "$1"; ok=$((ok+1)); }
c_warn() { printf '  \033[33mwarn\033[0m %s\n' "$1"; warn=$((warn+1)); }
c_bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; bad=$((bad+1)); }
head()   { printf '\n\033[1m%s\033[0m\n' "$1"; }

head "Tooling"
if command -v delohome >/dev/null 2>&1; then
  c_ok "delohome on PATH ($(command -v delohome))"
else
  c_bad "delohome not on PATH — uv tool install --force --reinstall $REPO"
fi
[ -d "$REPO" ] && c_ok "repo at $REPO" || c_bad "repo not found at $REPO (set DELOHOME_REPO)"
command -v op >/dev/null 2>&1 && c_ok "op present" || c_bad "1Password CLI not installed"

head "Credentials (resolved, never printed)"
probe_secret() { # name, op-ref
  local v
  v="$(op read "$2" 2>/dev/null)"
  if [ -n "$v" ]; then c_ok "$1 resolves (${#v} chars)"; else c_warn "$1 MISSING — see references/setup.md"; fi
}
if command -v op >/dev/null 2>&1; then
  probe_secret "Hue app key"      "op://DeLoSecrets/mf5sqxr544cmzcyeoc7pxfmzsu/credential"
  probe_secret "Jellyfin token"   "op://DeLoSecrets/2aym4v3pqkyjzey2i5ivjewedi/credential"
  probe_secret "Samsung token"    "op://DeLoSecrets/jqvhzxoo2rx6hmue6l7ncfwoza/credential"
else
  c_warn "skipping credential checks — no op binary"
fi

head "Hardware reachability"
# A TCP connect only. Nothing is sent, nothing is changed.
port_open() { timeout 2 bash -c "echo > /dev/tcp/$1/$2" 2>/dev/null; }
probe() { # label, ip, port, hint
  if port_open "$2" "$3"; then c_ok "$1 ($2:$3)"; else c_warn "$1 ($2:$3) not answering — $4"; fi
}
probe "Hue bridge"        192.168.1.13 443  "bridge unplugged?"
probe "Jellyfin"          192.168.1.12 8096 "container down? docker start jellyfin"
probe "Samsung bedroom"   192.168.1.4  8001 "deep standby — it leaves the LAN entirely when off"
probe "LG office"         192.168.1.11 3001 "TV off; note 3000 accepts then drops the upgrade"
probe "LG ava"            192.168.1.42 3001 "TV off"
probe "Fire TV living"    192.168.1.3  5555 "TV asleep"
# NOT a port probe: something else on this host already listens on 0.0.0.0:3000, so
# "port open" would cheerfully report a sidecar that does not exist.
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'zwave-js'; then
  c_ok "zwave-js sidecar (container up)"
elif port_open 127.0.0.1 3000; then
  c_warn "zwave-js sidecar NOT running — but something else holds :3000; mise run up"
else
  c_warn "zwave-js sidecar not running — mise run up (Z-Wave tools will report unavailable)"
fi

head "Cast devices"
for entry in "Dommy's TV:192.168.1.24" "Chase's TV:192.168.1.29" "Shield:192.168.1.34" \
             "Playroom:192.168.1.16" "Computer Room:192.168.1.8" \
             "Kitchen speaker:192.168.1.9" "Bedroom speaker:192.168.1.5"; do
  name="${entry%%:*}"; ip="${entry##*:}"
  if port_open "$ip" 8009; then c_ok "$name ($ip)"; else c_warn "$name ($ip) unreachable — unplugged, or the lease moved: mise run discover"; fi
done

head "Domains"
if command -v delohome >/dev/null 2>&1; then
  if out="$(delohome --json 2>/dev/null)"; then
    read -r -d '' PY_DOMAINS <<'PY' || true
import json, sys
try:
    rows = json.load(sys.stdin)
except Exception as exc:
    print(f"  warn could not parse domain list ({type(exc).__name__})")
    sys.exit(0)
if isinstance(rows, dict):
    rows = rows.get("result", rows)
for d in rows:
    name = d.get("domain", "?")
    count = d.get("tool_count", 0)
    if d.get("status") == "ok":
        print(f"   ok  {name:9} {count} tools")
    else:
        print(f"  FAIL {name:9} {d.get('error', '')[:70]}")
PY
    printf '%s\n' "$out" | python3 -c "$PY_DOMAINS"
  else
    c_bad "delohome failed to start — run it directly to see why"
  fi
else
  c_warn "skipping domain check — delohome not on PATH"
fi

head "Panels paired"
if command -v delohome >/dev/null 2>&1; then
  read -r -d '' PY_PANELS <<'PY' || true
import json, sys
try:
    rows = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if isinstance(rows, dict):
    rows = rows.get("result", rows)
for d in rows:
    key = d.get("display", "?")
    if "error" in d:
        print(f"  FAIL {key:16} {d['error'][:60]}")
        continue
    proto = d.get("protocol", "")
    if d.get("paired"):
        print(f"   ok  {key:16} {proto:12} paired")
    else:
        print(f"  warn {key:16} {proto:12} NOT PAIRED - see references/setup.md")
PY
  delohome displays list-displays --json 2>/dev/null | python3 -c "$PY_PANELS"
fi

printf '\n\033[1mSummary\033[0m  %d ok, %d warn, %d fail\n' "$ok" "$warn" "$bad"
printf 'A "warn" on a TV usually just means it is off. A "FAIL" is a real problem.\n'
[ "$bad" -eq 0 ]
