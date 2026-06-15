#!/usr/bin/env bash
# sweep.sh — one-shot, READ-ONLY evidence gatherer for big-chungus maintenance sweeps.
# Part of the server-maintenance skill. No args. ~2 min budget.
# Writes a markdown report to /tmp/maintenance-sweep-<date>.md and prints its path on stdout.
# Every probe tolerates failure: partial evidence beats no evidence.

set -u

REPORT="/tmp/maintenance-sweep-$(date +%F-%H%M).md"

# Print stdin if non-empty, else the fallback message.
print_or() {
  local out
  out=$(cat)
  if [ -n "$out" ]; then printf '%s\n' "$out"; else printf '%s\n' "$1"; fi
}

fence() { printf '```\n'; }

main() {
  local sudo_ok=0 docker_ok=0
  sudo -n true 2>/dev/null && sudo_ok=1
  docker info >/dev/null 2>&1 && docker_ok=1

  printf '# Maintenance Sweep — %s — %s\n' "$(hostname 2>/dev/null || true)" "$(date '+%F %H:%M %Z' 2>/dev/null || true)"
  printf '\nsudo available: %s | docker available: %s\n' "$sudo_ok" "$docker_ok"
  printf 'REMINDER: journalctl shows LOCAL time; docker timestamps are UTC. UTC now: %s\n' "$(date -u '+%F %H:%M' 2>/dev/null || true)"

  printf '\n## Identity\n\n'
  fence
  { hostname; uptime; uname -r; } 2>/dev/null || true
  fence

  printf '\n## Load / Memory / Swap\n\n'
  fence
  free -h 2>/dev/null || true
  fence

  printf '\n## Top 10 by CPU\n\n'
  fence
  ps aux --sort=-%cpu 2>/dev/null | head -11 || true
  fence

  printf '\n## Top 10 by RSS\n\n'
  fence
  ps aux --sort=-rss 2>/dev/null | head -11 || true
  fence

  printf '\n## Context switches (vmstat 2 3)\n\n'
  local vm cs
  vm=$(vmstat 2 3 2>/dev/null || true)
  fence
  printf '%s\n' "${vm:-vmstat unavailable}"
  fence
  cs=$(printf '%s\n' "$vm" | tail -1 | awk '{print $12}' 2>/dev/null || true)
  printf '\nLast-sample cs: %s/s (baseline ~117k/s; >=300k/s = healthcheck storm or crash loop)\n' "${cs:-?}"

  printf '\n## OOM kills (kernel)\n\n'
  fence
  if [ "$sudo_ok" -eq 1 ]; then
    sudo -n dmesg -T 2>/dev/null | grep -iE 'out of memory|oom-kill|killed process' | tail -20 | print_or "none in dmesg"
  else
    echo "NOTE: sudo unavailable, dmesg skipped; journalctl -k fallback:"
    journalctl -kq --no-pager 2>/dev/null | grep -iE 'out of memory|oom-kill|killed process' | tail -20 | print_or "none visible (may need privileges)"
  fi
  fence

  printf '\n## Failed units (system + user)\n\n'
  fence
  systemctl list-units --state=failed --no-legend --plain 2>/dev/null | print_or "none failed (system)"
  systemctl --user list-units --state=failed --no-legend --plain 2>/dev/null | print_or "none failed (user)"
  fence

  printf '\n## Crash-loop detector (user units, NRestarts > 10)\n\n'
  fence
  # Batched: one systemctl fork per 50 units instead of per unit (~100 forks -> 3).
  # systemctl show with multiple units prints NRestarts/Id blocks separated by blank
  # lines but NO trailing blank, and property order is NOT the -p order (NRestarts
  # comes first) — so each xargs batch appends an 'echo' separator and the awk parser
  # is order-agnostic, flushing a block on each blank line.
  systemctl --user list-units --type=service --state=active --no-legend --plain 2>/dev/null \
    | awk '{print $1}' \
    | xargs -r -n 50 sh -c 'systemctl --user show -p Id -p NRestarts "$@" 2>/dev/null; echo' sh \
    | awk -F= '
        $1=="Id" {id=$2}
        $1=="NRestarts" {n=$2}
        NF==0 { if (id!="" && n+0>10) print "FLAG NRestarts=" n ": " id; id=""; n="" }
        END   { if (id!="" && n+0>10) print "FLAG NRestarts=" n ": " id }
      ' | print_or "no active user unit with NRestarts > 10"
  fence

  printf '\n## Restart-job spam, last 1h (top 5 units)\n\n'
  fence
  {
    journalctl -q --since '-1h' --no-pager 2>/dev/null || true
    journalctl -q --user --since '-1h' --no-pager 2>/dev/null || true
  } | grep 'Scheduled restart job' | grep -oE '[A-Za-z0-9@:._-]+\.service' \
    | sort | uniq -c | sort -rn | head -5 | print_or "no 'Scheduled restart job' lines in last hour"
  fence

  printf '\n## Docker anomalies\n\n'
  if [ "$docker_ok" -ne 1 ]; then
    echo "docker unavailable; section skipped"
  else
    # One inspect pass over all containers:
    # name|status|health|project|workdir|startedAt|finishedAt|restartCount
    # Bare xargs (no -d/-0) is safe here and below: docker ps -q emits one hex
    # container ID per line — no whitespace or quote characters possible.
    local meta now_epoch
    meta=$(docker ps -aq 2>/dev/null | xargs -r docker inspect --format \
      '{{.Name}}|{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.project.working_dir"}}|{{.State.StartedAt}}|{{.State.FinishedAt}}|{{.RestartCount}}' 2>/dev/null || true)
    now_epoch=$(date +%s)

    printf '### Restarting / unhealthy\n\n'
    fence
    printf '%s\n' "$meta" | awk -F'|' '$2=="restarting" || $3=="unhealthy" {print $2" "$3" "$1}' | print_or "none"
    fence

    printf '\n### Exited within the last hour\n\n'
    fence
    local nm st fin ep age
    while IFS='|' read -r nm st _ _ _ _ fin _; do
      [ "$st" = "exited" ] || continue
      ep=$(date -d "$fin" +%s 2>/dev/null) || continue
      age=$((now_epoch - ep))
      if [ "$age" -ge 0 ] && [ "$age" -lt 3600 ]; then
        echo "$nm exited ${age}s ago ($fin UTC)"
      fi
    done <<<"$meta" | print_or "none"
    fence

    printf '\n### Group-restart detector (started <1h, compose siblings >1d)\n\n'
    fence
    local proj started
    declare -A proj_max=()
    while IFS='|' read -r nm st _ proj _ started _ _; do
      [ "$st" = "running" ] && [ -n "$proj" ] || continue
      ep=$(date -d "$started" +%s 2>/dev/null) || continue
      age=$((now_epoch - ep))
      [ "$age" -gt "${proj_max[$proj]:-0}" ] && proj_max[$proj]=$age
    done <<<"$meta"
    while IFS='|' read -r nm st _ proj _ started _ _; do
      [ "$st" = "running" ] && [ -n "$proj" ] || continue
      ep=$(date -d "$started" +%s 2>/dev/null) || continue
      age=$((now_epoch - ep))
      if [ "$age" -lt 3600 ] && [ "${proj_max[$proj]:-0}" -gt 86400 ]; then
        echo "FLAG: $nm (project=$proj) started ${age}s ago; project has siblings >1d old"
      fi
    done <<<"$meta" | print_or "none"
    fence

    printf '\n### RestartCount > 3\n\n'
    fence
    printf '%s\n' "$meta" | awk -F'|' '$8+0 > 3 {print "RestartCount="$8" "$1" ("$2")"}' | print_or "none"
    fence

    printf '\n### Orphaned compose working_dirs (dir gone — container cannot be recreated)\n\n'
    fence
    local wd
    while IFS='|' read -r nm st _ _ wd _ _ _; do
      [ -n "$wd" ] || continue
      [ -d "$wd" ] || echo "ORPHAN: $nm ($st) -> $wd"
    done <<<"$meta" | print_or "none"
    fence

    printf '\n### Running from stale ~/docker/trunk-main\n\n'
    fence
    printf '%s\n' "$meta" | awk -F'|' '$2=="running" && $5 ~ /\/docker\/trunk-main/ {print "STALE-TREE: "$1" -> "$5}' | print_or "none"
    fence

    printf '\n### Healthcheck intervals < 30s (churn sources)\n\n'
    fence
    docker ps -q 2>/dev/null | xargs -r docker inspect --format \
      '{{.Name}}|{{if .Config.Healthcheck}}{{.Config.Healthcheck.Interval}}{{end}}' 2>/dev/null \
      | awk -F'|' '$2 ~ /^[0-9.]+s$/ {v=$2; sub(/s$/,"",v); if (v+0>0 && v+0<30) print "FLAG: "$1" interval="$2}
                   $2 ~ /^[0-9.]+(ms|us|ns)$/ {print "FLAG: "$1" interval="$2}' | print_or "none < 30s"
    fence

    printf '\n### docker system df\n\n'
    fence
    docker system df 2>/dev/null || true
    fence
  fi

  printf '\n## Disk and journal\n\n'
  fence
  df -h / 2>/dev/null || true
  journalctl --disk-usage 2>/dev/null || true
  fence

  printf '\n## Log bloat (>50MB under /tmp and ~/.local/state)\n\n'
  fence
  find /tmp "$HOME/.local/state" -type f -size +50M -exec du -h {} + 2>/dev/null | sort -rh | head -20 | print_or "none > 50MB"
  fence

  printf '\n## bgls problem metrics\n\n'
  fence
  bgls --prom 2>/dev/null | grep '^bgls_unit_problem' | print_or "no bgls_unit_problem lines (bgls missing or zero problems)"
  fence

  printf '\n## Root crontab (must be empty — cleared 2026-06-10)\n\n'
  fence
  if [ "$sudo_ok" -eq 1 ]; then
    local rc
    rc=$(sudo -n crontab -l 2>/dev/null || true)
    if [ -n "$rc" ]; then
      echo "WARNING: root crontab is NOT empty — any entry here is suspect:"
      printf '%s\n' "$rc"
    else
      echo "root crontab empty (expected)"
    fi
  else
    echo "NOTE: sudo unavailable; root crontab not checked"
  fi
  fence

  printf '\n## Prometheus trend (bgls_loadavg, sum of bgls_unit_problem)\n\n'
  fence
  local prom
  prom=$(curl -sG --max-time 5 'http://localhost:9472/api/v1/query' --data-urlencode 'query=bgls_loadavg' 2>/dev/null || true)
  printf '%s\n' "${prom:-prometheus :9472 unreachable}" | head -c 2000
  printf '\n'
  prom=$(curl -sG --max-time 5 'http://localhost:9472/api/v1/query' --data-urlencode 'query=sum(bgls_unit_problem)' 2>/dev/null || true)
  printf '%s\n' "${prom:-prometheus :9472 unreachable}" | head -c 2000
  printf '\n'
  fence

  printf '\n## End of sweep — %s\n' "$(date '+%F %H:%M:%S %Z' 2>/dev/null || true)"
}

main >"$REPORT" 2>&1
printf '%s\n' "$REPORT"
