# Forensics Playbook — attribution patterns for big-chungus

Patterns that were expensive to discover during the 2026-06-10 de-rookification. Apply these before improvising. When a new pattern is discovered, append it here (Phase 6).

## Suspect-elimination order (start here)

This order worked; it goes cheapest/most-common first:

1. **OOM?** `dmesg -T | grep -i oom` and `journalctl -k`.
2. **Restart loops?** systemd (`NRestarts`) and docker (`RestartCount`) — patterns below.
3. **Who sent signals?** Journal scope teardowns + cron timing windows (look ±2 min around each kill for cron schedules).
4. **Kill-capable crons/scripts?** `grep -rE 'kill|pkill|docker (stop|restart)' ~/.config/zshyzsh ~/code/infra/scripts ~/docker/scripts` plus BOTH crontabs (user and root).
5. **External actors?** compose invocations, docker-health-monitor logs, the user himself.

## Time-zone trap (read first, it poisons everything downstream)

- `journalctl` prints **LOCAL** time (EDT).
- `docker inspect` / `docker logs` timestamps are **UTC**.
- Convert to one zone before correlating events, or every "X happened right before Y" inference is off by 4-5 hours.

## Docker event attribution

- **`docker events` is USELESS for retro forensics here**: healthcheck exec events flood the ring buffer (~30s of history survives). Do not waste time on it.
- Instead, get container teardown times from the journal:
  ```bash
  journalctl | grep 'docker-<id>.scope: Deactivated'
  ```
  then map IDs to names: `docker inspect <id> --format '{{.Name}}'`.
- **PID → container**:
  ```bash
  grep -o 'docker[-/][0-9a-f]\{64\}' /proc/<PID>/cgroup
  ```
  then `docker inspect` the hash.

## "Who restarted this container?"

`RestartCount` semantics are the key:

- `RestartCount` increments **ONLY** on restart-policy restarts (i.e. the process died and the policy revived it).
- `docker restart` and compose recreate do **NOT** increment it.

Therefore:

- An `unless-stopped` container that "came back" after being stopped → its process **died** and the policy revived it. Ask what killed it.
- A `restart: no` container that restarted → an **external actor**: compose up, **docker-health-monitor** (check `~/docker/scripts/docker-health-monitor.sh`'s log — it auto-restarts exited containers), or a human.

## Simultaneous clean exits across unrelated projects

Multiple containers in unrelated compose projects exiting with **code 0 at the same moment** = a host-side signal sweep, not a docker problem. Known cause on this box: **the user runs `pkill -f uvicorn` when the box locks up.** Check `ps` lineage and shell histories before blaming docker.

## systemd loop patterns

- **"active" can mask a crash loop** when `Restart=always`. Check:
  ```bash
  systemctl show -p NRestarts,ActiveEnterTimestamp <unit>
  ```
  Young `ActiveEnterTimestamp` + high `NRestarts` = loop. Also journal spam: `Scheduled restart job, restart counter is at N`.
- **`WatchdogSec=` on a unit whose binary never calls `sd_notify`** (and isn't `Type=notify`) = guaranteed watchdog-timeout **SIGABRT kill loop**. The syncthing unit did exactly this.

## The kill-loop *pair* pattern

A watchdog/guardian script kills the process → a restart policy revives it → forever. Symptom: **perfectly periodic kills** in an actions.log or the journal (memory_guardian SIGKILLed a whisper container ~5,500 times this way). Always answer BOTH questions: **what kills it** AND **what revives it**. Fixing only one side leaves a half-loop that re-arms later.

## OOM vs stale swap

- Check: `dmesg -T | grep -i oom` and `journalctl -k`.
- **No OOM kills + plenty of free RAM + high swap usage = stale swap pages, NOT memory pressure.** Fix: `swapoff -a && swapon -a` and `vm.swappiness=10` (already applied — see server-map Tuning). Do not chase a memory leak that isn't there.

## Healthcheck storm

Symptom: ctx switches ≥300k/s, constant exec churn. Find offenders:

```bash
docker ps -q | xargs docker inspect --format '{{.Name}} {{if .Config.Healthcheck}}{{.Config.Healthcheck.Interval}}{{end}}'
```

Anything **<30s** is a churn source. Fix: patch the interval in the compose file, then `docker compose up -d <svc>`. **Verify the recreated container kept its networks** (`docker inspect <c> --format '{{json .NetworkSettings.Networks}}'`) — one recreation came back with NO networks attached; `docker compose up -d --force-recreate <svc>` fixes that.

## GPU VRAM exhaustion → GNOME black-screen "freeze" (NOT a gdm bug)

Symptom: desktop frozen / GDM stuck at a black screen, often with a stale failed-unit line on the VT (e.g. "failed to start docker-stack-33god") that is a **red herring**. SSH still works.

Attribution order:
1. **Rule out the obvious decoys FIRST** so you don't chase them: disk (`df -h /` + `df -i /`), docker daemon (`systemctl is-active docker`), and any console unit name mentioned — on this box those are almost always coincidental, not causal. A `docker-stack-*` unit showing `inactive/disabled` while its containers are `Up` and `healthy` is fine; ignore the console message.
2. **Driver mismatch?** `nvidia-smi` + compare `cat /sys/module/nvidia/version` vs the userspace lib vs `dpkg -l | grep nvidia-driver`. All equal + `nvidia-smi` works = driver is fine, NOT the cause (don't reboot for this).
3. **The real tell — VRAM full:** `dmesg -T | grep -iE 'nvkms|nv_drm_gem'` showing `*ERROR* Failed to allocate NVKMS memory for GEM object` = the GPU is out of VRAM and the **GNOME Wayland compositor can't allocate its ~580 MiB framebuffer**, so the greeter renders black. Confirm: `nvidia-smi --query-gpu=memory.used,memory.free --format=csv` (near 24576/0) and `nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv` for the hogs.
4. **Known hogs on big-chungus:** voxxy `voxcpm` engines (~5.4 GB *each* — it has run TWO at once ≈ 11 GB), `ollama` (~6 GB), per-service `python3`/`uvicorn engine.main` workers (~1.4 GB). `gnome-shell` itself shows ~580 MiB under `G` type once it's healthy — its absence from the `nvidia-smi` process table = the compositor never started = still starved.

Fix WITHOUT reboot (the box is usually remote — a reboot you can't recover from is the real danger):
- Clear any wedged session: `loginctl list-sessions` → a `seat0` session `State=closing/online Active=no` whose leader pid is already dead is a phantom. `loginctl terminate-session <id>` then `loginctl kill-session <id>`.
- `sudo systemctl restart gdm`. It succeeds once even ~2 GB VRAM is free.
- Restore the physical display: find the live session's VT (`loginctl show-session <id> -p VTNr`) and `sudo chvt <N>`. The session flips to `Active=yes State=active`.
- If the greeter still can't draw, free VRAM first: `docker stop voxxy-engine-voxcpm` or `ollama stop <model>`, then restart gdm.

Permanent: recurs until GPU usage is capped — drop voxxy to one engine, set `OLLAMA_KEEP_ALIVE`/`OLLAMA_MAX_LOADED_MODELS=1`, or reserve a VRAM floor for the display. (First seen 2026-06-11.)

## Shell gotchas while investigating

- zsh: `echo ===X===` fails (`=word` expansion). Quote it: `echo '===X==='`.
- `sudo -n` first to test for passwordless sudo; many probes (dmesg, root crontab) silently need it.
