# carries-macbook-air — disk profile

**Last verified:** 2026-10-28 (initial survey) — if a run contradicts this file, the run wins: fix the file.

## Identity

- **OS / hardware:** macOS 26.6.2 (25G83), MacBook Air `Mac15,13` (Apple M3, 24 GB RAM). Xcode 27.1 at `/Applications/Xcode.app`.
- **Names:** tailnet `carries-macbook-air`, hostname `mommymac.local`, display name "Carrie's MacBook Air". The user (delorenj) calls it "my macbook".
- **Disk layout:** one internal 500 GB SSD, one APFS container `disk3` of 494.4 GB (460 GiB) shared by all volumes:

  | Volume | Used | Notes |
  |---|---|---|
  | Data (`disk3s5`, mounted `/System/Volumes/Data`) | 402 GiB | everything that is ours; this is what `df` shows as "Used" |
  | System (`disk3s1`, sealed, snapshot `com.apple.os.update-...`) | 15.5 GiB | read-only, untouchable |
  | Preboot (`disk3s2`) | 15.3 GiB | boot assets of the staged macOS update; large because an update is prepared (`os.update-MSUPrepareUpdate` snapshot) |
  | Recovery (`disk3s3`) | 2.4 GiB | untouchable |
  | VM (`disk3s6`) | 8.0 GiB | swap: 8 x 1 GiB `swapfile*`, 7.0 GiB in use. Memory pressure, not a leak |
  | free (container) | 16 GiB | all volumes share it; `df` shows the same 16 GiB on every volume |

  A second APFS container, `disk5` (18.6 GB "iOS 27.0 Simulator"), is a mounted disk image. It is virtual: it costs 7.5 GiB, as the backing file `/System/Library/AssetsV2/com_apple_MobileAsset_iOSSimulatorRuntime/<id>.asset/AssetData/Restore/043-70362-657.dmg`. Do not count it twice.
