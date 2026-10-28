# tiny-chungus — disk profile

**Last verified:** 2026-10-28 (initial survey) — if a run contradicts this file, the run wins: fix the file.

## Identity

- **OS:** Omarchy (Arch Linux derivative), kernel 7.2.3-arch1-3, Hyprland desktop, SDDM. Up 15+ days.
- **Hardware:** a laptop. AMD Ryzen 7 7840U (Radeon 780M), 30 GiB RAM, zram swap 30.7G (about 100M used). Single 1.8T NVMe (`nvme0n1`).
- **Disk layout:**
  - `nvme0n1p1` 2G vfat is `/boot` (435M used, limine bootloader).
  - `nvme0n1p2` 1.8T is LUKS2. It opens as `/dev/mapper/root`, which holds one **btrfs** (zstd:3, ssd, space_cache=v2).
  - Mounted subvolumes: `@` is `/`, `@home` is `/home`, `@log` is `/var/log`, `@pkg` is `/var/cache/pacman/pkg`. All of them share the one pool, so there is no per-mount free space. `df` shows the same 1.7T free on each.
  - `snapper` has one config, `root` (`/`, `TIMELINE_CREATE=no`, `NUMBER_LIMIT=5`). `limine-snapper-sync` boots from snapshots, and `/boot/.../limine_history` and `/.snapshots` exist.
  - `/tmp` and `/dev/shm` are tmpfs (16G each, about 200M used), so they cost no disk.
- **Role:** Jarad's daily-driver desktop laptop, not a server. It is the TOKAMAK desk-widget deploy target, so the `~/.ssh/config` comment calls it "the desk widget host". It also runs:
  - Sunshine (game/desktop streaming)
  - syncthing (user unit)
  - tailscaled
  - the `vinyl` dictation client and `voxxy-listen`
  - `ssbnk` upload services
  - `openclaw-node` (a node host that dials big-chungus gateway `100.66.29.76:18789`)
  - a Codex desktop auto-update timer
  - 1Password, Telegram, Slack, Teams, Claude desktop, Chrome, Brave, Chromium, Firefox
  - heavy dev toolchains: mise, uv, rustup, pnpm, npm, bun, flutter, wine
- **Not present:** no CI runners (no `~/actions-runner*`), no Hermes gateway (`~/.hermes` is 8K), no cron (`crontab` is not installed), no snap or flatpak. Docker is installed but **not used**: `docker.service` is inactive and disabled, and the socket is active. Nothing else on this machine depends on docker, but see the Docker caveat under Gotchas.
- **User:** only `delorenj` (single user in `/home`), who is Jarad. Jarad is logged in on tty1 (since Oct 12) and also reaches it over SSH from big-chungus.
- **Reach:** `ssh tiny-chungus` (alias `tiny` also works). `~/.ssh/config` on big-chungus maps both to `HostName 100.120.32.73` (tailnet) and uses the default user `delorenj`. Use `ssh -o BatchMode=yes`.
- **sudo:** NO. `sudo -n true` fails with "a password is required". Anything that needs root (pacman cache, journal vacuum, snapper, docker data, `/var/lib`) needs Jarad at the keyboard or a password. The agent cannot do it unattended. Plan for this: tier A below is split into "no sudo needed" and "needs sudo (hand to owner)".

## Baseline

- **Today:** `/dev/mapper/root` 1.9T, **157G used (9%), 1.7T free**. btrfs reports 181 GiB allocated, 1.64 TiB unallocated, and `Data,single` 87.6% full inside its chunks. This is healthy and not tight.
- **Healthy:** below 25% used (about 470G). That is far away and needs no action.
- **Tight (start routine A-tier cleanup):** over 50% used (about 950G). At that point something is runaway, since the machine has grown only about 157G in a year.
- **Emergency:** over 90% used (about 1.7T), or btrfs **unallocated < 50 GiB** (check `btrfs filesystem usage /`; btrfs can ENOSPC on metadata well before `df` hits 100%). Metadata is DUP, 6G allocated and 3.9G used, so there is no pressure there now.
- **/boot is the real small disk:** 2.0G with 435M used (22%). Kernel and initramfs growth, or a failed hook that leaves files behind, could fill it and break updates. It becomes tight at 80% (1.6G).

