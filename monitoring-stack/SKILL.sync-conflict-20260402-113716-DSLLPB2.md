---
name: monitoring-stack
description: >
  Manage the homelab monitoring stack at ~/docker/stacks/monitoring/.
  Services: Prometheus, Grafana, Alertmanager (Telegram via DeLoNETBot), cadvisor,
  node-exporter, process-exporter, Loki, OTEL collector, Dockge, Uptime Kuma, health-monitor.
  Use when: (1) adding, editing, or debugging Prometheus alert rules,
  (2) managing or restarting monitoring services, (3) checking alert delivery or Telegram bot status,
  (4) diagnosing system performance issues (CPU hogs, memory bloat, swap pressure),
  (5) adding new scrape targets to Prometheus, (6) configuring Grafana dashboards or datasources,
  (7) any task referencing "monitoring", "alerts", "prometheus", "grafana", "cadvisor",
  "process-exporter", "alertmanager", "telegram alerts", or "DeLoNETBot".
---

# Monitoring Stack

Stack root: `~/docker/stacks/monitoring/`

## Architecture

See [references/architecture.md](references/architecture.md) for full service map, ports, URLs, and data flow.

## Common Operations

### Restart the full stack
```bash
cd ~/docker/stacks/monitoring && docker compose up -d
```

### Restart a single service
```bash
cd ~/docker/stacks/monitoring && docker compose up -d <service-name>
```

### Hot-reload Prometheus rules (no restart needed)
```bash
curl -s -X POST http://localhost:9472/-/reload
```

### Hot-reload Alertmanager config (no restart needed)
```bash
curl -s -X POST http://localhost:9784/-/reload
```

### Verify process-exporter is scraping
```bash
curl -s http://localhost:9256/metrics | grep namedprocess | head -5
```

### Test Telegram alert delivery
```python
import urllib.request, json
url = "https://api.telegram.org/bot<TOKEN>/sendMessage"
data = json.dumps({"chat_id": 7564050286, "text": "Test alert", "parse_mode": "HTML"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
urllib.request.urlopen(req)
```

Bot token is in `~/docker/stacks/monitoring/alertmanager/config.yml`.

## Adding New Alert Rules

See [references/alert-rules-guide.md](references/alert-rules-guide.md) for rule file locations, PromQL patterns, severity conventions, and examples.

**Quick path:** Edit the appropriate rule file, then hot-reload Prometheus:
```bash
curl -s -X POST http://localhost:9472/-/reload
```

### Rule file locations
| File | Scope |
|------|-------|
| `prometheus/alert_rules.yml` | Container CPU, memory, availability |
| `prometheus/system_alerts.yml` | Host system + per-process hogs |
| `prometheus/rules/docker-health.yml` | Container health checks, restart loops |

## Alerting

Alerts route to Telegram via **@DeLoNETBot** (chat_id: `7564050286`).

Config: `alertmanager/config.yml`

Severity routing:
- `critical`: repeat every 1h
- `warning`: repeat every 4h

## Key Design Decisions

- **cadvisor is resource-capped**: 1 CPU, 512M memory, 30s housekeeping interval, pruned metrics. Without these limits it will eat an entire core scanning 69+ containers.
- **process-exporter exists specifically to catch host-level hogs** that cadvisor and node-exporter miss (per-process CPU/memory).
- **Duplicate rules were consolidated**: `docker-health.yml` only has health-check and restart-loop rules. CPU/memory rules live in `alert_rules.yml`.

## Diagnosing Performance Issues

When the system stutters, check in this order:

1. `ps aux --sort=-%cpu | head -15` - find CPU hogs
2. `free -h` - check swap pressure
3. `sensors` - check thermals (Tctl)
4. `docker stats --no-stream` - find container hogs

The alert rules should catch most of these automatically now. If they don't fire, check:
- Prometheus is up: `curl http://localhost:9472/-/healthy`
- Alertmanager is up: `curl http://localhost:9784/-/healthy`
- Rules loaded: `curl http://localhost:9472/api/v1/rules | python3 -m json.tool | head -40`
