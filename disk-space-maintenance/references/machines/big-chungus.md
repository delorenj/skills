# big-chungus — disk profile

**Last verified:** 2026-10-28 (initial survey) — if a run contradicts this file, the run wins: fix the file.

Sizes are GiB unless marked GB. `df -B1G` is GiB; Prometheus and `docker system df` print decimal GB (x1.0737 to get GiB). Measured with `survey.sh`, `gdu`, `sudo du -x`, `docker system df`, and Prometheus on 2026-10-28 05:10-05:30 EDT.

## Identity

- **OS/hardware:** Ubuntu 25.10, kernel 6.17. AMD Ryzen 9 9950X (32 threads), 125 GiB RAM, RTX 3090.
- **Disk layout:** one volume. `/dev/nvme0n1p2` ext4, 3666 GiB (3.6T), mounted `/`. Everything is on it: `/home`, `/var/lib/docker`, `/tmp` (real disk; `tmp.mount` is masked, not tmpfs), `/mnt/TheChung`, `/var/lib/lemonade`, swap. Plus `/boot/efi` (vfat, 511M, irrelevant). No LVM, no LUKS, no second data disk. ext4 reserves 5% (~183 GiB) for root, so `df` Use% reads about 4 points higher than the real fill (75% shown, ~71% real) and non-root writers hit ENOSPC while root-owned daemons (dockerd) can still write.
- **Swap:** `/swapfile64`, 64 GiB, in `/etc/fstab`, currently ~50-54 GiB used. An inactive 8 GiB `/swapfile` (Mar 10, not in fstab, not active) also exists.
- **Role:** the DeLoNET workstation and homelab server. It runs the Docker stacks in `~/docker/stacks` (Prometheus/Loki/Grafana, Postgres, qdrant, NATS, Traefik, hindsight, ...), the 33GOD platform, the Hermes agent fleet (all agents share one cgroup, `zellij-ark.service`), ~25 GitHub self-hosted Actions runners in `~/actions-runner/*` (cgroup `ci.slice`), Jellyfin, `lemond` (lemonade LLM server, user `lemonade`), Android emulators, Steam, music production. Every agent harness (claude, codex, opencode, gemini, hermes, orca) writes here constantly.
- **Who:** Jarad (`delorenj`, uid 1000) is the only human. A second account `node` exists with an empty home.
- **Reach:** it is the hub; you are usually already on it. From another box: `ssh big-chungus` over the tailnet (`big-chungus.burro-salmon.ts.net`). Do not hardcode LAN addresses.
- **sudo:** passwordless (`sudo -n` works). Root-only measurement is available (`sudo du`, `lsof`, other users' dirs).

## Baseline

- **2026-10-28:** 873 GiB free (`df` Avail; Prometheus 937 GB), 2608 GiB used, 75% shown, inodes 10%.
- **History:** 76 GiB free / 98% on 2026-10-14 (first emergency); ~1411 GiB free on 2026-10-15 after the sweeps; 1132 GiB on 2026-10-19; 870 GiB on 2026-10-24; flat 865-890 GiB since.
- **Healthy:** 800 GiB free or more with a flat 24h trend. The current plateau is the floor of "healthy"; there is no longer any slack hiding in caches, because the bounded accumulators are already bounded.
- **Tight:** under 600 GiB free (a Prometheus `RootDiskLow` pending, which fires at less than 15% free = 550 GiB). Time to run the tier-A playbook and look at tier B.
- **Emergency:** under 300 GiB free (`RootDiskCritical` at less than 8% = 293 GiB), or ENOSPC symptoms, or Prometheus `RootDiskFillsWithin24h`. Docker, Postgres and the journal start failing writes well before 0. Go straight to `references/emergency.md` and the tier-A items below, build cache first.
- **Alerts that exist:** Prometheus group `disk_space` (`~/code/33GOD/monitoring/prometheus/rules/disk-space.yml`): RootDiskLow, RootDiskCritical, RootDiskFillsWithin7d (6h trend), RootDiskFillsWithin24h (1h trend), RootDiskMetricMissing, then Alertmanager to Telegram. All five show `inactive/ok` on 2026-10-28. Prometheus retention is 200h, so trend windows must stay under about 8 days. Query: `curl -s 'http://localhost:9472/api/v1/query_range?query=node_filesystem_avail_bytes{mountpoint="/"}&start=..&end=..&step=6h'`.

### Are the bounds holding? (verified 2026-10-28)

Mostly yes for what they target; the disk is still 540 GiB lower than on 2026-10-15 because of new agent-driven project data, not a failed bound.

- Free space fell 1411 GiB (Oct 15) to 1132 (Oct 19) to 870 (Oct 24), then **went flat at 865-890 GiB for four days** with a daily sawtooth: roughly +20-25 GB overnight when the 05:xx sweeps run, drained back by daytime agent and build writes. Prometheus 6h samples, GB: 1215 (10-19 21:10), 1012 (10-23 03:10), 947 (10-24 03:10), 928-955 (10-25 to 10-27), 934 (10-28 03:10).
- What the Oct 15-24 drop was made of (files written after 2026-10-15, `find -newermt`): uv archives 45 (torch/CUDA re-resolved per venv), `tower-of-lost-things/artifacts` 40 (gitignored), Claude `vm_bundles` 20, `gruvato/src-tauri/target` 19, `~/.cache/gruvato` ~70 (venvs, HF blobs, cargo targets, all created Oct 22-26), vinyl traces 16, Postgres dumps 12 (rotating), Android AVDs ~17, green-in-between server targets 15, `/tmp/*-target` Rust builds ~15. None of these is a regression of a swept accumulator; they are new owners with no bound yet (see Known accumulators).
- The sweeps are running: cache-prune weekly freed 15.6 GiB (Oct 25) and 16.5 GiB (Oct 26 13:29); cache-prune-daily frees 4.5-5.3 GiB per run (df delta, includes concurrent writes); docker-prune, state-maintain, user-logrotate run daily with `failed=0`; root `logrotate.service` exited 0 on Oct 28 00:42; journald holds at 1 GiB.
- **Not holding:** (1) the user `systemd-tmpfiles-clean.service` has **failed every night since at least 2026-10-25** (exit 73 CANTCREAT) on root-owned files under `~/.claude/tmp` (a scapy venv `__pycache__` in a Claude session scratchpad, and read-only test dirs `pjC-*`, `rollback-*`); it still cleans the rest and `~/.claude/tmp` is 4.8 GiB, but those paths never age out and the journal floods. (2) apt `Keep-Downloaded-Packages "false"` is **not effective**: `/var/cache/apt/archives` holds 38 debs (5.4 GiB), all written 2026-10-20 to 10-27 (claude-desktop, chrome, tailscale). (3) Docker build cache sits on a plateau of **245-255 GB** after every daily prune (the filter is `until=72h`, so it never goes lower than three days of builds).

## Never touch

Personal data, live service state, and unrecoverable things. Specific:

- **Docker named volumes.** `docker volume prune` and `docker system prune --volumes` are forbidden. Live data: `persistence_qdrant_data` (20 GB), `candystore_pgdata` (17), `monitoring_loki_data` (6.6), `monitoring_aai_llm_observability_state` (4.5), `bloodbank_bloodbank-nats-data` (3.6), `monitoring_prometheus_data` (3.2), `intelliforia-local_if_pgdata`, `*neo4j*`, `33god_*`, `opencode_data`, `ssbnk_data`, `zshyzsh-ssl-certs`, and the dozens of others held in the 2026-07-08 sweep. 254 volumes exist; 47 are attached. An unattached named volume is not dead (a stopped stack's database looks identical). Only the 64-hex anonymous ones, older than 7 days and attached to nothing, are swept by `docker-prune`.
- **Docker images that are locally built and still named by a compose file** (no registry digest, so un-pullable): `voxxy-voxxy-engine-vibevoice`, `voxxy-voxxy-engine-voxcpm`, `god-g6-voxcpm`, `delorenj/comfyui`, `enricher:local`, `cal-diy:*`. `docker-prune` already keeps these; do not `docker image prune -a` over them.
- **Databases and state that prune themselves or must not shrink:** `~/.local/state/holocene/events.sqlite3` (4.8 GiB, API prunes hourly to a 30d window), `~/.hermes*/state.db` and `*/agents/hermes/pm/runtime/state.db` (hermes auto-prune), `~/.n8n/database.sqlite`, `~/.local/state/33god/hook-hub/receipts.sqlite3` (state-maintain keeps 3 days), `~/.pg0` and hindsight data, `/var/lib/postgresql` (2.3 GiB), `~/.codex/thread_history_1.sqlite`, `~/.local/share/opencode/opencode.db` (sessions are history). Never `rm` these; never VACUUM one while it is open.
- **Agent history:** `~/.claude/projects` (8.9 GiB, Claude Code manages it with `cleanupPeriodDays`), `~/.codex/sessions` (state-maintain zstd-compresses, never deletes), `~/.hermes/profiles`, `~/.local/state/hermes-runtime-backups`.
- **Backups and vaults:** `~/backups/postgres` (nightly dumps with a rotation of about 9 and an offsite restic copy; the newest copies are the point), `/vault`, forever-ago vault backup, restic repos, `~/.local/state/intelliforia-pre-purge-backup`.
- **Personal creative/media data:** `~/Music` (46 GiB, FL Studio, Bitwig, presets), `~/.local/share/sh.delo.stemjangler/library` (38 GiB), `~/.local/share/sh.delo.gruvato/library`, `~/.vst3`, `~/vst`, `~/DeLoDrive`, `~/fireflies-archive` (29 GiB of assets), `~/HeyMa`, `~/gd`, `~/Documents`, `~/Archive`, `~/code/voxxy/voices` (`carlin.aup4` 4.6 GiB is a project file).
- **Source:** everything in `~/code/*` except `target/`, `.venv`, `node_modules` that the sweeps already classify. Run `git unpushed` before deleting any repo-level directory. Never `git clean -fdx` in a repo here.
- **Live toolchains:** never `mise prune` (see Gotchas). Never delete `~/.local/share/uv/tools` (22.9 GiB; `voxxy` and other services run from these venvs and `~/.local/bin` shebangs point into them), `~/.rustup/toolchains` (a service or `rust-toolchain.toml` may pin one), mise `python` 3.13.2 and 3.14.2, `swift`, `rust 1.95.0`.
- **Running-app state:** `~/.config/Claude/vm_bundles` (12.7 GiB, the live Claude desktop VM; `rootfs.img` and `sessiondata.img` are rewritten every few minutes and look like 10 GiB sparse files), `~/.config/google-chrome`, `~/.config/teams-for-linux`, `~/.config/Slack`, `~/.config/obsidian`.
- **System:** `/swapfile64` (in use, 50+ GiB resident; `swapoff` under memory pressure risks the 2026-09-18 livelock), `/usr` (41 GiB, includes `/usr/share/ollama` 7 GiB and CUDA), `/opt` (16 GiB of installed apps), `/boot`, `/nix`.
- **Cgroup note:** never size or cap anything from `memory.current`; read `memory.stat` anon (page cache and slab are reclaimable). Never cap `zellij-ark.service`.

## Space map

Accounted 2026-10-28: home about 1,430 + `/var` 552 + `/mnt` 451 + `/usr` 41 + `/tmp` 37 + `/opt` 16 + `/root` 5 + swap 72 = about 2,604 GiB against 2,608 GiB used by `df`. Within 1%.

Class: A = rebuildable/safe to delete without asking, B = needs an owner decision, C = never.

| Path | Size | Class | Notes |
|---|---|---|---|
| `/var/lib/docker` (total on disk) | 434 | mixed | `docker system df` shows 497 GiB-equivalent because layers and caches overlap. Parts below. |
| docker build cache | 260 GB (174 "reclaimable") | A | 2746 records, 0 active. Plateau 245-255 GB after the daily 72h prune. Pure rebuild cost. Largest single lever on this box. |
| docker images | 185 GB (108 "reclaimable") | A/B | 370 images, 106 in use. Reclaimable overstates (shared layers) and includes locally built images. Daily prune already takes the old, pullable, unreferenced ones. |
| docker named volumes | 59 GiB on disk (82 GB by `df`) | C | 254 volumes, 47 attached. See Never touch. Only anonymous 64-hex ones are swept. |
| docker containers | 6.5 GB | C | 143, 127 running. |
| `/mnt/TheChung` | 451 | B | Torrent/media library on the root disk (`24.S01` 97 GiB, Back to the Future II 18, Chucky collection 18, ...). Jarad's media. Not a cache. |
| `~/code/ComfyUI` | 112 | B | `models/` is 112 GiB; regrows by download. The 2026-10-14 sweep removed Q8 GGUF copies and they came back. |
| `~/code` (rest) | 297 | mixed | `UnrealEngine` 62.7 (B, engine checkout), `tower-of-lost-things` 41 (`artifacts/` 40 GiB, gitignored; B), `hot` 35 (`output/` 26.7 B, `.venv` 8.4 A), `green-in-between*` 37 (`server/target` 12.7 + 7.3 A once stale), `gruvato` 22 (`src-tauri/target` 20: A via cache-prune after 14d), `navi` 11, `slowburns` 10, `33GOD` 8.4, the rest under 7 each. |
| `~/.local/share/Steam` | 74.6 | B | Native Steam, `steamapps` 73 GiB. A second Steam lives in flatpak (`~/.var/app/com.valvesoftware.Steam`, 69.6 GiB). Two installs = 143 GiB of games. Never-launched ones were deleted on 2026-10-14; the rest need Jarad. |
| `~/.cache` | 148 | mixed | `gruvato` 63 (B), `uv` 17.9 by gdu (32.5 by `du`, hardlinks double-counted; A via prune), `huggingface` 15.4 (B, keep-list), `tower-of-lost-things` 6.9, `google-chrome` 5.2, `gib-native` 4.3, `mobile-deploy-hub` 3.4, `opencode` 2.5, `codex-runtimes` 1.7. |
| `~/.cache/gruvato` | 63 | B | `meter-ab` 17.4 (one 15.4 GiB HF blob), `groove-synth` 12.8, `realmix-cc` 8.6, plus beatthis/demucs/flamingo/fal venvs and `gruv-127-target`. All created 2026-10-22..26 by the gruvato audio pipeline. Rebuildable, but ask: it is in active use. |
| `~/.var` | 78.2 | B | Flatpak app data: Steam 69.6, WineCharm 4.6, Heroic 1.7, Slack 1.4. |
| `~/Videos` | 88 | B | `Recordings` 66.7 GiB (OBS captures; one 8.6 GiB mp4), `tom green`, movies. Jarad's. |
| `~/.local/share/mise/installs` | 30.1 | A/C | python 11.4, node 10.6, swift 3.4, flutter 2.3. Live interpreters. Trim only `bun uv pnpm` through cache-prune. |
| `~/.local/share/uv` | 22.9 | C | `tools/` 22.9 GiB: uv tool venvs that services run from. |
| `~/.local/share/wineprefixes` + `~/.wine` | 17.7 + 15.3 | B | `poppy-playtime` prefix 17.5 GiB. |
| `~/.local/state/vinyl/traces` | 17.9 | B | Float32 dictation audio (`audio.f32le`) plus `events.jsonl`. One trace is 9.3 GiB (a session left recording Oct 24-26). 1.9 GiB on Oct 15, so it grew 16 GiB in 13 days. No retention. |
| `/var/lib/lemonade/.cache` | 61 | B | Root-owned (`lemonade` user) HF model cache for `lemond`. Models, re-downloadable but slow. |
| `~/actions-runner` | 32.5 | A (when idle) | `_work` dirs 0.6-2.9 GiB each across ~25 runners; swept daily when no `Runner.Worker` runs. `_tool`/`_actions` are runner-managed. |
| `~/Music` | 46.2 | C | |
| `~/fireflies-archive` | 29.1 | C | |
| `~/.config/Claude` | 14.6 | C | `vm_bundles` 12.7, in use. |
| `~/Android` + `~/.android` | 23.6 + 12.2 | B | `Sdk/system-images` 11 GiB, AVDs: `HOLOC_9_Honda_API33`, `Medium_Phone`, `towe16crank`, `Holocene_API32_Compatibility`; each has a 2-3 GiB `snapshots/default_boot/ram.img` and a 2.5-6 GiB qcow2. |
| `~/.hermes` | 17.5 | C | profiles 8.4, hermes-agent 4.0, installs 2.8. |
| `~/HeyMa`, `~/DeLoDrive`, `~/backups`, `~/gd`, `~/Downloads` | 17, 16, 15.4, 8.4, 9.8 | C (Downloads B) | `backups/postgres` 14 GiB is bounded rotation. |
| `/swapfile64` (+ inactive `/swapfile` 8 GiB) | 64 (+8) | C (`/swapfile` B) | `/swapfile` is not in fstab and not active; deleting it frees 8 GiB if Jarad agrees. |
| `/tmp` | 37.4 | A (stale part) | 8,573 entries, only 5 older than 10 days (the system 10d rule holds), so the bytes are fresh agent builds: `gib-p5-target` 4.5, `rev-pool51-target` 4.4, `gib-direv-r1-target` 3.9, `r2-target` 2.6, `tokies-drift` 2.0, `ci-fix` 1.4. Cargo targets in `/tmp` are outside cache-prune's `~/code` scope. |
| `/usr` | 41.4 | C | |
| `/var/lib/rancher/k3s` | 23.8 | B | `k3s` is inactive; 24 GiB of containerd content. Dead cluster, ask before `k3s-uninstall`/rm. |
| `/var/lib/flatpak` | 16.7 | B | `repo` 15 GiB; `flatpak uninstall --unused` is the tool. |
| `/opt` | 16 | C | wine 1.5+1.5, codex-desktop 1.3, mssql 1.3, OpenWhispr 1.0. |
| `~/.config` (rest) | 23.6 | C | google-chrome 8.5, nerd-dictation 3.8, obsidian 1.9. |
| `~/.claude` | 14.2 | C/A | `projects` 8.9 (C), `tmp` 4.8 (A, tmpfiles-managed, see Gotchas). |
| `~/.codex` | 5.2 | C | `sessions` 2.0, `thread_history_1.sqlite` 1.3, `packages` 1.2 (releases pruned by cache-prune), `.tmp` 0.16. |
| `~/.gradle` 8.4, `~/.rustup` 8.4, `~/.npm` 5.3, `~/.bun` 2.5, `~/.local/share/pnpm` 4.0 | 28.6 | A | Package caches. gradle: `--stop` first. |
| `/var/cache/apt` | 5.4 | A | 38 `.deb` files from 10-20..10-27; `apt-get clean`. |
| `/var/lib/snapd` + `~/snap` | 6.1 + 4.6 | A/B | Old revisions; `refresh.retain=2` is set. |
| `/root` | 4.9 | B | `.local` 2.1, `.wine` 1.8 (root ran wine once), `.npm` 0.7. |
| `/var/log` | 1.4 | A | journal 1.0 GiB (capped), rest rotated. |
| `~/.local/share/Trash` | 1.7 | A | Expires at 14 days via cache-prune. |

**Could not measure:** `/mnt/ncdata` (Nextcloud data, owner `www-data`, mode 0750) was inside the `sudo du` of `/mnt` and is small; per-container overlay sizes inside `/var/lib/docker/overlay2` were not walked (the walk takes 5+ minutes and double-counts layers); `gdu` and `du` differ by up to 1.8x on hardlink-heavy caches (uv, pnpm, bun, cargo targets) so those rows are upper bounds. `lsof +L1` real deleted-but-open files are only 100-220 MiB each (old `opencode`, `orca-ide`, hermes python after updates).

## Known accumulators

| What regrows | Where | Observed size | Growth driver | Bound today | Recommended bound |
|---|---|---|---|---|---|
| Docker build cache | `/var/lib/docker/buildkit` | 245-260 GB plateau | CI/test stacks, voxxy/comfyui/gib builds | `docker-prune` daily, `builder prune --filter until=72h` | `until=24h`, and a `--keep-storage 60GB` cap |
| Docker images (unused) | `/var/lib/docker/overlay2` | 178-214 GB, 106 of 370 in use | `docker build`, CI pulls, ECR tags | `docker-prune` daily, unused and older than 7d, spares locally built images named by compose | none needed; watch the 33 GB voxxy engines |
| Anonymous docker volumes | `/var/lib/docker/volumes` | 19 removed on 10-27 | `docker run` without `-v name:` | `docker-prune` (unattached, older than 7d, 64-hex names only) | none |
| uv cache | `~/.cache/uv`, `archive-v0` | 17.9-32.5 GiB; 45 GiB written since Oct 15 | torch + CUDA resolved into many venvs | `cache-prune` weekly, `uv cache prune --force` (needs `--force`: daemons hold the lock) | also run weekly prune after big ML installs; per-project `UV_LINK_MODE` is already hardlink |
| Rust targets | `~/code/*/target`, `~/.cache/gruvato/*-target` | gruvato 20, green-in-between 20, ... | cargo builds by agents | `cache-prune` weekly: target older than 14d, `incremental` older than 2d, skips service-run targets | cap with shared `CARGO_TARGET_DIR` on a swept path; extend sweep to `~/.cache/*/` and `/tmp/*-target` |
| `/tmp/*-target`, `/tmp/*` build dirs | `/tmp` | 37 GiB, all under 10 days | agent verification/CI builds outside `~/code` | system tmpfiles `q /tmp 10d` | 3d rule for `/tmp/*-target` and `/tmp/*-pool*` |
| Agent scratch | `~/.claude/tmp` (`TMPDIR`) | 4.8 GiB (was 85 GiB) | every harness's mktemp, go-build, pytest | user tmpfiles: 5d top-level, 2d for go-build/pytest/tmp.*, 4d `opencode`, 7d `claude-1000/*/*` | fix the unit failure (root-owned files) or the bound is partial |
| Codex git scratch | `~/.codex/.tmp`, `~/.config/orca/codex-runtime-home/home/.tmp` | ~244 dirs / hour boundary | codex app-server leaks 2 `git-*` per ~30s | `cache-prune --codex-tmp` hourly | none |
| Codex releases/updater | `~/.codex/packages/*/releases`, `~/.cache/codex-update-manager` | 0.4 GiB per release; Codex.dmg 0.8 | self-update never prunes | `cache-prune` weekly/daily | none |
| Claude Code versions | `~/.local/share/claude/versions` | 0.8 GiB total | self-update | `cache-prune` daily (keep newest 2) | none |
| Headless Chrome profiles | `~/.config/google-chrome-headless/scoped_dir*` | 0.3 GiB (was 26) | SIGKILLed headless chrome | `google-chrome-clean` wrapper; `cache-prune` sweeps leftovers older than 1d | none |
| Holocene events | `~/.local/state/holocene/events.sqlite3` | 4.8 GiB (2.3 on Oct 15) | event bus | hourly in-process prune to 30d window (still filling) | watch; if it passes ~7 GiB check the prune |
| hook-hub receipts | `~/.local/state/33god/hook-hub/receipts.sqlite3` | 0.45 GiB | one row set per hook | `state-maintain` daily, 3d retention | none |
| opencode.db | `~/.local/share/opencode/opencode.db` | 1.9 GiB | sessions | `state-maintain` incremental vacuum only | none (history) |
| Agent transcripts | `~/.codex/sessions`, `~/.gemini/tmp` | 2.0 GiB | sessions | `state-maintain` zstd after 30d | none |
| HOME logs | codex-desktop launcher, kapture, pm2, hermes `*.stderr.log`, etc. | small now | appenders | `user-logrotate` daily (logrotate copytruncate + `log-sweep` age rules) | add a rule when a new appender shows in the survey's Logs section |
| Root logs | `/var/log` | 1.4 GiB | syslog, crowdsec, tailscale-monitor | root logrotate (daily + maxsize 400M for rsyslog), journald 1G/3 weeks | none |
| GitHub runner `_work` | `~/actions-runner/*/_work` | 0.6-2.9 GiB each, ~25 runners | checkout per job | `cache-prune --daily`, only when no job running | none |
| Trash | `~/.local/share/Trash` | 1.7 GiB | GUI deletes | `cache-prune` daily, 14d | none |
| HF hub | `~/.cache/huggingface/hub` | 15.4 GiB | model downloads | `cache-prune` weekly: unread for 60d, except `cache-prune.hf-keep` | none |
| **apt debs** | `/var/cache/apt/archives` | 5.4 GiB, 38 files, all since Oct 20 | claude-desktop (170 MB), chrome, tailscale updates | **none** (`Keep-Downloaded-Packages false` is not working) | `DPkg::Post-Invoke {"rm -f /var/cache/apt/archives/*.deb";};` or weekly `apt-get clean` |
| **vinyl dictation traces** | `~/.local/state/vinyl/traces/*/audio.f32le` | 17.9 GiB, +16 GiB in 13d | `vinyl` records float32 audio per session, one session ran 40 hours | **none** | `log-sweep` rule: delete `audio.f32le` older than 7d (keep `events.jsonl`), and a size cap per trace |
| **`~/.cache/gruvato`** | gruvato audio pipeline | 63 GiB, born Oct 22-26 | `meter-ab` HF blobs, demucs/beatthis/flamingo venvs, `gruv-127-target` | **none** | ask owner; extend `cache-prune` to venvs older than 30d under `~/.cache/*` |
| **`tower-of-lost-things/artifacts`** | `~/code/tower-of-lost-things/artifacts` | 40 GiB, all since Oct 19 | crank/cutscene/anim-lab renders (gitignored) | **none** | age rule (30d) or move to `DeLoDrive` |
| **Claude desktop vm_bundles** | `~/.config/Claude/vm_bundles` | 12.7 GiB (22 on Oct 15) | Claude desktop VM images | none (in use) | none; leave |
| **Android AVDs** | `~/.android/avd/*` | 12.2 GiB | emulator snapshots `ram.img` 2-3 GiB each | none | delete `snapshots/default_boot` when emulator is closed (B) |
| **tmpfiles unit failing** | user `systemd-tmpfiles-clean` | n/a | root-owned `__pycache__`/read-only dirs under `~/.claude/tmp` | unit **failed** nightly | `sudo chown -R delorenj:delorenj ~/.claude/tmp` once; find what runs python/test fixtures as root |
| Postgres dumps | `~/backups/postgres/dbs` | 14 GiB (candystore dump 1.3 GiB/day) | nightly dump | rotation of ~9 + restic offsite | none |

## Targeted playbook

Run measurements first (`bash scripts/survey.sh`), check `heavy --status`, and **batch heavy work through `heavy <cmd>`** (the box is shared by every agent; `heavy` yields to them and has its own memory ceiling). Never kick several cleanup sessions at once: two `uv cache prune` runs, a journal vacuum and a `docker prune` collided on locks on 2026-10-14. Check `pgrep -af 'uv cache|docker (system|builder|image) prune|cache-prune|state-maintain'` first.

Nothing below was executed (the profile pass was read-only). Yields are estimates from the 2026-10-28 survey; replace them with real numbers in the run log after the first cleanup.

### Tier A, safe without asking (biggest first)

1. **Docker build cache** (est. 100-170 GB; docker reports 174 GB reclaimable, the real figure is lower).
   Precondition: `pgrep -af 'docker( buildx)? build|buildctl'` returns nothing and no `mise run` image build is in flight.
   ```bash
   docker builder du | tail -3
   docker builder prune -f --filter until=24h        # keeps the last day of builds
   # emergency only, drops all cache:  docker builder prune -a -f
   ```
2. **Stale cargo targets in `/tmp`** (est. 15-25 GiB). Precondition: `pgrep -x 'cargo|rustc'` shows nothing writing there.
   ```bash
   /usr/bin/find /tmp -maxdepth 1 -type d -name '*-target' -mtime +1 -print     # review
   /usr/bin/find /tmp -maxdepth 1 -type d -name '*-target' -mtime +1 -exec rm -rf {} +
   ```
   Use `/usr/bin/find`, not bare `find` (zsh `find` is a bfs function).
3. **apt debs** (5.4 GiB).
   ```bash
   sudo apt-get clean
   ```
4. **The codified sweeps, in this order** (about 16 GiB weekly set + 5 GiB daily set + docker images). Dry-run first. These are the same jobs candybar runs, so a manual run is safe to repeat.
   ```bash
   ~/code/infra/scripts/cache-prune --dry-run | grep -E 'would|dry-run' | head -50
   heavy ~/code/infra/scripts/cache-prune --daily      # trash, updater leftovers, runner _work, rust incremental, codex tmp
   heavy ~/code/infra/scripts/cache-prune              # weekly: uv/bun/npx/mise(bun,uv,pnpm only)/pnpm/go caches, HF, codex releases, stale targets/venvs
   ~/code/infra/scripts/docker-prune --dry-run && ~/code/infra/scripts/docker-prune
   ~/code/infra/scripts/state-maintain                  # sqlite free pages + zstd old transcripts
   ~/code/infra/scripts/user-logrotate
   ```
   `cache-prune`'s `uv cache prune --force` is deliberate: long-lived `uv run --script` daemons hold the lock, so the polite attempt always times out. A manual `uv cache prune` without `--force` will hang for the lock timeout.
5. **Fix and run the user tmpfiles job** (a few GiB, mostly it stops the nightly failure).
   ```bash
   sudo /usr/bin/find ~/.claude/tmp ! -user delorenj -print | head          # review
   sudo chown -R delorenj:delorenj ~/.claude/tmp
   systemd-tmpfiles --user --clean && systemctl --user reset-failed systemd-tmpfiles-clean.service
   ```
6. **Package caches, when tight** (est. 5-10 GiB). `gradle --stop` first, never while a build runs.
   ```bash
   gradle --stop 2>/dev/null; rm -rf ~/.gradle/caches/build-cache-* 2>/dev/null
   pnpm store prune; go clean -cache; npm cache clean --force
   ```
7. **Journal and root logs** (rarely needed: bounded at 1 GiB). `sudo journalctl --vacuum-size=500M`. Test the real config with `sudo logrotate -d /etc/logrotate.conf` (`-d` on a single file gives false "insecure permissions").
8. **Inactive snaps/Flatpak runtimes** (est. 1-4 GiB): `flatpak uninstall --unused -y`; `snap list --all | awk '/disabled/{print $1,$3}'` then `sudo snap remove <name> --revision=<rev>`.

Do not use: `mise prune`, `cargo clean` in a directory a service runs from, `docker system prune -a --volumes`, `docker volume prune`, `uv cache clean` while daemons run (use `prune --force`), `rm -rf ~/.cache` wholesale.

### Tier B, decisions to put to Jarad

Phrase each as a question with the number and the cost of "yes".

1. **`/mnt/TheChung` media library, 451 GiB.** "Is this still wanted on the root disk? Biggest: `24.S01...` 97 GiB, Back to the Future II 18, Chucky 18. Cost of yes: gone (torrent re-download). Move to a NAS/second disk instead?"
2. **Docker build cache to a hard cap, 100-250 GB.** "OK to switch `docker-prune` to `until=24h` plus `--keep-storage 60GB`? Cost: first rebuild of each image after a day idle is slower."
3. **Two Steam installs, 143 GiB.** Native `~/.local/share/Steam` 74.6 and Flatpak 69.6. "Which one do you actually use? Uninstall unplayed games from the other."
4. **`~/.cache/gruvato`, 63 GiB.** "Is the gruvato audio pipeline still being iterated? `meter-ab` 17, `groove-synth` 13, `realmix-cc` 8.6, plus 5 venvs rebuildable. Cost: re-download of a 15 GiB HF blob."
5. **`tower-of-lost-things/artifacts`, 40 GiB.** "Keep which of cutscenes-20261019 (8.5), crank-20261022 (5.9), anim-lab (5.4)? Move the rest to `DeLoDrive`/delete."
6. **`/var/lib/lemonade/.cache` (61 GiB) and Ollama (7 GiB in `/usr/share/ollama`).** "Which local LLM models are in use by `lemond`? Cost: slow re-download."
7. **`~/code/ComfyUI/models`, 112 GiB** and **`~/code/UnrealEngine`, 62.7 GiB.** "Prune unused checkpoints? Is the UE5 source checkout still needed?"
8. **`~/.local/state/vinyl/traces`, 17.9 GiB.** "Delete `audio.f32le` older than 7 days and install a retention rule?" Recommended yes; keep `events.jsonl`.
9. **Android AVDs and `Sdk/system-images`, 35 GiB.** "Delete the `snapshots/` and the AVDs you no longer test on (HOLOC_9, Medium_Phone, towe16crank, Holocene_API32)?" Cost: emulator cold boot.
10. **`~/Videos/Recordings`, 66.7 GiB** and **`.wine/poppy-playtime` prefix, 17.5 GiB** and **`~/.var` WineCharm/Heroic**: "Still wanted?"
11. **k3s leftovers, `/var/lib/rancher/k3s`, 23.8 GiB**, and inactive **`/swapfile`, 8 GiB.** "Cluster is stopped; OK to run `k3s-uninstall.sh` and delete?"
12. **`/var/lib/flatpak`, 16.7 GiB, `~/snap` 4.6 GiB, `~/Downloads` 9.8 GiB.**

Decisions recorded: none yet. Add Jarad's answers here so the next run does not re-ask.

### Bound the regrowers (do after reclaiming, same session)

Per the skill's rule, fix the accumulator not the pile. In priority order, all in `~/code/infra`: (1) apt debs post-invoke rule under `system/apt.conf.d/`; (2) a `log-sweep` rule for vinyl `audio.f32le` older than 7d; (3) `docker-prune` `until=24h` and `--keep-storage`; (4) extend `cache-prune`'s rust-target step to `/tmp/*-target` and `~/.cache/*-target`; (5) fix the `~/.claude/tmp` root-owned files so tmpfiles stops failing; (6) add an owner and bound for `~/.cache/gruvato` and `tower-of-lost-things/artifacts`. Then `git unpushed` and land it.

## Installed automation

All cache/state/log sweep scripts live in `~/code/infra` and ran green in the last day. **Scheduling moved to candybar on 2026-10-26 (wave 7.7):** the old `.timer` units are retired (`not-found`, do not `enable` them; that double-schedules), but the `.service` units remain and candybar's systemd runner fires them with `systemctl --user start --wait`. So `systemctl --user list-timers` will NOT show them (the survey's "Cleanup automation" section lists the dead timers as `next: -`); check candybar instead.

| Job | Schedule (America/New_York) | What | Last verified run | Notes |
|---|---|---|---|---|
| `cache-prune-codex-tmp` | hourly :17 | codex `git-*` scratch dirs | 2026-10-28 05:17 ok | candybar `verified` |
| `cache-prune-daily` | 05:23 daily | trash 14d, codex-update leftovers, claude versions keep 2, runner `_work`, rust incremental 2d, chrome headless | 2026-10-27 05:23, freed 4.9 GiB | `verified` |
| `cache-prune` | Sun 05:07 weekly | uv/bun/npx/mise(bun,uv,pnpm keep 3)/pnpm/go, codex releases, stale rust targets (14d), HF (60d unread), stale `.venv`/`node_modules` (30d, lockfile required) | last ran 2026-10-26 13:29 (freed 16.5 GiB); native 10-25 05:17 (15.6 GiB) | candybar status **`cutover`, not yet `verified`**: first candybar-scheduled fire is Sun 2026-11-01 05:07 EST. Check it. |
| `docker-prune` | 05:41 daily | dangling + unused old images (7d), build cache (72h), anonymous volumes (7d) | 2026-10-27 05:41, `failed=0` | `verified`; header says weekly, it is now daily |
| `state-maintain` | 05:40 daily | sqlite retention + vacuum, zstd transcripts older than 30d | 2026-10-27 05:40 | `verified` |
| `user-logrotate` | 05:17 daily | logrotate (copytruncate) + `log-sweep` age rules | 2026-10-27 05:17 | `verified` |
| user `systemd-tmpfiles-clean` | 04:20 daily (+10min) | `~/.claude/tmp` rules (`systemd/user-tmpfiles.d/claude-tmp.conf`) | **FAILED nightly, exit 73** | see Gotchas |
| system `systemd-tmpfiles-clean` | 21:28 daily | `/tmp` 10d, `/var/tmp` 30d | ok | |
| root `logrotate` | daily | `/etc/logrotate.d/{rsyslog,delonet-logs}`, installed by `logrotate/install-system.sh` | 2026-10-28 00:42 ok | the duplicate `cloud-init-base` conffile that made it exit 1 was removed |
| journald | n/a | `SystemMaxUse=1G`, 3 weeks | 1.0 GiB | `/etc/systemd/journald.conf.d/99-delonet.conf` |
| `docker-stack-ssbnk-cleanup.timer` | 02:00 daily | ssbnk retention | | system timer |
| `fstrim.timer` | weekly | discard | | |
| apt `Keep-Downloaded-Packages false` | n/a | `/etc/apt/apt.conf.d/99-no-keep-debs` | **not effective** | 5.4 GiB of debs present |
| snap `refresh.retain=2` | n/a | | | |
| Prometheus `disk_space` rules | continuous | 5 alerts to Telegram | all inactive | see Baseline |
| `infra-doctor` | every 60s | PID-vs-port divergence probes, not disk | | candybar watchdog probe exists |
| restic + nightly Postgres dumps | nightly | `~/backups/postgres`, offsite restic with `forget` | ok | |

**Gaps:** nothing bounds `/tmp/*-target`, vinyl traces, `~/.cache/gruvato`, `tower-of-lost-things/artifacts`, apt debs, `/var/lib/lemonade`, Android snapshots, or Docker named volumes (by design). The Prometheus alerts watch free space only; no alert fires if a job silently stops (check candybar, `journalctl --user -u cache-prune --since -2d`). The weekly job has a single scheduler change not yet proven.

## Gotchas

- **Never `mise prune`.** It only sees config pins and removed python 3.13.2/3.14.2 (base interpreters of pipx/uv-tool venvs and `~/.local/bin` shebangs), swift (the ssbnk task tool) and rust 1.95.0 on 2026-10-14. cache-prune trims only `bun uv pnpm`, keeping 3.
- **Never `cargo clean` a target a service runs from.** `forever-ago` (vault backup) and `zellij-driver` run from `target/release`; cache-prune skips any target named by a unit file, crontab or `~/.local/bin` symlink. A stale mtime there means "stable", not "dead".
- **zsh `find` is a bfs function** in interactive shells and silently ignores `-newermt '-7 days'`. Use `/usr/bin/find` in every command and script.
- **The uv cache lock is held forever** by long-lived `uv run --script` daemons (curator-drain, pdf2md-serve, code-review-graph MCP, the voice scoring jobs running under `heavy` now). Plain `uv cache prune` waits then times out; `uv cache prune --force` is correct because those daemons only run already-resolved hardlinked venvs. `uv cache clean` is the destructive one: do not.
- **Root-owned `__pycache__` appears in caches** (`~/.cache/uv`, `~/.cache/huggingface`, `DeLoHome/.venv`, and now `~/.claude/tmp` scratchpad venvs). Something runs python as root; cause not found. It makes `uv cache prune`, `rm -rf` and `systemd-tmpfiles --clean` fail with EACCES. cache-prune chowns first; manual runs need `sudo chown -R delorenj:delorenj <dir>`.
- **`du` and `gdu` double-count hardlinks** (uv, pnpm, bun caches, cargo targets: `~/.cache/uv` reads 17.9 by gdu, 32.5 by `du`). Do not sum them as reclaimable. `survey.sh` uses `du`, so it overstates those rows.
- **Docker "reclaimable" overstates.** Shared layers count once per image; locally built images that a compose file names are not really reclaimable. `docker system df` Build Cache said 260 GB with 174 "reclaimable" and 0 active. Measure `df` before and after.
- **Never prune named volumes.** Unused-looking volumes hold databases of stopped stacks. `docker-prune` is written never to touch named ones.
- **G versus GiB, Prometheus versus df.** Prometheus `node_filesystem_avail_bytes` is bytes in decimal GB (937 GB) while `df -B1G` is GiB (873). They agree; the factor is 1.0737. The alert thresholds are ratios so they are unaffected. Sizing a cleanup target in the wrong unit is a 7% error.
- **`df` Use% runs about 4 points high** because of the 5% root reserve. 75% shown is ~71% real; do not compare with the pre-2026 "98%" language without checking Avail.
- **Deleted-but-open files:** `lsof +L1` shows real ones at 100-220 MiB (old `opencode`, `orca-ide`, hermes python after an update; restart the owner to release). The **2048 G entries `survey.sh` prints for `Runner.Li` (GitHub runner .NET), `jellyfin` and `marksman` are false positives**: sparse mmap'd files whose SIZE/OFF is the 2 TiB mapping, not disk usage. Ignore them; `survey.sh` should filter SIZE/OFF above 1 TiB.
- **The survey's automation section is blind to candybar.** The retired timers print `next: -`; the jobs are alive. Trust `journalctl --user -u cache-prune* -u docker-prune -u state-maintain -u user-logrotate --since -2d` and the candybar ledger (`~/code/33GOD/candybar/deploy/migration/ledger.yaml`), not `list-timers`.
- **`systemd-tmpfiles` ages on max(atime, mtime, ctime).** A top-level directory touched constantly (`~/.claude/tmp/opencode`) never ages under a top-level rule; it needs its own glob (done). Also `e` on a glob cleans the contents, not the directory.
- **Check the Prometheus history before blaming a nightly job.** The loss of 2026-10-14..24 was agent project writes during the day, not a failed sweep. Free-space deltas inside one run include concurrent writes (the "freed~5 MiB" lines).
- **Concurrent cleanup sessions collide on locks** (uv, docker, journal). Check for another session first; the scripts use `flock` on `$XDG_RUNTIME_DIR/*.lock` and exit 0 if another copy runs.
- **Run heavy jobs through `heavy <cmd>`** (`batch.slice`, yields to agents, own memory ceiling); size pools with `heavy --workers`, never `nproc`. A `--workers 28` pool saturated the box for 30 minutes on 2026-10-24. Never CPU-cap `zellij-ark.service`.
- **Sizing `/home` fast:** `gdu -n -x -p -o out.json /home` (about 1 minute) or plain `gdu -n -x -p <dir>` for one level. `json.load` on the 1.4 GB export eats ~15 GB RAM (no `ijson` installed here). A full `survey.sh` takes 20+ minutes on this disk under `heavy`; the `Written in the last 48h` and `Files >= 1G` walks plus a `sudo du` over `/var/lib/docker` are the slow parts. For a quick look use `--quick`, `docker system df`, `sudo du -xm -d1 /var /mnt /usr /opt`.
- **Never size a cgroup limit from `memory.current`** (40 GiB read = 0.9 GiB anon + page cache + slab).
- **`zellij-ark` and shells hold the `TMPDIR=~/.claude/tmp` convention.** Sweeping `/tmp` does not touch agent scratch; `~/.claude/tmp` is the one that was 85 GiB.
- **Some "looks big, is not" files:** `~/.config/Claude/vm_bundles/*/*.img` (10 GiB sparse-looking, but live), Postgres `.dump` (1.3 GiB, nightly, rotated), `thread_history_1.sqlite`.
- **`hermes-gateway`:** cleanup must never restart it with raw systemctl; use `hermes-gateway-restart --reason`. Killing `cargo`/`uv` daemons that agents use can cut in-flight turns.

## Run log

- 2026-10-28 — initial profile (read-only survey). Free: 873 GiB (937 GB, 75% shown). Nothing deleted. Found: tmpfiles unit failing nightly, apt keep-debs setting not working, docker build cache 245-260 GB plateau, `/mnt/TheChung` 451 GiB, `~/.cache/gruvato` 63 GiB, vinyl traces 18 GiB, k3s 24 GiB, lemonade 61 GiB.