## Never touch

- `~/code/` — all repos, including uncommitted work. Includes `~/code/DeLoDocs` (the **syncthing-shared** vault). Do not delete, move, or `git clean` anything there. Only rebuildable subdirs such as `target/` and `node_modules/` are fair game (see Space map).
- **Syncthing folders** (they replicate to other machines, so deleting here deletes there): `~/code/DeLoDocs`, `~/DevCloud`, `~/quickdrop`, `~/Pictures` (phone screenshots), `~/audio` (transcription inbox). Also leave `~/.config/syncthing` alone, because it holds the device identity and keys.
- `~/code/DeLoDocs/.stversions` (1.6G) is syncthing's trashcan versioning for that folder (cleanoutDays=60). Never `rm` it by hand. Let syncthing expire it, or lower `cleanoutDays` in the syncthing UI.
- **Credentials and identity:** `~/.ssh`, `~/.gnupg`, `~/.local/share/keyrings`, the gnome-keyring files, 1Password (`/opt/1Password`, `~/.config/1Password`), `~/.config/zshyzsh`, and `~/.claude`, `~/.codex`, `~/.hermes`, `~/.kimi-code`, `~/.opencode` (agent config, sessions and memory).
- **Logged-in browser and app profiles.** Deleting them signs Jarad out everywhere:
  - `~/.config/google-chrome/{Default,Profile *}`
  - `~/.config/BraveSoftware`, `~/.config/chromium`, `~/.mozilla`
  - `~/.config/teams-for-linux`, `Slack`, `Claude`, `obsidian`, `~/.local/share/TelegramDesktop`
  - Their cache subdirs are fine (see Playbook). The profiles are not.
- `~/.wine` and `~/wine_apps`: FL Studio prefix and installer. Leave them without an explicit "yes".
- **The LUKS header, `/boot`, `/boot/EFI`, `/boot/limine.conf`, `/.snapshots`, and `/boot/*/limine_history`.** These are the rollback path. Do not hand-delete snapshots. Use `snapper` only.
- `/var/lib/docker` (root-only, unmeasured), `/var/lib/pacman` (package DB), `/var/lib/systemd`, `/etc`.
- `~/.local/state/vinyl/state.json`, and the sock and lock files beside it, while the `vinyld-client` service is running.
- `~/.local/share/vinyl`-style app data and `~/code/vinyl/.venv` (the live dictation client runs from it).
- Personal documents in `~` root (PDFs such as the P&L and the refund request, fonts, `*.tar.gz` extension releases). They are small and are Jarad's. Ask first.

## Space map

btrfs `Used` is the truth at 157G. Summed `du` figures over-count (home 149G + `/usr` 16G + pacman cache 11G + `/opt` 2.8G + journal 3.2G is about 182G), most likely from zstd compression and reflinks. `compsize` is not installed, so this is unverified. Use `du` for ranking, not for reconciliation.

