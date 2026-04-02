---
pipeline-status:
  - new
---
# Monitoring Stack Architecture

## Stack Root

`~/docker/stacks/monitoring/`

## Services

| Service | Image | Internal Port | External Port | URL |
|---------|-------|---------------|---------------|-----|
| Prometheus | prom/prometheus | 9090 | 9472 | - |
| Grafana | grafana/grafana | 3000 | 9831 | https://grafana.delo.sh |
| Alertmanager | prom/alertmanager | 9093 | 9784 | https://alerts.delo.sh |
| cadvisor | gcr.io/cadvisor/cadvisor | 8080 | 9264 | https://cadvisor.delo.sh |
| node-exporter | prom/node-exporter | 9100 | 9519 | - |
| process-exporter | ncabatoff/process-exporter | 9256 | 9256 | - |
| Loki | grafana/loki | 3100 | - | - |
| OTEL collector | otel/opentelemetry-collector-contrib | 4317/4318 | 4317/4318 | - |
| Dockge | louislam/dockge | 5001 | 14654 | https://dockge.delo.sh |
| Uptime Kuma | louislam/uptime-kuma | 3001 | 13556 | https://uptime.delo.sh |
| health-monitor | alpine (custom script) | - | - | - |

## Data Flow

```
Host processes
  └─> process-exporter ──> Prometheus
Host metrics
  └─> node-exporter ────> Prometheus
Docker containers
  └─> cadvisor ──────────> Prometheus
App telemetry
  └─> OTEL collector ───> Prometheus (metrics)
                      └─> Loki (logs)

Prometheus ──> alert_rules.yml ──────> Alertmanager ──> Telegram (@DeLoNETBot)
           └─> system_alerts.yml ──┘         chat_id: 7564050286
           └─> rules/docker-health.yml ┘

Prometheus + Loki ──> Grafana (dashboards)
```

## Directory Layout

```
monitoring/
├── compose.yml
├── alertmanager/
│   └── config.yml              # Telegram bot config
├── prometheus/
│   ├── prometheus.yml          # Scrape configs
│   ├── alert_rules.yml         # Container alerts
│   ├── system_alerts.yml       # Host + process alerts
│   └── rules/
│       └── docker-health.yml   # Health check + restart alerts
├── process-exporter/
│   └── config.yml              # Process grouping config
├── grafana/
│   └── provisioning/
│       ├── dashboards/
│       └── datasources/
├── loki/
│   └── config.yml
└── otel/
    └── collector-config.yml
```

## Credentials

- Grafana: `$DEFAULT_USERNAME` / `$DEFAULT_PASSWORD` (from env)
- Telegram bot token: in `alertmanager/config.yml`

## Resource Limits

cadvisor is explicitly capped:
- CPU: 1 core
- Memory: 512MB
- Housekeeping interval: 30s (default was 1s)
- Docker-only mode (skips raw cgroups)
- Disabled expensive metrics: percpu, disk, diskIO, memory_numa, etc.

Without these limits, cadvisor will consume an entire CPU core scanning 69+ containers.
