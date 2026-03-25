#!/usr/bin/env bash
# Quick health check for the monitoring stack
# Usage: bash scripts/stack-health.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
    local name="$1" url="$2"
    if curl -sf "$url" > /dev/null 2>&1; then
        printf "${GREEN}OK${NC}  %s\n" "$name"
    else
        printf "${RED}FAIL${NC}  %s (%s)\n" "$name" "$url"
    fi
}

echo "=== Monitoring Stack Health ==="
echo ""
check "Prometheus"       "http://localhost:9472/-/healthy"
check "Alertmanager"     "http://localhost:9784/-/healthy"
check "Grafana"          "http://localhost:9831/api/health"
check "cadvisor"         "http://localhost:9264/healthz"
check "node-exporter"    "http://localhost:9519/metrics"
check "process-exporter" "http://localhost:9256/metrics"
check "Loki"             "http://localhost:3100/ready"
check "Dockge"           "http://localhost:14654"
check "Uptime Kuma"      "http://localhost:13556"

echo ""
echo "=== Alert Rules Loaded ==="
RULE_COUNT=$(curl -s http://localhost:9472/api/v1/rules 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = sum(len(g['rules']) for g in data['data']['groups'])
print(count)
" 2>/dev/null || echo "0")
echo "Total rules: $RULE_COUNT"

echo ""
echo "=== Firing Alerts ==="
curl -s http://localhost:9472/api/v1/alerts 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
firing = [a for a in data['data']['alerts'] if a['state'] == 'firing']
if not firing:
    print('None')
else:
    for a in firing:
        print(f'  {a[\"labels\"][\"alertname\"]} [{a[\"labels\"].get(\"severity\",\"?\")}]')
" 2>/dev/null || echo "Could not reach Prometheus"

echo ""
echo "=== Telegram Bot ==="
BOT_TOKEN=$(grep bot_token ~/docker/stacks/monitoring/alertmanager/config.yml 2>/dev/null | head -1 | awk -F"'" '{print $2}')
if [ -n "$BOT_TOKEN" ]; then
    RESULT=$(curl -sf "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['username'])" 2>/dev/null || echo "FAIL")
    printf "Bot: @%s\n" "$RESULT"
else
    echo "Bot token not found in alertmanager config"
fi