| path | size | class | notes |
|---|---|---|---|
| `~/.cache/uv` | 10.4G | A (partial) | **Hardlink trap.** About 7.8G of this is hardlinked into `~/.local/share/uv/tools/*` (soprano-tts alone). Measured with `du` argument order: cache-only bytes are about 2.6G, the rest is shared with tool venvs. `uv cache clean` frees only the ~2.6G unshared part. |
| `~/.local/share/uv/tools` | 8.2G (shared with cache above) | B | `soprano-tts` 7.1G (torch and CUDA wheels), `gptme` 557M, `kimi-cli` 221M, plus small ones. Reclaim only by `uv tool uninstall <tool>`, which is a decision. |
| `~/.local/share/mise/installs` | 9.7G | B | flutter 3.38.1 2.4G, node (several versions) 2.0G, claude 1.5G, python 1.2G, codex (multiple versions, 746M), zig 375M. Old versions are removable with `mise prune`, and the active ones are not. |
| `~/.cache/.bun` | 3.8G | A | bun install cache. |
| `~/.npm` (`_cacache` 3.7G) | 6.7G | A | npm cache, rebuildable. |
| `~/.cache/yay` | 3.0G | A | AUR build dirs and old `.pkg.tar.zst` (brave-bin 1.1G, teams-for-linux 732M, claude-desktop-bin 551M, chrome 362M, slack 207M). |
| `~/.cache/{google-chrome,chromium,BraveSoftware,electron,mozilla}` | 3.3G, 2.3G, 2.1G, 2.1G, 575M | A | Browser and Electron caches. Quit the browser first. |
| `~/.cache/codex-runtimes` | 1.8G | A | Codex runtime downloads, re-fetched on demand. |
| `~/.cache/{puppeteer,pip,zig,tracker3,go-build}` | 643M, 509M, 478M, 429M, 397M | A | Rebuildable. |
| `~/.config/google-chrome/OptGuideOnDeviceModel` | 4.0G | A | Chrome's on-device Gemini Nano `weights.bin` (dated Jul 11). Chrome re-downloads it. Quit Chrome first. See Gotchas. |
| `~/.config/google-chrome/{Default,Profile 2,4,5}` | 2.1G, 444M, 260M, 474M | C | Live profiles. Do not delete. |
| `~/.config/teams-for-linux/Partitions` | 2.5G | B | Electron session data. Deleting means re-login. |
| `~/.config/BraveSoftware`, `chromium`, `Claude`, `obsidian`, `orca`, `Slack` | 2.5G, 950M, 944M, 890M, 671M, 496M | C/B | Profiles with embedded caches. Only the cache subdirs are class A. Do not blind-delete. |
| `~/code` | 23.9G | mixed | `drumjangler/src-tauri/target` 6.7G (A, rebuildable), `tokamak/src-tauri/target` 1.3G (A), `iMi/trunk-main/target` 654M (A), `openclaw/node_modules` 1.9G (A), `ChoreScore/node_modules` 990M (A), `.venv` dirs (A). `DeLoDocs` 4.0G is C (sync folder, with `.stversions` 1.6G, `.obsidian` 841M, `.codegraph` 96M). The rest is source, so C. |
| `~/.local/share/pnpm` | 2.2G | A | pnpm content store. `pnpm store prune` removes only unreferenced packages. |
| `~/.rustup/toolchains` | 2.8G | B | `stable` 1.4G and `1.95.0` 1.4G. `stable` may duplicate `1.95.0`. Removing one is a decision. |
| `~/.local/share/nvim` | 1.8G | B | `mason` 1.2G (LSP and tool binaries), `lazy` 491M. Rebuildable, but it costs minutes of startup. |
| `~/.local/state/vinyl/traces` | 1.4G | A/B | Dictation trace dirs from Sep 8 on, 45 sessions. One `events.jsonl` is 102M. **Unbounded growth** (see Accumulators). Class B only because it is a debug trail for a live service. |
| `~/.local/share/omarchy.omarchy-upgrade-to-quattro.20260907210818.bak` | 696M | B | Pre-upgrade backup from the Omarchy "quattro" migration on 2026-09-07. A `.bak` that the user, not an agent, should retire. It is the rollback for that migration, and 7 weeks have passed. |
| `~/.local/opt/codex-desktop-linux` | 1.1G | B | Codex desktop app, auto-updated by timer. Old versions may pile up. Not inspected. |
| `~/.local/share/zed`, `pipx`, `claude`, `opencode` | 907M, 654M, 525M, 312M | B | Tool installs and data. Not itemized. |
| `~/Robin Hood ...partial.mp4` | 7.7G | B | A **partial** download (`.chromecast.partial.mp4`), dated Jun 6, and the likeliest single reclaim. Still personal media, so ask. |
| Movies in `~` root: `The Age of Disclosure ... .mkv` 5.5G, `Robin Hood 1991 (h264).mkv` 3.9G, `Robin Hood ... BONE.mkv` 2.1G, `3.Ninjas ...mp4` 1.5G, `Video` 1.5G, `Robin Hood 1991.mp4` 883M | about 15G | B | Personal media, with Robin Hood in three or four copies. Owner decision. |
| `~/Videos` | 3.5G | B | Includes `screenrecording-2026-10-25_22-00-03.mp4`, 3.4G, written within the last 3 days. |
| `~/Downloads` | 3.6G | B | Includes duplicates: `chromium-147...pkg` and `(2)` at 398M each, `firefox-147.0.4` and `(2)` at 289M each, `firefox-143.0.4` at 280M. The `(2)` copies and old browser packages are near-certain deletes after confirmation. |
| `~/quickdrop` | 2.4G | C | Syncthing folder. `builds` 435M, `android` 239M. Deleting here deletes elsewhere. |
| `~/squashfs-root` 536M, `~/orca-app` 536M, `~/orca.AppImage` 195M, `~/orchids.AppImage` 211M, `~/NeoInstaller.pkg` 150M, `~/extension` 466M, `~/webinar_replay.mp4` 153M | about 2.2G | B | Extracted AppImage and installer leftovers in `~`. `squashfs-root` and `orca-app` look like duplicate extractions. Confirm and delete. |
| `~/.wine` 4.7G, `~/wine_apps` 1.0G | 5.7G | B | FL Studio prefix and installer (`flstudio_win64_25.1.6.4997.exe`). |
| `/usr` | 16G | C | The system. Only `pacman` touches it. |
| `/var/cache/pacman/pkg` | 11G (3530 entries, 1754 package files) | A (needs sudo) | `paccache -d -k1` reports 679 candidates / **4.25 GiB**. `paccache -d -u -k0` reports 164 uninstalled-package files / **1.31 GiB**. Default keep is 3, but only 2 versions are retained, so `-k2` finds nothing. There are also 23 root-owned `download-XXXXXX` dirs (stale partial downloads, size unmeasured). |
| `/var/log/journal` | 3.2G | A (needs sudo) | 26 boots. No `journald.conf` overrides, so the built-in cap applies (see Accumulators). |
| `/opt` | 2.8G | C | `microsoft` 646M, `1Password` 571M, `brave-bin` 466M, `google` 437M. Package-managed. |
| `/boot` | 435M of 2.0G | C | Kernels, initramfs, limine. |
| `/var/lib` | 446M | C | `systemd` 324M, `plocate` 66M, `pacman` 55M. `/var/lib/docker` is root-only and unmeasured. |

