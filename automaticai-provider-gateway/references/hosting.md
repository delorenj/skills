# Hosting: where the gateway runs and how to keep it up

`api.automaticai.io` runs on the AWS Lightsail VM `aai-gateway` since
2026-10-13 02:21 ET. The authoritative runbook is
`~/code/client-portal/gateway/ops/CLOUD.md`; read it before changing anything
below, and trust it over this summary when they differ.

## Facts that change how you work

- **`gateway/TARGET` names the serving host** (`cloud` now, `home` before the
  cutover). `ops/compose.sh` follows it, and so does every script that execs
  into Postgres (they resolve the daemon through `ops/gateway_target.py`). After
  the cutover `compose.sh` refuses `home` without `AAI_ALLOW_HOME=1`, because a
  second live gateway would split the ledger.
- **Deploy only with `./ops/compose.sh`** (or `pnpm gateway:compose`). It
  resolves secrets on big-chungus with `op run` (the VM holds no 1Password
  credential), ships the locally built image over the tailnet (there is no
  registry), and serializes container changes on
  `$XDG_RUNTIME_DIR/automaticai-gateway/deploy.lock`. A bare `docker compose`
  fails by design.
- **Never `docker context use aai-cloud`.** Other sessions' plain `docker`
  commands must keep meaning big-chungus. Read the VM with
  `docker --context aai-cloud ...` or `ssh aai-gateway`.
- **Same container names as before**: `new-api`, `newapi-postgres`,
  `newapi-redis`, plus `newapi-caddy` and `newapi-cloudflared`. The home
  containers still exist, stopped with `restart=no`; do not start them.
- **Ingress**: Cloudflare tunnel `aai-gateway` → `cloudflared` → Caddy →
  `new-api`. No public inbound port is open; the VM is reachable over the tailnet
  (`100.65.37.119`). Caddy answers a JSON 503 with `Retry-After` while `new-api`
  is down, so a redeploy shows clients a short retryable 503.
- **Postgres health requires data.** New-api starts only once `users` has a
  row, because NewAPI leaves `/api/setup` open on an empty database.
- **Still at home**: the OAuth renewer (`oauth-connections.py`), 1Password
  Connect, Prometheus (`100.66.29.76:9472`, polled by the router's allowance
  oracle over the tailnet), the exporter, the free scout, ntfy and
  infra-doctor. If big-chungus is down for more than about two hours, the
  Claude subscription channels' access tokens expire.

## Commands

`tokies` is the front door (installed from `gateway/tokies`; it follows
`gateway/TARGET` like the scripts it wraps):

| Need | Command |
|---|---|
| Health, image, tunnel, backups and cost in one view | `tokies status` (`--json` for scripts; exit 1 on any problem, and each problem names the next command) |
| Logs | `tokies logs [new-api\|postgres\|redis\|caddy\|cloudflared] [-n N] [--since 10m] [-f]` |
| Start whatever is down, without deploying a changed pin | `tokies up` |
| Deploy a build | `tokies deploy <tag> [--build] --yes` (pins, recreates, verifies, puts the old pin back on failure or Ctrl-C, commits only `gateway/compose.yml`) |
| Restore the nightly copy onto the VM | `tokies restore [dump] --yes` |

Without `--yes`, `deploy` and `restore` print their plan and change nothing; run
that first. The underlying scripts, from `~/code/client-portal/gateway`:

| Need | Command |
|---|---|
| Health in one shot | `./ops/cloud/vm-health.py` (public endpoint via Caddy, containers, memory, swap, disk, container limits, transfer, pending reboot; exit 1 on problems) |
| Deploy a new build | `IMAGE_TAG=<tag> ./brand/build.sh v1.0.0-rc.40`, pin `<tag>` in `compose.yml`, `./ops/compose.sh up -d --no-deps --force-recreate new-api` |
| Roll back a build | pin the previous tag, same command (the old image stays on the VM) |
| Start whatever is down | `./ops/compose.sh up -d` |
| Logs | `docker --context aai-cloud logs --tail 200 new-api` |
| Tunnel | `./ops/cloud/cf.py tunnel status --tunnel cloud`; restart with `docker --context aai-cloud restart newapi-cloudflared` |
| Reboot the VM | `ssh aai-gateway sudo reboot` (about 35 s of Cloudflare `530`), or `aws lightsail reboot-instance --instance-name aai-gateway --profile automaticai-legacy --region us-east-1` after `aws sso login --profile automaticai-legacy` |
| Database shell | `docker --context aai-cloud exec -it -u postgres newapi-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'` |
| Restore the nightly copy | `./ops/compose.sh stop new-api && ./ops/cloud/backup-pull.sh restore && ./ops/compose.sh up -d` |
| Cost month to date | `aws ce get-cost-and-usage` filtered to Amazon Lightsail (the exact command is in CLOUD.md) |

Read the response before acting on a symptom: `200` with `via: 1.1 Caddy`
means the VM served it; Caddy's `503` means `new-api` is down; Cloudflare's
`530`/1033 means no tunnel connector (the VM or `cloudflared`).

## Monitoring and alerts

- `newapi-vm-health.timer` (every 5 min) pushes problems to ntfy once, again
  every 6 h while they last, and their recovery once.
- infra-doctor probes the public endpoint every minute and watches two
  dead-man markers: the health checker and the nightly database pull.
- Lightsail alarms email `jaradd@gmail.com` on a failed status check or low
  CPU burst credits. These are the only alerts that still arrive while
  big-chungus is down.
- AWS Budgets: "aai-gateway Lightsail" ($30) and the account's "Keep it Cheap"
  ($50) email on overruns. The VM costs a flat $24/month. The only variable
  cost is transfer beyond 4 TB (about 0.8 TB is expected), which
  `vm-health.py` reports from `vnstat`.

## Backups

`newapi-db-pull.timer` (08:05) dumps the VM's database and roles into
`~/backups/postgres/dbs/containers/newapi-postgres.*` and restore-tests every
copy in a throwaway Postgres. Lightsail keeps daily snapshots as a second
layer. A snapshot restored beside the live VM would start a second
`cloudflared` with the same token and split traffic, so stop it in any restored
copy first.

## Lessons from the first night

- Library updates must not restart the network stack under live connections.
  When `systemd-networkd` stopped, it dropped the DHCP address, which flushed
  Docker's NAT state and black-holed the gateway's pooled HTTP/2 connection to
  Anthropic. needrestart now leaves networking services alone, and networkd
  keeps its address on restart (applied live and in `cloud-init.sh`).
- Since `v1.0.0-rc.40-upstream-health-r1`, a silently dead upstream connection
  closes within about a minute (HTTP/2 pings, write timeouts, keepalive,
  `TCP_USER_TIMEOUT`). `AAI_UPSTREAM_PING_SECONDS` and
  `AAI_UPSTREAM_TCP_TIMEOUT_SECONDS` tune these, and `0` disables either.
  Cloudflare cuts a client at 100 s without a byte, so anything slower shows up
  as a 524.

## Cutover tooling

`./ops/cloud/cutover.py check|run|rollback` moved production with automatic
rollback. Its `rollback` only makes sense while the home database is still
current: after the VM has written days of ledger rows, failing back means
dumping the VM and restoring at home, never just starting the old containers.
Start only home Postgres and Redis (`docker start newapi-postgres
newapi-redis`), run `AAI_SOURCE_CONTEXT=aai-cloud AAI_GATEWAY_CONTEXT=default
ops/cloud/migrate-db.sh dump`, then `restore` with the printed directory under
the same variables, and move DNS and `TARGET` back with home `new-api` started
last.