- **Role:** the **Mac build host of mobile-deploy-hub** (iOS archive/export/sign, handoff to the iPad `iPad14,5` over USB/CoreDevice). It runs five GitHub Actions runners as launchd services under `~/actions-runner` (`tower-of-lost-things` = `carries-macbook-air`, `gib`, `gruvato`, `navi`, `james-brennan`). It is also a dev Mac: Android Studio, Flutter, Rust/Tauri (gruvato), pnpm, mise, Claude desktop (Cowork VM), Hermes, Codex, Chrome, ego lite (the authenticated browser that agents drive), plus music/video apps.
- **Users:** `delorenj` (admin, the only account an agent can read) and `carriedelorenzo` (Carrie, the user's wife). Carrie's home is mode 700: `du` returns 12 KB and I cannot read it. Her share is estimated by subtraction below.
- **Reach:** from big-chungus, `ssh -o BatchMode=yes hub-mac '<cmd>'` (Host `hub-mac` in `~/.ssh/config`, `ProxyCommand tailscale nc carries-macbook-air %p`, ConnectTimeout 20). Slow: batch commands, give `du` walks minutes. Remote login shell is **zsh**: an unmatched glob is a hard error (`no matches found`), so quote or use `find`.
- **sudo:** NO. `sudo -n` asks for a password. Everything below is user-level. Root-only things (APFS snapshots, `/Library` system caches, Carrie's home, other users' temp) cannot be touched or even measured.

## Baseline

- **Now (2026-10-28):** 460 GiB container, 402 GiB used on Data, **16 GiB free (97%)**.
- **mobile-deploy-hub refuses to run below 15 GiB free** (`tools/ci/devices.json`: `mac.min_free_gib: 15`). At 16 GiB this Mac is one archive away from blocking every iOS deploy for gib, gruvato, navi, tower and james-brennan. That is the practical definition of emergency here.
- **Healthy:** >= 60 GiB free (13%). **Tight:** < 40 GiB. **Emergency:** < 20 GiB. At < 15 GiB deploys hard-stop, macOS cannot stage updates (needs ~15 GiB), and swap cannot grow past its 8 GiB.
- A single iOS build cycle (archive + export + handoff) adds 0.5 to 2.5 GiB under `~/.cache/<app>/ios/<run>`; a Rust/Tauri release adds 2.4 GiB under `target/release`.

## Never touch

- **`/Users/carriedelorenzo`** and anything of Carrie's. Do not `sudo`, do not look.
- **Live hub state:** `~/Library/Caches/mobile-deploy-hub/handoff/` (in-flight builds, written today 04:25-04:32) and `~/Library/Caches/mobile-deploy-hub/outbox/` (the newest two IPAs per app, 0.2 GiB, which the iPad catch-up installs from). `handoff-cache/` is the hub's own cache, pruned by the hub at 3 days: leave it to the hub.
- **Runner identity and binaries:** everything in `~/actions-runner/` and `~/actions-runner/<name>/` except `_work/*` and `_diag/*`. `.runner`, `.credentials*`, `bin/`, `externals/`, `*.sh`, and `~/Library/LaunchAgents/actions.runner.*.plist` deleted means re-registering the runner with GitHub. Never `launchctl bootout` a runner while a job is active.
- **Signing material:** `~/Library/Keychains`, `~/Library/Developer/Xcode/UserData/Provisioning Profiles`, `~/Library/MobileDevice/Provisioning Profiles` (the hub enforces `profile_min_days: 30`), `~/.android/debug.keystore`, `~/.android/adbkey*`.
- **Live app data:** `~/Library/Application Support/sh.delo.gruvato` (4.5 GiB, the live Gruvato library; `gruvato-backups/` are its backups), Chrome profiles (`Application Support/Google/Chrome/{Default,Profile *}`, logged-in), ego lite profiles (`Application Support/Citro Labs/ego lite/Profile *`, authenticated agent sessions), Google Drive `DriveFS` (may hold unsynced files), `~/Library/Messages` (chat.db), Photos library.
- **Personal recordings:** `~/Library/Group Containers/group.com.apple.VoiceMemos.shared` (5.8 GiB, 472 recordings). Class C: offer to export, never suggest deleting.
- **Toolchains that look like caches:**
  - `~/.local/share/mise/installs` AND `~/.local/share/mise/http-tarballs` (3.7 GiB): `installs/flutter/3.38.1` is a **symlink into `http-tarballs/56f2fa5f...`**, so deleting the "cache" deletes Flutter. **Never `mise prune`** (it removes interpreters tools depend on).
  - `~/.hermes` (3.4 GiB live Hermes agent install), `~/.claude`, `~/.codex` (config and sessions), `~/.ssh`, `~/.config`.
- **Repos with uncommitted work in `~/code`** (not rebuildable): `Thermite` (68 dirty files), `automatic-ai-internal` (12), `skillex` (5), `tokamak` (5), `ssbnk` (4), `wean` (4), `intelliforia` (3), `intelliforia-mobile` (3, on a feature branch), `voxxy` (3), `PoopToTheMoon` (2), `green-in-between` (1). Only the build output inside them (`target/`, `node_modules/`) is deletable.
- **System-managed, unremovable without root:** the three APFS `com.apple.os.update-*` snapshots, Preboot, Recovery, the VM volume. See Gotchas.

## Space map

Whole-disk accounting (GiB). Data volume = 402.

| Where | GiB | Notes |
|---|---|---|
| `/Users/delorenj` (home) | 258.0 | detail below |
| `/Applications` | 59.7 | detail below |
| `/Library` | 20.2 | Arturia 8.7, Audio 4.7, Application Support 2.6, Developer 2.2 |
| `/System/Library/AssetsV2` | 14.5 | simulator runtime 7.5, SFR/Mac software update 2.6 (staged update), Siri UAF 1.3, LinguisticData 0.9, MetalToolchain 0.7 |
| `/opt/homebrew` | 7.7 | Cellar 5.0, Caskroom 1.1 |
| `/private/var` on Data | 9.6 | `folders` 5.4, `db` 3.7 (`db/diagnostics` 2.3), `tmp` 0.5 |
| `/usr/local` | 0.5 | |
| **identified** | **370.5** | |
| **not attributable (no sudo)** | **~31** | **Carrie's account**, plus root-only paths. This is a *lower bound* for her share: `du` double-counts APFS clones and hardlinks (pnpm, uv, cargo, `cp -c` handoff trees), which shrinks the gap. Do not call it exact |

Home breakdown (class A = rebuildable, delete without asking; B = owner decision; C = never):

| Path | GiB | Class | Notes |
|---|---|---|---|
| `~/.cache/tower-of-lost-things/ios/<run>` | 10.9 | A | 46 per-run dirs (xcarchive, Godot engine/templates copy, export, logs), all >= 19 days old. Writer: tower repo `tools/ios.mjs:1287`. Never pruned |
| `~/.cache/gib-ios17-delivery` | 5.7 | A | agent-made clone of green-in-between (branch `build-ios17-delivery`, clean, commits reachable from `origin/main`). Holds delivered preview IPAs |
| `~/.cache/gib-ios-preview-17` | 2.9 | A | same, branch `build-ios-preview-17`, clean, "ahead 3" only of a local `.bundle`, commits reachable from `origin/main` |
| `~/.cache/gib-native` | 1.0 | B | `bake/` is a content-addressed Blender/Cycles bake: 15-30 min to rebuild; `godot/`, `ios-hub/` toolchain |
| `~/.cache/gib-*.bundle` (8 files) | 0.3 | A | git bundles seeding the clones above |
| `~/.cache/codex-runtimes` | 1.6 | B | Codex app runtimes |
| `~/.cache/uv` + `~/.local/share/uv` | 1.3 + 1.1 | A | `uv cache prune` |
| `~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle` | 3.6 | A | Codex app's updater download staging |
| `~/Library/Caches/mobile-deploy-hub` | 3.1 | C | handoff 2.0, handoff-cache 0.9, outbox 0.2. Hub-managed |
| `~/Library/Caches/Citro Labs/ego lite` | 2.1 | B | browser cache of the agent browser; cache only, but sits beside live profiles |
| `~/Library/Caches/CocoaPods` | 0.8 | A | |
| `~/Library/Application Support/Claude/vm_bundles` | 10.1 | B | `claudevm.bundle`, the Claude Cowork VM (rootfs etc.), in use while Claude.app runs. Re-downloads ~10 GiB on next Cowork use |
| `~/Library/Application Support/Google/Chrome/OptGuideOnDeviceModel` | 4.0 | A | Chrome's on-device Gemini Nano model; re-downloads only if the feature is used |
| `~/Library/Application Support/Google/Chrome` profiles | 3.3 | C | logged-in browser profiles |
| `~/Library/Application Support/Google/DriveFS` | 1.6 | C | Drive sync cache, may hold unsynced files |
| `~/Library/Application Support/Neo/component_crx_cache` | 2.7 | A | extension component cache |
| `~/Library/Application Support/Neo/LocalLLM` | 2.6 | B | on-device model |
| `~/Library/Application Support/sh.delo.gruvato` | 4.5 | C | live Gruvato data |
| `~/Library/Application Support/Citro Labs/ego lite` | 3.5 | C | authenticated agent browser profiles |
| `~/Library/Application Support/com.docker.install/in_progress` | 2.1 | A | half-finished Docker Desktop install from Sep 4; Docker is not installed (`/Applications` has no Docker) |
| `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw` | 1.6 | B | sparse VM disk of the uninstalled Docker. `ls` says 460 GiB apparent, 1.6 GiB real. Any volumes inside are lost with it |
| `~/Library/Developer/Xcode/iOS DeviceSupport/iPad14,5 27.0 (24A437)` | 6.4 | B | symbols for the one device the hub deploys to. Regenerates on next connect (~10 min, iPad plugged in and trusted) |
| `~/Library/Developer/Xcode/DerivedData` | 2.1 | A | |
| `~/Library/Developer/Xcode/CodingAssistant` | 1.4 | B | Xcode predictive-completion model assets |
| `~/Library/Developer/CoreSimulator/Devices/12178C22-...` | 3.6 | A | iPhone 18 Pro simulator data. The other 10 devices are 17 MB each. All Shutdown, none "unavailable", no Archives dir |
| `~/Library/Android/sdk/system-images` | 2.9 | B | Android emulator images; the hub installs Android builds to a real S26 (`devices.json`), not an emulator |
| `~/.android/avd` (`Pixel_10_Pro.avd`) | 4.6 | B | the only AVD |
| `~/.gradle/caches` | 4.1 | A | `9.3.1` 1.2, `modules-2` 1.0, `8.13` 0.9. Re-downloads on next Gradle build |
| `~/.rustup/toolchains` | 5.5 | mixed | `stable` = rustc 1.95.0 (default, 2.2), `1.98.0` (2.1), `1.95.0` (1.3, **same rustc as stable**: duplicate) |
| `~/.local/share/mise/installs` | 4.5 | C | node 1.5, python 0.6, dart 0.6, heroku 0.5... |
| `~/.local/share/mise/http-tarballs` | 3.7 | C | Flutter 3.38.1 lives here (symlink). Never delete |
| `~/.local/share/pnpm/store/v10` | 2.9 | A | stale: pnpm 11 uses `~/Library/pnpm/store/v11` (`pnpm store path`) |
| `~/Library/pnpm/store/v11` | 2.1 | A | active store, `pnpm store prune` only trims it |
| `~/.local/share/pnpm/store/v11` | 0.6 | B | a second v11 store; check `pnpm store path` per project before removing |
| `~/.local/share/pnpm/global` | 1.0 | B | global pnpm installs |
| `~/.local/share/nvim` (`mason` 2.0, `lazy` 1.0) | 3.1 | B | editor tooling |
| `~/.local/share/tonny/releases` | 1.1 | B | |
| `~/.local/share/claude/versions` | 1.0 | B | 4 Claude Code versions (2.1.307 to 2.1.312); the newest is the one in use |
| `~/.local/bin/agy.*.old` | 0.2 | A | old binary |
| `~/code/gruvato/src-tauri/target` | 4.5 | A | `cargo clean`: release 2.4 + debug 2.3. The repo itself is clean and pushed |
| `~/code` rest | 9.2 | C/B | green-in-between 2.0 (`native` 1.5), tokamak 1.3, intelliforia-mobile 1.1, DeLoDocs 1.0, ... dirty trees listed in Never touch |
| `~/gruvato-backups` | 10.9 | B | 7 timestamped copies of `sh.delo.gruvato` (1.4 GiB each, 2026-10-13..15) plus an app. Pre-migration safety copies from the 6.1 to 6.7 work |
| `~/gruvato-67` | 5.5 | A / B | `repo/` 3.9 = scratch clone at detached `8fbcccf` (clean, contained in `origin/main`): A. `data/` 1.2 = test instance + tools: B |
| `~/gruvato-checks/repo` | 1.7 | A | same detached `8fbcccf`, clean |
| `~/gruvato-spike` | 1.0 | B | Sep 30 separator experiment outputs + `.venv`. Not a git repo |
| `~/actions-runner/<r>/_work` | 7.9 | A | `gruvato` 4.0, `gib` 1.3, `navi` 1.2, `james-brennan` 1.2, shared `_work/tower-of-lost-things` 0.24. Recreated by the runner. Only while no job runs |
| `~/actions-runner` rest (`externals` x5, `bin` x5, `_diag`) | 2.5 | C | runner binaries |
| `~/Library/Logs/cleanup_screenshots_error.log` + `.log` | 1.9 | A | **crash-loop log, growing right now**: see accumulators |
| `~/.openclaw/logs/node.err.log` | 0.8 | A | the whole `~/.openclaw` is this one log; second crash-loop log, see accumulators |
| `~/Library/Logs` rest | 0.3 | A | |
| `~/Library/Caches/ollama/updates` | 0.2 | A | downloaded `Ollama-darwin.zip` |
| `~/docker/stacks/media/video/*.avi.!qB` | 1.2 | B | an unfinished qBittorrent download from 2025-06 inside the `DeLoContainers` clone |
| `~/Downloads` | 3.5 | A / B | `flstudio_mac_26.1.7.5421.dmg` 1.1 (FL Studio is installed), `dsh-latest-macos-arm64.dmg` 0.25, APKs 0.35: A. Videos (~0.6): B |
| `~/Desktop` | 1.4 | A / B | `Godot.app`, `Godot 2.app`, `Godot 3.app` are three identical 337 MiB copies (A: keep one), `Claude.dmg` 0.25 and `Godot_v4.7.2...zip` 0.16 (A) |
| `~/.Trash` | 0.8 | A | `agents` 0.74 |
| `~/size_tree.json` | 0.3 | A | a stray `gdu`/du tree dump from Apr 30 |
| `~/thegrinch.mkv` | 2.9 | B | loose video, Nov 2025 |
| `~/AI Dev Onboarding-...Meeting Recording.mp4`, `~/2025-06-04 11-03-02.mkv`, `~/AIDevEnvBootstrappingTalk.mkv` | 0.8 + 0.4 + 0.4 | B | meeting recordings |
| `~/audio` (`2026` 1.9, `2023` 0.35) | 2.3 | B | |
| `~/quickdrop` | 1.9 | B | phone hand-off folder (APKs, `verity.m4b` 0.22 which is duplicated in `~/Music`) |
| `~/music-presets`, `~/Presets`, `~/Splice` | 1.5, 1.5, 0.5 | B | music production |
| `~/flutter-3.38.1` | 1.8 | B | a second Flutter 3.38.1 (mise has its own) |
| `~/.hermes` | 3.4 | C | live agent |
| `~/.codex` | 2.3 | C/B | `packages` 0.8, `plugins` 0.8 |
| `~/docker` | 0.9 | B | `DeLoContainers` clone, 352 commits behind, has an untracked `chase.tar.gz` |
| `~/Library/Roblox` + `RobloxStudio.app` | 1.4 + 0.8 | B | kids' |
| `~/Library/Containers`: DuckDuckGo 2.0, CoreDevice 1.5, MobileSMS 1.1, Teams 1.0, mediaanalysisd 0.6 | 8.5 | B/C | Messages is C |
| `~/Library/Group Containers/group.com.apple.VoiceMemos.shared` | 5.8 | C | see Never touch |
| long tail | ~17 | mixed | ~300 entries under 0.9 each (`.npm` 0.8, `.antigravity-ide` 0.8, `.openclaw` 0.8, `if-ext` 0.8, `.cursor` 0.7, `.cargo/registry` 0.6, `.pulumi` 0.6...) |

`/Applications` (59.7): Xcode 3.9, iMovie 3.7, Affinity 3.6, Android Studio 3.0, CapCut 2.6, `Studio 2.0` 2.3, FL Studio 2.3, Chrome 2.1, ChatGPT 1.7, Play-Doh 1.2, Teams 1.1, GarageBand 1.0, stitch 1.0, then ~100 apps under 1 GiB. Several are probably Carrie's or the kids' (iMovie, CapCut, Affinity, Play-Doh, GarageBand, Roblox Studio): **class B, ask whose they are**. `/Library/Arturia` (8.7), `/Library/Audio` (4.7, GarageBand/Logic loops) are the same story.

**Could not measure:** Carrie's home and root-only paths (no sudo), APFS snapshot-held blocks (`tmutil` lists three `os.update` snapshots, size not queryable without root), Time Machine (no destinations configured), iCloud-evicted files, and the exact real yield of hardlink/clone-heavy caches (pnpm, uv, cargo: `du` shows full size in both places).

## Known accumulators

| What regrows | Where | Observed | Growth driver | Bound today | Recommended bound |
|---|---|---|---|---|---|
| Crash-loop stderr/stdout | `~/Library/Logs/cleanup_screenshots_error.log`, `.log` | 1.75 + 0.18 GiB; +36 KB/min = ~52 MB/day (~34 days of loop) | launchd agent `com.delorenj.cleanup_screenshots` (`KeepAlive`, `set -x`) restarts every ~10 s because `TARGET_DIR=~/gd/screenshots` and `~/gd -> Google Drive/My Drive` is **dangling** (Drive for Desktop now mounts under `~/Library/CloudStorage/GoogleDrive-*`) | none | fix the target path, drop `set -x`, `exit 0` if the dir is missing instead of restarting, add `ThrottleInterval 60`; newsyslog or truncate the logs |
| Reconnect-loop stderr | `~/.openclaw/logs/node.err.log` | 0.8 GiB since 2026-03-27 (~4 MB/day, ~80 B/s) | launchd agent `ai.openclaw.node` (`KeepAlive`, `ThrottleInterval 1`): "node host gateway connect failed: Unexpected server response: 502" then "closed (1006)", forever, because its gateway answers 502 | none | fix or unload the agent if the OpenClaw gateway is gone; otherwise newsyslog-rotate the file |
| iOS build run dirs | `~/.cache/tower-of-lost-things/ios/<run>` | 10.9 GiB, 46 dirs, 0.2 to 2.5 GiB each | tower repo `tools/ios.mjs` (`join(home, '.cache/tower-of-lost-things/ios', runId)`), run by the tower runner and by hand | none (the hub prunes only its own `handoff-cache` at 3 days and keeps 2 IPAs in `outbox`) | prune runs older than 7 days at the end of `ios.mjs` / hub deliver (repo fix, not machine fix) |
| Runner workspaces | `~/actions-runner/*/_work` | 7.9 GiB | the 5 runners; `gruvato` keeps a Rust `target` | none | a nightly `find _work -maxdepth 2 -mtime +7` sweep when no `Runner.Worker` runs, or `--ephemeral` runners |
| Rust build output | `~/code/gruvato/src-tauri/target` (also `gruvato-67/repo`, `gruvato-checks/repo`, runner `_work`) | 4.5 + 3.6 + 1.5 GiB | `cargo`/`tauri build` | none | `cargo sweep --time 14` or `cargo clean` after each release |
| Agent-made scratch clones | `~/.cache/gib-*`, `~/gruvato-67`, `~/gruvato-checks`, `~/gruvato-spike` | 8.6 + 5.5 + 1.7 + 1.0 GiB | agents doing delivery/release work and never cleaning up | none | agents delete their scratch clone when the delivery is verified; flag it in the PR |
| App-data backups | `~/gruvato-backups/<date>/` | 10.9 GiB, 7 copies | manual pre-migration backups before gruvato 6.x work | none | keep newest 2, delete older when the migration is verified |
| Claude Cowork VM | `~/Library/Application Support/Claude/vm_bundles` | 10.1 GiB | Claude.app (re-downloads after removal) | none | decide whether Cowork is used on this Mac |
| Codex updater staging | `~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle` | 3.6 GiB | Codex.app Sparkle updates | none | periodic delete |
| Chrome on-device model | `.../Google/Chrome/OptGuideOnDeviceModel` | 4.0 GiB | Chrome | none | `chrome://flags` "optimization guide on device model" disabled |
| Gradle / pnpm / uv / CocoaPods / Cargo / Xcode caches | `~/.gradle/caches`, `~/.local/share/pnpm/store`, `~/Library/pnpm`, `~/.cache/uv`, `~/Library/Caches/CocoaPods`, `~/Library/Developer/Xcode/DerivedData` | 4.1 + 5.6 + 1.3 + 0.8 + 2.1 GiB | normal tool use | none | monthly tool-native prune (playbook A) |
| Per-device Xcode symbols | `~/Library/Developer/Xcode/iOS DeviceSupport` | 6.4 GiB (one entry, `iPad14,5 27.0`) | Xcode on each new iPad OS build (~6.4 GiB per build) | none | delete old OS versions when the iPad updates |
| Staged macOS update | Preboot 15.3, `AssetsV2` SFR/MacSoftwareUpdate 2.6, `os.update` snapshots | ~18 GiB combined | macOS auto-downloaded an update and has not applied it | macOS self-manages | apply the update (restart) once there is room; pressure is what keeps it |
| Diagnostics | `/private/var/db/diagnostics` | 2.3 GiB | unified log | macOS | none (root-only) |

## Targeted playbook

Run each block as `ssh -o BatchMode=yes hub-mac '<block>'`. Order is biggest-safest first and stops being "A" at the marked line. Nominal Tier A yield is ~70 GiB; expect 55-65 GiB real because of clones/hardlinks.

**Step 0, preconditions (always):**

```sh
df -h /System/Volumes/Data | tail -1
ps -eo command | grep -E 'Runner\.Worker|xcodebuild|cargo|gradle|Xcode\.app|simctl|devicectl' | grep -v grep
# Runner.Listener lines are idle runners and fine. Any Runner.Worker or xcodebuild line: stop, skip the steps marked "idle only", try again later.
```

**A1. Stop the crash loop and reclaim its logs (2.7 GiB, 30 seconds).** The agent does nothing useful: its target dir does not exist.

```sh
launchctl bootout gui/$(id -u)/com.delorenj.cleanup_screenshots
: > ~/Library/Logs/cleanup_screenshots_error.log
: > ~/Library/Logs/cleanup_screenshots.log
: > ~/.openclaw/logs/node.err.log          # +0.8 GiB: second reconnect-loop log, see accumulators. Truncate only; leave the service running
```

Follow-up for the owner (do not skip: `launchctl bootout` lasts until the next login, because the plist has `RunAtLoad`, so either move the plist out of `~/Library/LaunchAgents` or fix the script). Fix: in `~/.config/zshyzsh/scripts/cleanup_screenshots/cleanup_screenshots.zsh` point `TARGET_DIR` at the real Drive folder under `~/Library/CloudStorage/GoogleDrive-<account>/My Drive/screenshots` (which of the two Drive accounts holds it is not known), remove `set -x`, exit 0 when the dir is missing. **Decide first** what the folder is for: the crontab line `*/2 * * * * rm -rf ~/gd/screenshots/*` empties it every 2 minutes once `~/gd` resolves again.

**A2. Old tower iOS run dirs (10.9 GiB).** Idle only (a tower build wrote `handoff/delorenj-tower-of-lost-things` at 04:25 today).

```sh
cd ~/.cache/tower-of-lost-things/ios && find . -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

**A3. Agent scratch clones (8.6 GiB + 0.3 bundles).** Re-verify first; both were clean and reachable from `origin/main` on 2026-10-28.

```sh
for d in gib-ios17-delivery gib-ios-preview-17; do git -C ~/.cache/$d status -s | head -3; done      # must print nothing
git -C ~/code/green-in-between fetch -q origin
git -C ~/code/green-in-between branch -r --contains 323c506 eb75261                                  # must list origin/main
rm -rf ~/.cache/gib-ios17-delivery ~/.cache/gib-ios-preview-17 ~/.cache/gib-*.bundle
```

**A4. gruvato 6.7 scratch (7.1 GiB).** `gruvato-67/repo` and `gruvato-checks/repo` were clean, detached at `8fbcccf`, contained in `origin/main`. Keep `gruvato-67/data` for now (Tier B).

```sh
for r in ~/gruvato-67/repo ~/gruvato-checks/repo; do git -C $r status -s | head -3; git -C $r branch -r --contains 8fbcccf; done   # clean + origin/main
pgrep -fl 'gruvato-67|gruvato-checks' || true                                                         # nothing running from them
rm -rf ~/gruvato-67/repo ~/gruvato-checks
```

**A5. Rust build output (4.5 GiB).** Idle only.

```sh
cd ~/code/gruvato/src-tauri && ~/.cargo/bin/cargo clean   # or: rm -rf target
```

**A6. Runner workspaces (7.9 GiB).** Idle only (Step 0 shows no `Runner.Worker`). Runner recreates `_work`; the next gruvato run recompiles from scratch (slow, one time).

```sh
for r in gruvato gib navi james-brennan; do rm -rf ~/actions-runner/$r/_work/*; done
rm -rf ~/actions-runner/_work/tower-of-lost-things
```

**A7. App caches (~15 GiB).** Quit the app first: Codex, Chrome, Neo, Xcode.

```sh
rm -rf ~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle                       # 3.6, quit Codex
rm -rf ~/Library/Application\ Support/Google/Chrome/OptGuideOnDeviceModel                   # 4.0, quit Chrome
rm -rf ~/Library/Application\ Support/Neo/component_crx_cache                               # 2.7, quit Neo
rm -rf ~/Library/Developer/Xcode/DerivedData/*                                              # 2.1, quit Xcode
rm -rf ~/Library/Caches/CocoaPods                                                           # 0.8
rm -rf ~/Library/Application\ Support/com.docker.install/in_progress                        # 2.1, Docker not installed
```

**A8. Simulator and toolchain caches (~13 GiB).**

```sh
xcrun simctl erase 12178C22-2533-44FD-BED8-19ACCDDECFC2      # iPhone 18 Pro, 3.6 GiB -> ~17 MB; do not delete the device
rm -rf ~/.local/share/pnpm/store/v10                           # 2.9, stale store (active one is ~/Library/pnpm/store/v11)
PATH=$HOME/.local/share/mise/shims:$PATH pnpm store prune      # trims the active v11 store
PATH=$HOME/.local/share/mise/shims:$PATH uv cache prune        # ~1.3
PATH=$HOME/.local/share/mise/shims:$PATH gradle --stop 2>/dev/null; rm -rf ~/.gradle/caches   # 4.1, re-downloads on next Android build
~/.cargo/bin/rustup toolchain uninstall 1.95.0-aarch64-apple-darwin   # 1.3, duplicate of `stable`
/opt/homebrew/bin/brew cleanup                                  # ~0 today, harmless
```

Rust precondition: `grep -rn '1\.95' ~/code/*/rust-toolchain* ~/code/*/mise.toml 2>/dev/null` shows no pin (the active default `stable` is 1.95.0 and keeps working).

**A9. Loose junk (~4.5 GiB).**

```sh
rm -rf ~/.Trash/* ~/size_tree.json ~/.local/bin/agy.*.old
# three identical Godot copies on the Desktop: confirm, then keep one
diff -rq ~/Desktop/Godot.app ~/Desktop/"Godot 2.app" >/dev/null && rm -rf ~/Desktop/"Godot 2.app" ~/Desktop/"Godot 3.app"
rm -f ~/Desktop/Claude.dmg ~/Desktop/Godot_v4.7.2-stable_macos.universal.zip
# installers already installed: FL Studio, dsh, Gruvato 0.2.2 alpha APK
rm -f ~/Downloads/flstudio_mac_*.dmg ~/Downloads/dsh-latest-macos-arm64.dmg ~/Downloads/Gruvato-0.2.2-android-alpha.apk
```

After A1..A9: expect ~16 GiB free to become ~70+ GiB, back above the 60 GiB "healthy" line.

**Tier B: decisions to put to the owner** (largest first). Put them as a list with the number, not as a deletion:

1. **Claude Cowork VM, 10.1 GiB** (`~/Library/Application Support/Claude/vm_bundles/claudevm.bundle`). "Do you use Cowork on this Mac? If not: quit Claude, delete it." It re-downloads ~10 GiB the first time Cowork is used again.
2. **`~/gruvato-backups`, 10.9 GiB.** "Gruvato 6.7 is merged; keep only the newest two backups (`2026-10-15/...-012517` 1.9 GiB and `2026-10-13/sh.delo.gruvato` 0.9 GiB, the oldest known-good), delete the other five (~8 GiB)?"
3. **Android emulator, 7.5 GiB** (`~/.android/avd` 4.6 + `Android/sdk/system-images` 2.9). "Do you run the Pixel 10 Pro emulator here? The hub deploys Android to the real S26." If no: `avdmanager delete avd -n Pixel_10_Pro`, then `sdkmanager --uninstall` the system image.
4. **iOS Simulator runtime, 7.5 GiB** (the 18 GiB disk image). "Any iOS Simulator work here, or only device builds to the iPad?" If device-only: `xcrun simctl runtime delete BB4C5B29-4E7F-4884-A277-CFE5D5446298` (Xcode re-offers it in Settings > Components).
5. **`iPad14,5 27.0` DeviceSupport, 6.4 GiB.** "Delete? It rebuilds next time the iPad is plugged in and trusted (~10 min)." Hub installs use `devicectl`, so deploys are unaffected.
6. **Apps and their libraries probably not yours, ~35 GiB.** "Whose are these, and still used?" iMovie 3.7, Affinity 3.6, CapCut 2.6 (+0.6 `~/Movies/CapCut`), Play-Doh 1.2, GarageBand 1.0 (+ `/Library/Audio` 4.7), Roblox Studio 0.9 (+ `~/Library/Roblox` 1.4), FL Studio 2.3, `/Library/Arturia` 8.7, `Studio 2.0` 2.3. Delete through Finder / the app's uninstaller; `/Library` items may need an admin password, which agents do not have.
7. **Loose media, ~11 GiB.** `thegrinch.mkv` 2.9, the three meeting recordings 1.6, `~/audio` 2.3, `~/quickdrop` 1.9, `~/music-presets` + `~/Presets` + `~/Splice` 3.5, duplicate `~/Music/verity.m4b` 0.22. "Move to the NAS (`rsync` to big-chungus) and delete locally?"
8. **gruvato leftovers, 2.2 GiB:** `~/gruvato-67/data` 1.2 (test instance and downloaded tools), `~/gruvato-spike` 1.0 (Sep 30 experiment).
9. **Neo LocalLLM 2.6, CodingAssistant 1.4, `~/.cache/codex-runtimes` 1.6, `gib-native` 1.0 (bake cache, 15-30 min to rebuild), Docker.raw 1.6, `~/flutter-3.38.1` 1.8.** Each is a "still used?" question.
10. **Voice Memos, 5.8 GiB (class C).** Mention only as: "if you want a last resort, export the recordings to the NAS first". Never delete.

If Tier A + B are not enough, the remaining lever is Carrie's account (~31 GiB, probably more): only she can clear it. Ask the user to have her check System Settings > General > Storage while logged in.

## Installed automation

- `~/Library/LaunchAgents/com.delorenj.cleanup_screenshots.plist`: named "cleanup" but it is the source of the biggest *leak*, not a cleaner (see A1). It is a screenshot-folder watcher that has been crash-looping since about 2026-09-24. `ai.openclaw.node.plist` is the second looping agent (0.8 GiB of 502 errors).
- mobile-deploy-hub itself bounds its own state: `outbox` keeps the newest 2 IPAs per app (`keepInOutbox`), `handoff-cache` is pruned at 3 days (`find ... -mtime +3` over ssh in `handoff.mjs`), big-chungus staging at 7 days (`pruneStaging`). It does NOT touch `~/.cache/<app>/ios` or `_work`.
- **One user crontab line:** `*/2 * * * * rm -rf /Users/delorenj/gd/screenshots/*` (a screenshots inbox on Google Drive, emptied every 2 minutes). It is a no-op today because `~/gd` is dangling, but **if anyone repoints `~/gd` / the watcher at a live Drive folder, this deletes everything in it every 2 minutes**. Do not "fix" the symlink without deciding what that folder is for (see A1 follow-up).
- No logrotate/newsyslog entry for user logs (`/etc/newsyslog.d` has only Apple files), no Time Machine, no brew autoupdate/cleanup job. `homebrew.mxcl.postgresql@18` and `pulseaudio` services are running, not cleaning.
- **Gaps:** nothing prunes tower run dirs, runner `_work`, Rust `target/`, gradle/pnpm/uv/cargo caches, Xcode DerivedData or DeviceSupport, scratch clones, or app-data backups. A monthly launchd job running the Tier A tool-native commands would stop this recurring; the free-space gate (15 GiB) should alert (`ntfy`) well before it blocks a deploy, e.g. at 40 GiB.

## Gotchas

- **`du` sees one Mac, `df` sees one container.** All APFS volumes share 16 GiB free. Deleting from Data frees it for everyone. "System Data" in Settings is the sum of the unattributed part plus caches: it is not a folder.
- **Sparse files lie in the other direction:** `Docker.raw` is 494 GB by `ls -l`, 1.6 GiB real. Use `du`, not `ls`, for sizes.
- **Disk images are not extra disk:** `disk4`/`disk5` (18.6 GB) is the simulator runtime mounted from a 7.5 GiB file under `/System/Library/AssetsV2`. `du -x` on `/private/var` also walks into the mounted cryptex (`/private/var/run/com.apple.security.cryptexd/mnt/...`, 17 GiB) and into `/private/var/vm` (the VM volume): subtract both or the totals overshoot by ~28 GiB.
- **`du` double-counts APFS clones and hardlinks** (pnpm/uv stores, cargo targets, `cp -c` handoff trees). Real yield of those caches is less than shown, and "Carrie's share by subtraction" is a *lower bound*.
- **`os.update` snapshots (3) and Preboot (15.3 GiB) are system-managed.** `tmutil deletelocalsnapshots` needs root and refuses `os.update` ones anyway. They shrink after the staged macOS update is applied and the Mac restarts, or when macOS needs space.
- **Looks deletable, is not:** `~/.local/share/mise/http-tarballs` (Flutter symlink), `~/Library/Caches/mobile-deploy-hub/{handoff,outbox}` (live deploy state, "Caches" is a lie), `~/Library/Application Support/sh.delo.gruvato` ("library" = live data), `~/.cache/gib-native/bake` (cheap to delete, 30 minutes to rebuild), `~/.hermes/hermes-agent`.
- **`~/.cache` is not all disposable on this Mac:** tower and gib dirs are agent/build output, but `~/.cache/mobile-deploy-hub` does not exist here (the hub's cache lives in `~/Library/Caches/mobile-deploy-hub`; big-chungus has the `~/.cache/mobile-deploy-hub/staging`).
- **brew is not on PATH in non-interactive ssh.** Use `/opt/homebrew/bin/brew`; mise tools need `PATH=$HOME/.local/share/mise/shims:$PATH`; rustup is `~/.cargo/bin/rustup`. `brew cleanup -n` reports 192 bytes: Homebrew is not the problem.
- **zsh remote shell:** unmatched globs error out and abort the line; `=` in a command word is expanded. `ssh hub-mac 'cmd'` runs under the user's zsh with the login PATH minimal.
- **`~/Library/CloudStorage` is a network mount that `find -xdev` does not stop at** (Google Drive for Desktop, two accounts: it walked into a Drive `node_modules` and ran 15+ minutes). `survey.sh` now prunes it and has a perl-alarm `timeout` fallback; the fixed full run takes ~10 minutes. Never `find`/`du` through `~/Library/CloudStorage` or `~/gd`; it also triggers downloads and Drive sync churn.
- **The machine name:** the Mac calls itself `mommymac` / "Carrie's MacBook Air"; runner names are `mommymac-*` and `carries-macbook-air`. The tailnet name is the profile key.
- **Time budget:** `du -sk -x ~` takes ~3 minutes over the tailscale ProxyCommand; `~/Library` alone ~1 minute. Batch.

## Run log

- 2026-10-28 — initial profile (read-only survey). Free: 16 GiB (97% used, container 17.2 GB free).