**Could not measure (no sudo):**
- `/.snapshots` (permission denied) and `snapper -c root list` ("No permissions"). Snapshot count and exclusive size are unknown. btrfs snapshots share extents, so they cost only what has diverged since they were taken. `NUMBER_LIMIT=5` and no timeline snapshots suggests this is small.
- `/var/lib/docker` (root:root 0710, and `delorenj` is not in the `docker` group).
- `/root`, the root-owned `download-*` dirs in the pacman cache, and `/tmp/systemd-private-*` and `/var/tmp/systemd-private-*`.
- `btrfs subvolume list /` ("Operation not permitted"), per-device btrfs detail, and `lsof` (not installed), so deleted-but-open files were not checked.
- Other `.local` and `.config` apps below about 150M, and `/usr` internals.

## Known accumulators

| what regrows | where | observed size | growth driver | bound today | recommended bound |
|---|---|---|---|---|---|
| systemd journal | `/var/log/journal` | 3.2G over 26 boots | **`openclaw-node.service` (user unit) crash-loops.** It fails with `connect ECONNREFUSED 100.66.29.76:18789` (big-chungus gateway), then auto-restarts. It wrote about 3200 journal lines in one hour and about 12.5k in the last 24 h (the top journal producer, equal to `systemd` itself). Also syncthing (8.4k lines/day), tailscaled (5k), and quickshell (4k). | The journald default: `SystemMaxUse` is the lesser of 10% of the filesystem and 4G, so it is capped at about 4G. No `journald.conf` override. | `SystemMaxUse=500M` and `MaxRetentionSec=1month` in `/etc/systemd/journald.conf.d/size.conf` (needs sudo). **Fix the producer:** disable `openclaw-node` while big-chungus's gateway is unreachable, or set `RestartSec`. Also burns CPU (2.1s CPU and 430M peak memory per restart). |
| pacman package cache | `/var/cache/pacman/pkg` (own subvolume `@pkg`) | 11G | Every `pacman -Syu` and AUR build adds new versions. | Retains about 2 versions. `paccache.timer` is **disabled** (paccache and yay installed, no timer). | `systemctl enable --now paccache.timer` (pacman-contrib, weekly, keeps 3), or a `paccache -rk2` run. Needs sudo. |
| yay AUR build cache | `~/.cache/yay` | 3.0G | `yay` leaves sources and every built `.pkg.tar.zst` (brave-bin has 6+ versions). | None | `yay -Sc` periodically, or `yay --clean` after updates. No sudo needed. |
| uv cache plus tools | `~/.cache/uv`, `~/.local/share/uv/tools` | 10.4G cache, 8.2G tools (shared via hardlinks) | `uv tool install` of ML tools (soprano-tts at 7.1G), `uv pip` and `uvx` runs. | None | `uv cache prune` (drops unused entries only). Remove unused tools with `uv tool uninstall`. |
| npm, bun, pnpm, pip, go, zig caches | `~/.npm` 6.7G, `~/.cache/.bun` 3.8G, `~/.local/share/pnpm` 2.2G, `pip` 509M, `go-build` 397M, `zig` 478M | about 14G total | Frequent JS and agent-tool installs (`npx`, `bunx`, `pnpm dlx`). | None | Periodic `npm cache clean --force`, `bun pm cache rm`, `pnpm store prune`. |
| Rust build output | `~/code/*/src-tauri/target`, `~/code/iMi/trunk-main/target` | 8.7G (drumjangler 6.7G) | `cargo` and `tauri build` or `tauri dev`. | None. `rustup` toolchains also pile up at 2.8G. | `cargo clean` per project when idle. Install `cargo-sweep` for age-based cleanup. |
| node_modules and .venv | `~/code/*` | about 6G (openclaw 1.9G, ChoreScore 990M, HeyMa-Satellite venv 790M, ...) | Every JS or Python project. | None | Rebuild-on-demand. Delete in stale repos. |
| Browser and Electron caches | `~/.cache/{google-chrome,chromium,BraveSoftware,electron}` | about 10G | Chrome, Chromium, Brave, Electron apps (Teams, Slack, Claude, Obsidian). | Browser-internal size limits only. | Occasional clear. Quit the browser first. |
| Chrome Gemini Nano model | `~/.config/google-chrome/OptGuideOnDeviceModel` | 4.0G (one version, 2025.8.8.1141) | Chrome auto-downloads it, and each model update could leave a second copy. | None | Disable the on-device model (`chrome://flags` "Optimization Guide On Device Model" off), then delete the dir. |
| Vinyl traces | `~/.local/state/vinyl/traces` | 1.4G (45 dirs, since Sep 8) | `vinyld-client` writes `events.jsonl` per dictation session. One is 102M. | **None** | Prune dirs older than 14 days: `find ~/.local/state/vinyl/traces -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +`. Better, add a retention setting in `~/code/vinyl`. |
| Syncthing versions | `~/code/DeLoDocs/.stversions` | 1.6G | Trashcan versioning of the DeLoDocs sync folder, for example a 106M `gateway-exit-diag.log` copy. | `cleanoutDays=60` on trashcan folders. Some folders have no versioning. | Fine. Check that `DeLoDocs/agents/hermes/pm/runtime/logs` is excluded from sync (it holds a 106M log). |
| Screen recordings | `~/Videos` | 3.5G (one 3.4G file written Oct 25) | Manual or `screenrecording-*` hotkey captures. | None | Move off-box or delete after use. |
| Downloads and partials | `~/Downloads`, `~` root, `~/quickdrop` | about 3.6G plus 15G loose media plus a 7.7G partial | Manual downloads, Chromecast partials, repeated `(2)` copies. | None | Owner triage (see Playbook B). |
| Core dumps | `/var/lib/systemd/coredump` | small now (electron 310M, remmina 13M, in the 3 most recent) | A crash (electron on Oct 11, remmina on Oct 18). | `systemd-tmpfiles-clean.timer` ages them out (default 3 days for the dir). | Fine. |
| btrfs snapshots | `/.snapshots` | unknown (no sudo) | snapper (number cleanup, limit 5) plus `limine-snapper-sync`. | `snapper-cleanup.timer`, `NUMBER_LIMIT=5`, no timeline snapshots. | Fine. Just make sure `snapper -c root list` stays short. |
| Docker | `/var/lib/docker` | unknown (root-only) | Not in use. Daemon is off. `daemon.json` caps json-file logs at `10m x 5`. | Log driver limits only. | If docker is ever started: `docker system prune`. Check `/var/lib/docker` size first, with sudo. |
| `/tmp` | tmpfs, 16G | 216M | Anything. | RAM-backed, vanishes on reboot, so there is no disk impact. | n/a |

