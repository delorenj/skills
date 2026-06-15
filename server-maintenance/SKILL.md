---
name: server-maintenance
description: Diagnose and clean up the big-chungus home server. Finds what is killing processes or containers, attributes crash loops, kill loops, healthcheck storms, OOM, swap pressure, and docker bloat, then fixes and prunes safely. Use when the user says "what is killing my server", "server is slow", "server locked up", "server is dying", "high load", "what's eating CPU", "what's eating memory", "spring cleaning", "maintenance sweep", "cleanup the server", "docker cleanup", "too many containers", "disk full", "prune docker", or asks why a unit/container keeps restarting, who restarted X, or why load spiked. Built around scripts/sweep.sh (one-shot evidence report), references/server-map.md (system baselines), and references/forensics-playbook.md (attribution patterns); uses bgls, systemd, journalctl, docker, Prometheus, hindsight. Do NOT use for debugging one project's application code, provisioning new services or stacks (use delonet-conventions), or Cloudflare/network routing issues.
---

# Server Maintenance

Phased maintenance sweep for big-chungus. The expensive research (file locations, attribution patterns, baselines) is pre-paid in `references/` and `scripts/sweep.sh` — spend agent judgment only on Phase 2 forensics, never on re-discovering the system.

## Operating Principles

- **Never start with ad-hoc `ps`/`journalctl` spelunking.** `scripts/sweep.sh` gathers all of it in one ~2min pass into one report file. Run it first, read the report, work from there.
- **The map is the baseline.** An observation is only an anomaly relative to `references/server-map.md`. Compare before investigating.
- **One fix at a time, verified.** Parallel fixes destroy attribution.
- **Read-only until Phase 3.** Phases 0-2 must not change system state.
- **Always ask both questions of a loop: what kills it AND what revives it.** Kill loops on this box have historically been self-inflicted pairs (guardian script + restart policy).
- **The skill is self-maintaining.** If a sweep reveals the map is stale, updating it is part of the job (Phase 6). Stale maps are worse than no maps.

## Phase Routing

| Phase | Goal | Inputs | Load |
|---|---|---|---|
| 0 Gather | Evidence, cheap + deterministic | `hindsight recall`, `scripts/sweep.sh` | report file only |
| 1 Triage | Anomaly list | report vs baselines | [references/server-map.md](./references/server-map.md) |
| 2 Forensics | Root cause per anomaly | journal, docker inspect, crontabs | [references/forensics-playbook.md](./references/forensics-playbook.md) |
| 3 Fix | Apply + verify, one at a time | per-anomaly | playbook + map |
| 4 Prune | Reclaim space (only if asked) | triage doc | map (Docker layout) |
| 5 Verify | Prove the box is healthier | re-run sweep, diff | Phase 0 report |
| 6 Retain | Persist learnings, refresh map | findings | map + hindsight |

## Phase 0: Gather (deterministic — no judgment yet)

1. `hindsight memory recall infra "<the symptom, or 'maintenance sweep'>"` — prior incidents often name the culprit outright.
2. Run `bash "$SKILL_DIR/scripts/sweep.sh"`, where `SKILL_DIR` is the base directory stated when this skill was loaded (fallback path on this host: `~/.agents/skills/server-maintenance/scripts/sweep.sh`). It prints the path of a markdown report in /tmp. Read that one file. It covers identity, load/mem/swap, top consumers, ctx switches, OOM, failed units, crash-loop flags, docker anomalies (restart storms, orphans, trunk-main leftovers, fast healthchecks), disk/journal/log bloat, bgls problem metrics, root crontab, and Prometheus trend. Do not duplicate any of these with ad-hoc commands.

## Phase 1: Triage

Load `references/server-map.md`. Compare the sweep report against its **Healthy baselines** and known-state sections (known-disabled units, retired automation, orphan list). Output: a short anomaly list — only deltas from baseline, each with the report line that evidences it. Known/expected items (e.g. openclaw-gateway disabled) are NOT anomalies; flag them only if their state changed.

## Phase 2: Forensics (dynamic — agent judgment lives here)

Per anomaly, load `references/forensics-playbook.md` and apply its attribution patterns: time-zone normalization, scope-teardown journal greps, PID-to-container mapping, RestartCount semantics, watchdog/kill-loop pair detection, OOM-vs-stale-swap, healthcheck storms. Follow the playbook's suspect-elimination order rather than improvising. New strange behavior with no matching pattern: investigate freely, then write the new pattern into the playbook in Phase 6.

## Phase 3: Fix

One fix at a time. Verify each before touching the next:

- A restarted/patched unit: stays `active` 5-10 min with `NRestarts` not incrementing.
- A kill loop: the kill counter / log line stops appearing (watch for 2+ former kill intervals).
- A recreated container: healthy AND still attached to its networks (`docker inspect <c> --format '{{json .NetworkSettings.Networks}}'` — recreation has dropped networks before).

Retired automation goes to the attic dirs (see map), never deleted. Never resurrect anything on the PERMANENTLY RETIRED list in [references/server-map.md](./references/server-map.md), "Attic convention" section.

## Phase 4: Prune (only if explicitly asked, or part of a spring-cleaning request)

SAFE set, no permission needed: `docker builder prune -f` and dangling-image prune (`docker image prune -f`).

Everything else — volumes, stopped stacks, images in use, decommissioning trunk-main leftovers — requires: (1) update `~/code/infra/docs/docker-stack-triage.md` with the candidates, (2) an explicit user decision per row; execute only rows the user marked. **Never `docker volume prune` blind** — orphan-looking volumes on this box have held real data.

## Phase 5: Verify

Re-run `scripts/sweep.sh`; diff the new report against the Phase 0 report (anomaly sections shrink, baselines hold). Then check the trend, not just the moment: Holocene dashboard Systems tab (holocene.delo.sh) or Prometheus directly (`bgls_unit_problem`, `bgls_loadavg`, ctx-switch rate) — confirm problem metrics are flat or declining.

## Phase 6: Retain (mandatory — this is what keeps the skill cheap)

1. `hindsight memory retain infra "<what broke, why, how fixed, what did NOT work>" --context debugging` — one retain per distinct finding.
2. **Update `references/server-map.md`** if any baseline or fact changed: baselines, units/stacks added or removed, orphan list, attic entries, tuning. Bump its "Last verified" date.
3. **Update `references/forensics-playbook.md`** with any new attribution pattern discovered.
4. Update `~/code/infra/docs/docker-stack-triage.md` if container dispositions changed.

## Gotchas

- sweep.sh uses `sudo -n` for root-only probes (dmesg, root crontab) and notes when it skipped them — check those notes before concluding "no OOM" or "root crontab empty".
- journalctl prints LOCAL time; docker timestamps are UTC. The playbook covers this; it has burned a full investigation before.
- `systemctl status` saying `active (running)` proves nothing about loops — check `NRestarts`.

## Out of Scope

- **Application debugging** of one project's code or tests — use that project's tooling/skills.
- **Provisioning** new stacks, services, hermes agents, or DNS/tunnel routes — use `delonet-conventions` / `33god-projects`.
- **Hardware/BIOS/GPU driver work** — manual.
- **Other hosts** — the map and baselines are big-chungus-specific; for another machine, gather facts fresh and fork the map.
