# big-chungus System Map

**Last verified: 2026-07-04** (CPU-runaway + crash-loop sweep). This file is the baseline for Phase 1 triage. If a sweep contradicts it, the sweep wins — fix the system or fix this map (Phase 6), never leave them divergent.

## Host

- Hostname: **big-chungus**. LAN `192.168.1.12`, Tailscale `100.66.29.76`.
- 123 GiB RAM, 8 GiB swap, RTX 3090, NVMe `/` = 3.6T.
- Primary user: `delorenj`. The user systemd manager shows as `systemd[<PID>]` in the journal (useful when grepping for who issued stop/restart jobs). That PID is **session-specific** — it was 18542 on 2026-06-10 but changes on relogin/reboot; resolve the current one with `pgrep -u "$(id -u)" -x systemd`.

## Background-task surfaces (where things can run from)

Check ALL of these when hunting an actor; `bgls` covers them in one shot.

1. **User crontab** (`crontab -l`).
2. **Root crontab** (`sudo crontab -l`) — **cleared 2026-06-10. ANY entry reappearing here is suspect.**
3. `/etc/crontab` + `/etc/cron.d/`.
4. **System systemd**: ~65 services, 19 timers.
5. **User systemd** at `~/.config/systemd/user`: ~130 units, including the **hermes fleet**: `hermes-<repo>-<role>-{gateway,consumer,checkpoint}` units. These pin **absolute repo paths** and break when repos move; the registry at `~/.hermes/agents-registry.yaml` must stay in sync with the unit files.
6. **Docker**: ~46 compose projects, ~120 running containers.
7. **pm2**: n8n only.

## THE TOOL: bgls

`bgls` (on PATH) — unified background-task inventory across all surfaces above.

- Output modes: table (default) / `--json` / `--prom` / `--md` / `--fzf`.
- Actions: `bgls inspect|stop|restart|start|disable TYPE NAME`.
- Types: `cron`, `sys-svc`, `sys-timer`, `usr-svc`, `usr-timer`, `docker`, `pm2`.

## Metrics pipeline

- `bgls-metrics.timer` (user, every 5 min) → writes `~/.local/state/node-exporter-textfile/bgls.prom` → **node-exporter** (host `:9519`, textfile collector) → **Prometheus** (host `:9472`).
- Prometheus queries: `bgls_items`, `bgls_unit_problem`, `bgls_loadavg`.
- Nightly markdown snapshots: `bgls-snapshot.timer` → `~/code/infra/docs/inventory/` (git-committed) — diff these for "when did X appear".
- **Holocene dashboard** (holocene.delo.sh, behind SSO) has a Systems tab over this data; its API is the user unit `holocene-api.service` on `:4000`.

## Docker layout

- **Live trees**: `~/docker/stacks/{monitoring,utils,websites,media,ai}` and `~/docker/core/`.
- **`~/docker/trunk-main/` is a STALE pre-reorg tree** — anything still running from there is a decommission candidate.
- Project stacks also live in `~/code/<project>`.
- **Orphans** (compose `working_dir` label points at a deleted dir — container cannot be recreated). As of 2026-06-10: `twenty`, `candystore`, `chrome-debug`, `maybe-finance`.
- **Triage doc**: `~/code/infra/docs/docker-stack-triage.md` — user marks rows keep/stop/decommission; the agent executes only marked rows.

### Monitoring stack

`~/docker/stacks/monitoring/compose.yml`: prometheus, grafana, loki, node-exporter, process-exporter, cadvisor, uptime-kuma, dockge, **docker-health-monitor**. The last one runs as a **live container** (`docker-health-monitor`) executing `~/docker/scripts/docker-health-monitor.sh`; it auto-restarts exited containers — and at script line ~399 will **recreate** one via `docker compose -p <proj> up -d <svc>`, which **resets its RestartCount**. This makes it a **second reviver**: a plain `docker stop` on a flapping container is undone within one monitor interval (the tell is RestartCount dropping to a low number). To kill a loop for good, `docker rm -f` the whole stack so nothing is left in `exited` state. (No `.log` file on disk as of 2026-07-04 — read its output via `docker logs docker-health-monitor` for "who restarted X".)