## Targeted playbook

Everything is a rebuildable cache unless marked. Nothing here has been run. **No sudo available to agents**, so steps marked `[sudo]` go to Jarad. Run `df -h /` before and after each step, but note that btrfs frees space lazily, so it can lag a few seconds.

### Tier A, no sudo (safe without asking)

1. **Stop the journal producer first (stops regrowth).** This is a decision-lite action, because the service is already failing continuously. Reversible with `enable`.
   ```bash
   systemctl --user disable --now openclaw-node.service   # restart loop against big-chungus gateway :18789
   ```
   Yield: no direct bytes, but it stops about 3200 lines/h of journal growth. Re-enable when the big-chungus gateway is reachable.
2. **yay cache.** Yield about 3.0G. No precondition.
   ```bash
   yay -Sc --noconfirm      # or: rm -rf ~/.cache/yay/*/*.pkg.tar.zst ~/.cache/yay/*/src
   ```
3. **npm cache.** Yield about 3.7G, up to 6.7G including logs.
   ```bash
   npm cache clean --force
   ```
4. **bun cache.** Yield about 3.8G. No bun install may be running.
   ```bash
   bun pm cache rm
   ```
5. **pnpm store.** Yield up to 2.2G. It removes only unreferenced packages.
   ```bash
   pnpm store prune
   ```
