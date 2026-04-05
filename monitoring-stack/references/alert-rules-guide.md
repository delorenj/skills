---
pipeline-status:
  - new
---
# Alert Rules Guide

## Rule File Locations

| File | Purpose | Reload after edit |
|------|---------|-------------------|
| `prometheus/alert_rules.yml` | Container CPU, memory, availability | `curl -X POST http://localhost:9472/-/reload` |
| `prometheus/system_alerts.yml` | Host system, swap, per-process hogs | same |
| `prometheus/rules/docker-health.yml` | Container health checks, restart loops | same |
| `alertmanager/config.yml` | Alert routing, Telegram config | `curl -X POST http://localhost:9784/-/reload` |

## Current Alert Inventory

### Container alerts (alert_rules.yml)
- **ContainerHighMemoryUsage**: >80% of memory limit for 5m
- **ContainerMemoryAbsolute**: >4GB RSS for 15m (catches limitless containers)
- **ContainerCPUSustained**: >0.5 cores for 15m
- **ContainerHighCPU**: >1.0 cores for 5m (critical)
- **MetaMCPHighProcessCount**: >15 processes in MetaMCP container
- **ContainerDown**: any scrape target down for 1m

### System alerts (system_alerts.yml)
- **SystemLoadCritical**: load1 > 100
- **SystemLoadHigh**: load1 > 32 (core count) for 5m
- **MemoryUsageHigh**: >90% for 5m
- **SwapUsageHigh**: >50% for 10m
- **SwapUsageCritical**: >80% for 5m
- **SwapThrashing**: swap I/O >100 pages/sec for 5m
- **DiskIOSaturated**: disk util >90% for 10m
- **ProcessHighCPU**: any process >0.8 cores for 10m
- **ProcessCPUSustained**: any process >0.5 cores for 30m (critical)
- **ProcessHighMemory**: any process >8GB RSS for 10m
- **ProcessMemoryCritical**: any process >16GB RSS for 5m

### Docker health (rules/docker-health.yml)
- **ContainerUnhealthy**: health check failing for 2m
- **ContainerRestartingTooOften**: >0.25 restarts/min over 15m

## Severity Conventions

- `warning`: Something is off, investigate when convenient. Telegram repeat: every 4h.
- `critical`: Actively degrading the system. Telegram repeat: every 1h.

## Writing a New Alert Rule

### Template
```yaml
  - alert: MyAlertName
    expr: <PromQL expression>
    for: <duration before firing, e.g., 5m>
    labels:
      severity: warning|critical
    annotations:
      summary: "Short description with {{ $labels.name }} and {{ $value }}"
      description: "Longer explanation of impact and what to check"
```

### Available metric sources

**From node-exporter** (host-level):
- `node_cpu_seconds_total`, `node_memory_*`, `node_disk_*`, `node_filesystem_*`
- `node_load1`, `node_load5`, `node_load15`
- `node_vmstat_pswpin`, `node_vmstat_pswpout` (swap I/O)

**From cadvisor** (container-level):
- `container_cpu_usage_seconds_total{name!=""}` - always filter `name!=""` to exclude root cgroup
- `container_memory_usage_bytes{name!=""}`
- `container_spec_memory_limit_bytes{name!=""}`
- `container_restart_count`

**From process-exporter** (per-process):
- `namedprocess_namegroup_cpu_seconds_total{mode="user"}` - use `rate()` for CPU cores
- `namedprocess_namegroup_memory_bytes{memtype="resident"}` - RSS
- `namedprocess_namegroup_num_procs` - process count per group
- `namedprocess_namegroup_context_switches_total`

### Common PromQL patterns

```promql
# Container CPU usage in cores (5m average)
rate(container_cpu_usage_seconds_total{name!=""}[5m])

# Per-process CPU in cores
rate(namedprocess_namegroup_cpu_seconds_total{mode="user"}[5m])

# Swap usage percentage
1 - (node_memory_SwapFree_bytes / node_memory_SwapTotal_bytes)

# Swap thrashing rate (pages/sec)
rate(node_vmstat_pswpin[5m]) + rate(node_vmstat_pswpout[5m])

# Memory usage percentage
1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Disk utilization
rate(node_disk_io_time_seconds_total{device!~"loop.*"}[5m])
```

## Testing Rules

Verify rules loaded after reload:
```bash
curl -s http://localhost:9472/api/v1/rules | python3 -c "
import sys, json
data = json.load(sys.stdin)
for g in data['data']['groups']:
    print(f'Group: {g[\"name\"]}')
    for r in g['rules']:
        state = r.get('state', 'n/a')
        print(f'  {r[\"name\"]}: {state}')
"
```

Check currently firing alerts:
```bash
curl -s http://localhost:9472/api/v1/alerts | python3 -c "
import sys, json
data = json.load(sys.stdin)
for a in data['data']['alerts']:
    print(f'{a[\"labels\"][\"alertname\"]}: {a[\"state\"]}')
" 2>/dev/null || echo "No alerts firing"
```