## Attic convention (retired automation)

Retired automation moves to `~/code/infra/attic/` or `~/.config/zshyzsh/attic/`, with crontab backups alongside. Never delete; never silently re-enable.

**PERMANENTLY RETIRED — never resurrect:**

- `memory_guardian.sh` — existed in BOTH user and root crontabs; SIGKILLed a whisper container ~5,500 times.
- `system-monitor.sh` — cron + a daemon variant that `pkill`'d chrome-devtools MCP servers at load>8.
- `zombie-cleanup.sh`
- `load-alert.sh`

## Tuning applied 2026-06-10

- `/etc/sysctl.d/99-delonet.conf`: `vm.swappiness=10`.
- `/etc/systemd/journald.conf.d/99-delonet.conf`: `SystemMaxUse=2G`.

If these files are missing or values differ, that is an anomaly.

## Known-disabled units awaiting human action (NOT anomalies unless state changed)

- **openclaw-gateway**: Telegram token 401 → openclaw bug crashes the gateway → 150%-CPU restart loop. Needs a new token from 1Password DeLoSecrets before re-enabling.
- **hermes-delodocs-pm-checkpoint** + delodocs wiki curator timers: the delodocs PM was never fully provisioned — fix via pjangler re-provision, not by poking the units.
- **intelliforia-demo-snapshot**: its mise task is gone.
- **whisper-server stack**: stopped (idle since Feb). Compose kept at `~/docker/core/whisper-server`, models at `~/whisper-models`.
- **keepy-money PM (hermes)**: consumer + checkpoint.timer **disabled 2026-07-04**. Provisioning left `.tirith-install-failed` (`download_failed`) in `~/code/tiller/agents/hermes/pm/runtime/` — `bloodbank-consumer.py`/`.env` were never downloaded, so the enabled `-consumer` unit crash-looped 14k× (`status=2`). `hermes-keepy-money-pm-gateway.service` left **running** (not churning). Re-provision via pjangler/tirith, then re-enable — don't just re-enable the units.
- **vexa transcription-service stack**: **removed 2026-07-04** (`docker rm -f transcription-lb/-worker-1/-worker-2`). Workers were `Exited(255)` for 2 days; the nginx LB flap-looped 3047× on unresolvable upstream. Compose at `~/code/vexa/services/transcription-service/docker-compose.yml`; `docker compose up -d` to revive when vexa is worked on again.

## Known recurring issues (band-aided, need real fixes)

- **scout-api CPU runaway**: `ghcr.io/delorenj/scout` (uvicorn `app.main:app` :8000, `~/docker/stacks/ai/scout`) wedges at 100% CPU (full core) after ~1-2 days uptime. Restarted 2026-07-01 AND 2026-07-04 for this. `docker restart scout-api` clears it (→0.1%) but it recurs — a hot-loop/busy-wait bug in scout needs a code fix. **First suspect for "one core pinned."**

## Healthy baselines (2026-06-10)

| Metric | Healthy | Anomaly signal |
|---|---|---|
| Load 1m | ~4-7 with dev sessions running | sustained above that without sessions |
| Swap used | <500 MB | growth without memory pressure (see playbook: stale swap) |
| Context switches | ~117k/s | ≥300k/s = healthcheck storm or crash loop |
| Failed user units | 0 | any |
| Root crontab | empty | ANY entry |
| journald disk | ≤2G | growth past cap |

## Secrets

Resolution order: project `.env` → `~/.config/zshyzsh/secrets.zsh` (exported in interactive shells; **systemd stack units do NOT see it**) → 1Password DeLoSecrets vault. Plane API keys: `$PLANE_33GOD_API_KEY` etc. A unit failing on a missing env var that "works in my shell" is almost always this gap.

## Hindsight

Banks: `infra` (this box), `33GOD`, `general`. API at `api.hs.delo.sh`. **Always `recall` before a sweep and `retain` after.**