6. **uv cache.** Expected yield only about 2.6G, because the rest is hardlinked into tool venvs (see Gotchas). Do not expect 10G.
   ```bash
   uv cache prune          # unused entries only; 'uv cache clean' frees about the same
   ```
7. **Rust build output** in repos not being built right now. Precondition: no `cargo` or `tauri` process (`pgrep -a 'cargo|tauri|rustc'`).
   ```bash
   cd ~/code/drumjangler/src-tauri && cargo clean          # about 6.7G
   cd ~/code/tokamak/src-tauri && cargo clean              # about 1.3G
   cd ~/code/iMi/trunk-main && cargo clean                 # about 654M
   ```
   Yield about 8.7G. The next build is slow (full recompile). Skip `tokamak` if Jarad is iterating on the desk widget, since it is the deploy target.
8. **Old mise versions.** `mise prune` removes tools no longer in any config.
   ```bash
   mise prune --dry-run && mise prune -y
   ```
   Yield: some of the 9.7G, mostly old node, codex and python versions.
9. **Browser caches.** Precondition: Chrome, Chromium, Brave and Electron apps closed (otherwise they re-grow and may lock files).
   ```bash
   rm -rf ~/.cache/google-chrome ~/.cache/chromium ~/.cache/BraveSoftware ~/.cache/electron ~/.cache/mozilla
   ```
   Yield about 10G. Never touch `~/.config/*` profiles in this step.
10. **Misc caches.** Yield about 3G.
    ```bash
    rm -rf ~/.cache/puppeteer ~/.cache/codex-runtimes ~/.cache/tracker3 ~/.cache/zig ~/.cache/pip
    go clean -cache
    ```
11. **Chrome on-device model.** Precondition: Chrome fully quit. Yield 4.0G. It may be re-downloaded unless the flag is off (see Gotchas).
    ```bash
    rm -rf ~/.config/google-chrome/OptGuideOnDeviceModel
    ```
12. **Vinyl traces older than 14 days.** Precondition: `vinyld-client` may be running, so only prune old session dirs. Yield up to 1.4G.
    ```bash
    find ~/.local/state/vinyl/traces -maxdepth 1 -mindepth 1 -type d -mtime +14 -exec rm -rf {} +
    ```

