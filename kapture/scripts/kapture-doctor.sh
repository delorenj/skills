#!/usr/bin/env bash
# Kapture preflight: is the server up, which tabs are actually drivable, and what to do.
#
# /tabs alone is not proof of life - a tab that has lost its content script is still
# listed there with a fresh lastPing and fails every command. So probe each tab with a
# real content-script round trip.
#
# Read-only: it lists tabs and runs one `elements?selector=title` per tab. Nothing mutates.
#
# Exit: 0 at least one live tab · 2 server up, no tabs · 3 tabs listed, all zombie
#       1 server down · 4 missing dependency

set -uo pipefail

K="${KAPTURE_URL:-http://127.0.0.1:61822}"

for dep in curl jq; do
  command -v "$dep" >/dev/null || { echo "kapture-doctor: $dep is required"; exit 4; }
done

TABS=$(curl -sf -m3 "$K/tabs" 2>/dev/null) || {
  cat <<EOF
KAPTURE DOWN   nothing answering at $K
  start it:    (setsid npx -y kapture-mcp@latest >/tmp/kapture.log 2>&1 &)
  then wait:   for i in \$(seq 20); do curl -sf -m1 $K/tabs >/dev/null && break; sleep 0.5; done
EOF
  exit 1
}

COUNT=$(jq 'length' <<<"$TABS")
if [ "$COUNT" -eq 0 ]; then
  cat <<EOF
KAPTURE UP     0 tabs connected
  for your own work, just open one (it self-connects in ~0.5s):
      T=\$(curl -s -X POST $K/tabs -d '{}' | jq -r .tabId)
      curl -s -X POST "$K/tab/\$T/navigate" -d '{"url":"https://example.com"}'
  to drive a tab the USER already has open, ask them to click the Kapture
  toolbar icon on it and flip the toggle (badge turns green).
EOF
  exit 2
fi

live=0
zombie=0
while read -r id; do
  r=$(curl -sf -m5 --get --data-urlencode "selector=title" "$K/tab/$id/elements" 2>/dev/null)
  if jq -e '.success == true' >/dev/null 2>&1 <<<"$r"; then
    live=$((live + 1))
    printf 'LIVE   %-12s %s\n' "$id" "$(jq -r '.title // "?"' <<<"$r")"
    printf '       %-12s %s\n' "" "$(jq -r '.url // "?"' <<<"$r")"
    printf '       %-12s domSize=%s viewport=%sx%s scrollY=%s\n' "" \
      "$(jq -r '.domSize // "?"' <<<"$r")" \
      "$(jq -r '.viewportDimensions.width // "?"' <<<"$r")" \
      "$(jq -r '.viewportDimensions.height // "?"' <<<"$r")" \
      "$(jq -r '.scrollPosition.y // "?"' <<<"$r")"
  else
    zombie=$((zombie + 1))
    printf 'ZOMBIE %-12s %s\n' "$id" \
      "$(jq -r '.error.message // .error // "no response"' <<<"$r" 2>/dev/null || echo 'no response')"
    printf '       %-12s %s\n' "" "$(jq -r --arg i "$id" '.[]|select(.tabId==$i)|.url' <<<"$TABS")"
  fi
done < <(jq -r '.[].tabId' <<<"$TABS")

echo
echo "$live live, $zombie zombie, $(curl -sf -m3 "$K/clients" | jq 'length') MCP clients sharing this browser"

if [ "$zombie" -gt 0 ]; then
  cat <<'EOF'

A zombie has an open socket but no content script in the page. Neither `reload` nor
`show` revives it - abandon that tabId. Open a fresh tab, or ask the user to reload
theirs and re-flip the toggle. DELETE /tab/{id} clears the stale entry.
EOF
fi

[ "$live" -gt 0 ] && exit 0 || exit 3