**Tier A total, no sudo:** about 40G in aggregate if everything runs (yay 3, npm 3.7, bun 3.8, pnpm up to 2.2, uv 2.6, Rust targets 8.7, browser caches 10, misc 3, Chrome model 4, vinyl 1.4). That is theoretical, since the machine is at 9%.

### Tier A, sudo needed (hand these to Jarad)

```bash
sudo paccache -rk1                                   # 4.25 GiB (679 files); -rk2 finds nothing
sudo paccache -ruk0                                  # also drop uninstalled-package files: 1.31 GiB
sudo rm -rf /var/cache/pacman/pkg/download-*         # stale partial downloads (size unmeasured), only if no pacman is running
sudo journalctl --vacuum-size=500M                   # frees about 2.7G of the 3.2G journal
sudo systemctl enable --now paccache.timer           # closes the "no retention" gap permanently
```
For a permanent journal cap, `printf '[Journal]\nSystemMaxUse=500M\nMaxRetentionSec=1month\n' | sudo tee /etc/systemd/journald.conf.d/size.conf` and then `sudo systemctl restart systemd-journald`.

### Tier B, decisions to put to Jarad

- **`~/Robin Hood ... chromecast.partial.mp4` (7.7G)** is an incomplete download dated Jun 6. Delete it?
- **Movie copies in `~` root (about 15G):** Robin Hood exists as `.mkv` (3.9G), `BONE.mkv` (2.1G) and `.mp4` (883M), plus the `partial`. Keep one? Also `The Age of Disclosure` 5.5G and `3.Ninjas` 1.5G. Move to external storage, or delete?
- **`~/Videos/screenrecording-2026-10-25_22-00-03.mp4` (3.4G).** Still needed? It is only 3 days old.
- **`soprano-tts` uv tool (7.1G).** Is it used by `voxxy` or `vocalinux`? If not, `uv tool uninstall soprano-tts` and then `uv cache prune`. Together they free about 7.1G of the 10.4G uv footprint.
- **`~/.local/share/omarchy.omarchy-upgrade-to-quattro.20260907210818.bak` (696M).** The quattro migration was 7 weeks ago and the system has rebooted several times. Retire the backup?
- **`~/Downloads` duplicates (about 1.7G):** the `chromium-147... (2)`, `firefox-147.0.4 (2)` and `firefox-143.0.4` packages. Delete?
- **AppImage and installer leftovers in `~` (about 2.2G):** `squashfs-root`, `orca-app`, `orca.AppImage`, `orchids.AppImage`, `NeoInstaller.pkg`, `extension`, `webinar_replay.mp4`. Which are still used?
- **`~/.rustup/toolchains`** has `stable` and `1.95.0`, 1.4G each. Are both needed? (`rustup toolchain uninstall 1.95.0`.)
- **`~/.config/teams-for-linux/Partitions` (2.5G).** Accept a re-login to Teams?
- **`~/.local/share/uv/tools/gptme` (557M)** and other uv tools. Still in use?
- **Whether to keep snapper boot-snapshots at all (`NUMBER_LIMIT=5`).** Fine as is. Surfaces only if `snapper list` (with sudo) shows large exclusive sizes.

## Installed automation

- **System timers:** `snapper-cleanup.timer` (hourly, number-cleanup limit 5), `systemd-tmpfiles-clean.timer` (daily), `man-db`, `plocate-updatedb`, `shadow`, `archlinux-keyring-wkd-sync`. None of these touch pacman caches, user caches or journals beyond defaults.
- **User timers:** `codex-desktop-update.timer` (weekly, Sun 05:00), `syncthing-monitor.timer`. Nothing for cleanup.
- **Syncthing:** trashcan versioning with `cleanoutDays=60` on two folders. Several folders have no versioning stanza.
- **journald:** built-in default cap (about 4G), no override.
- **logrotate:** installed, with configs for `bootlog`, `cups`, `postgresql`, `snapper`. No timer was checked (`systemctl is-enabled logrotate.timer` returned "not-found"), so logrotate is **not scheduled**. It does not matter much, because services log to journald.
- **docker:** `daemon.json` limits json-file logs to 10m x 5, but docker is not running.
- **cron:** not installed.
- **Gaps:**
  - No `paccache.timer`, though `paccache` and `yay` are installed.
  - No journald size cap tighter than the 4G default.
  - No retention on the vinyl traces.
  - No cleanup for any dev cache (npm, bun, pnpm, uv, cargo, mise, yay).
  - No age-based `cargo` sweep.
  - No disk-space alerting. `infra-doctor` and ntfy live on big-chungus and do not cover this host.

## Gotchas

- **No sudo for agents.** `sudo -n` fails. Do not try to work around it. Tier A has a large no-sudo yield, and the sudo items are a short list for Jarad.
- **uv hardlink trap.** `du -sh ~/.cache/uv ~/.local/share/uv` in one command makes `du` count shared hardlinks once, so the first-listed path "wins" and the other looks small. Measured both ways: `.cache/uv` alone is 10.4G, and it is 2.6G when listed after `.local/share/uv`. Deleting the cache will free far less than 10G, and deleting only the tool venv frees nothing while the cache keeps the bytes. The same applies to the pnpm store versus `node_modules`. **Always size a path alone with `du -sh <path>` before promising a yield.**
- **Compressed, reflinked btrfs.** Summed `du` exceeds `btrfs filesystem usage`. Do not chase the gap. `compsize` is not installed, so the effect is unmeasured.
- **Free space is pool-wide.** `/`, `/home`, `/var/log` and `/var/cache/pacman/pkg` are subvolumes of one filesystem. Cleaning any of them frees space for all of them, and `df` shows identical numbers on each.
- **btrfs ENOSPC arrives before `df` says full.** Check `btrfs filesystem usage /` for unallocated space and metadata. Deleting files does not shrink allocated chunks, so only `btrfs balance` returns them (needs root).
- **Deleting snapshots or files can free less than expected** when extents are shared with a snapshot. Free space moves only when the last reference goes.
- **`/boot` is a separate 2G FAT partition.** A full `/boot` breaks kernel and initramfs updates. Check it with `df -h /boot` after big package updates.
- **Chrome's `OptGuideOnDeviceModel` looks like config but is a re-downloadable model** (Gemini Nano, 4.0G). It sits in `~/.config`, so a generic sweep that skips `~/.config` misses it. Chrome will fetch it again unless the flag is disabled.
- **Browser profiles hide huge caches inside `~/.config`** (`Default/Service Worker`, `Code Cache`, `Cache`). Only the dedicated `~/.cache/*` dirs are safe to remove blind.
- **Syncthing folders look like ordinary directories** (`~/code/DeLoDocs`, `~/quickdrop`, `~/DevCloud`, `~/Pictures`, `~/audio`). Deleting a file there propagates to other machines. `DeLoDocs/.stversions` is syncthing's own recycle bin.
- **`openclaw-node` is in `auto-restart` state forever** while big-chungus's gateway (`100.66.29.76:18789`) is down. Pane-level `systemctl --user status` shows `activating`, not `failed`, so it looks alive. Each restart uses about 430M of memory at peak.
- **Docker looks present but is not used.** The daemon is inactive and the socket is active, so the first `docker` call may start it. `delorenj` is not in the `docker` group, so `docker ps` returns "permission denied". Use `sudo docker`, not `rm`, if you ever clean it.
- **`lsof` is not installed**, so deleted-but-open files can't be checked with it. Use `ls -l /proc/*/fd 2>/dev/null | grep deleted` as a fallback.
- **It is a laptop.** The user is at the keyboard on tty1 (Hyprland). Killing browsers or Electron apps for cache cleanup disrupts a live desktop session. Ask first, or run when the session is idle.
- **Survey script:** `scripts/survey.sh` runs fine here over `ssh tiny-chungus 'bash -s'`. It marks root-only probes as skipped, and its "Written in the last 48h >=200M" section came back empty even though a 3.4G screen recording (Oct 25) exists, which is outside 48h, so that is correct, not a bug.

## Run log
- 2026-10-28 — initial profile (read-only survey). Free: 1.7T of 1.9T (157G used, 9%).
