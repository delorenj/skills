# carries-macbook-air — disk profile

**Last verified:** 2026-10-28 — if a run contradicts this file, the run wins: fix the file.

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

- **Now (2026-10-28, after the tier-A run):** 460 GiB container, 347 GiB used on Data, **71.3 GiB free (83%)**. Before: 402 GiB used, 15.2 GiB free (97%), 0.2 GiB above the hub's gate.
- **Measure in bytes, from the container:** `diskutil info / | sed -n 's/.*Container Free Space:.*(\([0-9]*\) Bytes).*/\1/p'`. `df -h` rounds to whole GiB, which hides most per-step deltas.
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
- **`~/Library/LaunchAgents.attic/`**: retired agents (`com.delorenj.cleanup_screenshots`, `ai.openclaw.node`) and the removed crontab, with a `README.txt` of restore commands. The openclaw plist carries a gateway token. Do not restore the crontab (see Installed automation).
- **`~/.Trash` contents trashed recently.** On 2026-10-28 everything in it (an Obsidian-style vault: `AI`, `_bmad`, `Sandbox`, `System`, `agents` 0.74 GiB) had been trashed the day before. Recently trashed items are the owner's call (B), not junk. The trash date is the item's **ctime** (`stat -f %Sc`), not its mtime. `mdls kMDItemDateAdded` returns `(null)` here.

## Space map

Whole-disk accounting (GiB), from the 2026-10-28 survey taken before the tier-A run: Data volume = 402. After the run Data = 347. The home rows below give "→ now" for what the run changed.

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
| `~/.cache/tower-of-lost-things/ios/<run>` | 10.9 → 0 | A | 46 per-run dirs (xcarchive, Godot engine/templates copy, export, logs). Writer: tower repo `tools/ios.mjs` `build()`. Cleaned 2026-10-28 (real 10.65). Now bounded twice: `pruneRuns` in `ios.mjs` (tower `8bd2872`: >7d, newest 3 builds kept) and the weekly agent |
| `~/.cache/gib-ios17-delivery`, `~/.cache/gib-ios-preview-17`, `gib-*.bundle` (8), `gib-ios-preview-17-sign-probe` | 8.9 → 0 | A | agent-made clones of green-in-between, made by hand during iOS preview deliveries (no script writes them; BMAD specs in the gib repo cite evidence paths inside them). Removed 2026-10-28 after re-verifying clean, no stash, HEADs in `origin/main` (real 7.89). The weekly agent removes future ones >7d only when clean and pushed |
| `~/.cache/gib-native` | 1.0 | B | `bake/` is a content-addressed Blender/Cycles bake: 15-30 min to rebuild; `godot/`, `ios-hub/` toolchain. The weekly agent never touches it |
| `~/.cache/codex-runtimes` | 1.6 | B | Codex app runtimes |
| `~/.cache/uv` + `~/.local/share/uv` | 1.3 + 1.1 | A | `uv cache prune` freed only 0.1 (it drops unreferenced entries; `uv cache clean` would take all) |
| `~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle` | 3.6 | A (app quit) | **belongs to ChatGPT.app** (bundle id `com.openai.codex`; there is no Codex.app). Sparkle `Installation/` + `Launcher/` written 2026-10-25: a staged update. Skipped 2026-10-28 because ChatGPT was running. Delete only with ChatGPT quit |
| `~/Library/Caches/mobile-deploy-hub` | 3.1 | C | handoff 2.0, handoff-cache 0.9, outbox 0.2. Hub-managed |
| `~/Library/Caches/Citro Labs/ego lite` | 2.1 | B | browser cache of the agent browser; cache only, but sits beside live profiles |
| `~/Library/Caches/CocoaPods` | 0.8 → 0 | A | removed 2026-10-28 |
| `~/Library/Application Support/Claude/vm_bundles` | 10.1 | B | `claudevm.bundle`, the Claude Cowork VM (rootfs etc.), in use while Claude.app runs. Re-downloads ~10 GiB on next Cowork use |
| `~/Library/Application Support/Google/Chrome/OptGuideOnDeviceModel` | 4.0 | A (app quit) | Chrome's on-device Gemini Nano model; re-downloads only if the feature is used. Skipped 2026-10-28: Chrome was running (live desktop, logged-in profiles) |
| `~/Library/Application Support/Google/Chrome` profiles | 3.3 | C | logged-in browser profiles |
| `~/Library/Application Support/Google/DriveFS` | 1.6 | C | Drive sync cache, may hold unsynced files |
| `~/Library/Application Support/Neo/component_crx_cache` | 2.7 → 0 | A | extension component cache of `/Applications/Neo.app` (a Chromium browser). Removed 2026-10-28 with Neo not running |
| `~/Library/Application Support/Neo/LocalLLM` | 2.6 | B | on-device model |
| `~/Library/Application Support/sh.delo.gruvato` | 4.5 | C | live Gruvato data |
| `~/Library/Application Support/Citro Labs/ego lite` | 3.5 | C | authenticated agent browser profiles |
| `~/Library/Application Support/com.docker.install/in_progress` | 2.1 → 0 | A | half-finished Docker Desktop install from Sep 4; Docker is not installed. Removed 2026-10-28 |
| `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw` | 1.6 | B | sparse VM disk of the uninstalled Docker. `ls` says 460 GiB apparent, 1.6 GiB real. Any volumes inside are lost with it |
| `~/Library/Developer/Xcode/iOS DeviceSupport/iPad14,5 27.0 (24A437)` | 6.4 | B | symbols for the one device the hub deploys to. Regenerates on next connect (~10 min, iPad plugged in and trusted) |
| `~/Library/Developer/Xcode/DerivedData` | 2.4 → 0 | A | removed 2026-10-28 (Xcode not running); the weekly agent drops project dirs untouched for 14d |
| `~/Library/Developer/Xcode/CodingAssistant` | 1.4 | B | Xcode predictive-completion model assets |
| `~/Library/Developer/CoreSimulator/Devices/12178C22-...` | 3.6 | B | iPhone 18 Pro simulator data. The other 10 devices are 17 MB each. All Shutdown, none "unavailable". `simctl erase` wipes the apps and state inside the simulator, so it is B (as in `macos.md`), not A. Only `simctl delete unavailable` is A |
| `~/Library/Android/sdk/system-images` | 2.9 | B | Android emulator images; the hub installs Android builds to a real S26 (`devices.json`), not an emulator |
| `~/.android/avd` (`Pixel_10_Pro.avd`) | 4.6 | B | the only AVD |
| `~/.gradle/caches` | 4.1 → 0 | A | removed 2026-10-28 with no Gradle daemon/JVM running (real 4.17). Re-downloads on next Gradle build. `~/.gradle/wrapper/dists` 0.4 left |
| `~/.rustup/toolchains` | 5.5 → 4.3 | mixed | `stable` = rustc 1.95.0 (default, 2.2), `1.98.0` (2.1, pinned by gib `server/` and `native/` `rust-toolchain.toml`). The duplicate `1.95.0` (same rustc as stable, nothing pinned it) was uninstalled 2026-10-28 (real 1.31) |
| `~/.local/share/mise/installs` | 4.5 | C | node 1.5, python 0.6, dart 0.6, heroku 0.5... |
| `~/.local/share/mise/http-tarballs` | 3.7 | C | Flutter 3.38.1 lives here (symlink). Never delete |
| `~/.local/share/pnpm/store/v10` | 2.9 → 0 | A | **not stale**: the store behind the global pnpm installs (`~/.local/share/pnpm/global/5`: pm2, opencode-ai, claude-flow, typescript-language-server, marp, openclaw). Removed 2026-10-28 anyway; the globals kept working (pnpm materialises files into `node_modules/.pnpm`), verified by loading their `package.json`. Removal + `pnpm store prune` freed 2.43 together |
| `~/Library/pnpm/store/v11` (+ `v10`) | 2.1 → 1.25 total | A | `v11` is the active store (`pnpm store path`). `~/Library/pnpm/store/v10` is what `~/code/tokamak/node_modules` points at: leave it. `pnpm store prune` only trims the active store |
| `~/.local/share/pnpm/store/v11` | 0.6 | B | a second v11 store; check `pnpm store path` per project before removing |
| `~/.local/share/pnpm/global` | 1.0 | B | global pnpm installs |
| `~/.local/share/nvim` (`mason` 2.0, `lazy` 1.0) | 3.1 | B | editor tooling |
| `~/.local/share/tonny/releases` | 1.1 | B | |
| `~/.local/share/claude/versions` | 1.0 | B | 4 Claude Code versions (2.1.307 to 2.1.312); the newest is the one in use |
| `~/.local/bin/agy.*.old` | 0.2 → 0 | A | old binary, removed 2026-10-28 |
| `~/code/gruvato/src-tauri/target` | 4.5 → 0 | A | `cargo clean` 2026-10-28 (reported 4.7 GiB, real 4.19). The repo itself is clean and pushed |
| `~/code` rest | 9.2 | C/B | green-in-between 2.0 (`native` 1.5), tokamak 1.3, intelliforia-mobile 1.1, DeLoDocs 1.0, ... dirty trees listed in Never touch |
| `~/gruvato-backups` | 10.9 | B | 7 timestamped copies of `sh.delo.gruvato` (1.4 GiB each, 2026-10-13..15) plus an app. Pre-migration safety copies from the 6.1 to 6.7 work |
| `~/gruvato-67` | 5.5 → 1.6 | B | `repo/` (scratch clone at detached `8fbcccf`, clean, in `origin/main`) removed 2026-10-28 together with `~/gruvato-checks` (real 4.78). Left: `data/`, `data2/`, `render-b-*`, scripts and logs, 1.6: B |
| `~/gruvato-checks` | 1.7 → 0 | A | same detached `8fbcccf`, clean; removed 2026-10-28 |
| `~/gruvato-spike` | 1.0 | B | Sep 30 separator experiment outputs + `.venv`. Not a git repo |
| `~/actions-runner/<r>/_work` | 7.9 → 0.25 | A | `gruvato` 4.0, `gib` 1.3, `navi` 1.2, `james-brennan` 1.2, shared `_work/tower-of-lost-things` 0.24. Emptied 2026-10-28 with no `Runner.Worker` running (real 6.46). Regrows per job (gruvato's Rust `target` is the bulk); the weekly agent removes entries idle 7d |
| `~/actions-runner` rest (`externals` x5, `bin` x5, `_diag`) | 2.5 → 2.0 | C | runner binaries. `_diag` logs >7d (0.23, 557 files) are pruned by the weekly agent |
| `~/Library/Logs/cleanup_screenshots_error.log` + `.log` | 1.9 → 0 | A | crash-loop logs, truncated 2026-10-28 and their writer retired: see accumulators |
| `~/.openclaw/logs/node.err.log` | 0.8 → 0 | A | 502 reconnect-loop log, truncated 2026-10-28, writer retired |
| `~/Library/Logs` rest | 0.3 | A | |
| `~/Library/Caches/ollama/updates` | 0.2 | A (app quit) | downloaded `Ollama-darwin.zip`; Ollama was running on 2026-10-28, left |
| `~/docker/stacks/media/video/*.avi.!qB` | 1.2 | B | an unfinished qBittorrent download from 2025-06 inside the `DeLoContainers` clone |
| `~/Downloads` | 3.5 → 2.1 | A / B | removed 2026-10-28: `flstudio_mac_26.1.7.5421.dmg` 1.1 (FL Studio 2026 installed), `Gruvato-0.2.2-android-alpha.apk` 0.26. **`dsh-latest-macos-arm64.dmg` 0.25 is B**: dsh is not installed (no app, no binary). Videos (~0.6) and the rest: B. Also holds two `1password-credentials*.json` (secrets, not disk) |
| `~/Desktop` | 1.4 → 0.4 | A / B | removed 2026-10-28: two of three identical `Godot*.app` copies (kept `Godot.app`), `Claude.dmg`, `Godot_v4.7.2...zip`, `Hermes-Setup.dmg` (apps installed). Screenshots and documents: B. Holds a `*.private-key.pem` (secret, not disk) |
| `~/.Trash` | 0.8 | B | everything in it was trashed 2026-10-27 (ctime), the day before the run: an owner decision, not junk. Only the `Audacity_Installer_via_MuseHub.pkg` installer was removed |
| `~/size_tree.json` | 0.3 → 0 | A | a stray `gdu`/du tree dump from Apr 30, removed |
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
| long tail | ~17 | mixed | ~300 entries under 0.9 each (`.npm` 0.8, `.antigravity-ide` 0.8, `if-ext` 0.8, `.cursor` 0.7, `.cargo/registry` 0.6, `.pulumi` 0.6...) |

`/Applications` (59.7): Xcode 3.9, iMovie 3.7, Affinity 3.6, Android Studio 3.0, CapCut 2.6, `Studio 2.0` 2.3, FL Studio 2.3, Chrome 2.1, ChatGPT 1.7, Play-Doh 1.2, Teams 1.1, GarageBand 1.0, stitch 1.0, then ~100 apps under 1 GiB. Several are probably Carrie's or the kids' (iMovie, CapCut, Affinity, Play-Doh, GarageBand, Roblox Studio): **class B, ask whose they are**. `/Library/Arturia` (8.7), `/Library/Audio` (4.7, GarageBand/Logic loops) are the same story.

**Could not measure:** Carrie's home and root-only paths (no sudo), APFS snapshot-held blocks (`tmutil` lists three `os.update` snapshots, size not queryable without root), Time Machine (no destinations configured), iCloud-evicted files, and the exact real yield of hardlink/clone-heavy caches (pnpm, uv, cargo: `du` shows full size in both places).

## Known accumulators

| What regrows | Where | Observed | Growth driver | Bound now (2026-10-28) |
|---|---|---|---|---|
| Crash-loop stderr/stdout | `~/Library/Logs/cleanup_screenshots_error.log`, `.log` | 1.75 + 0.18 GiB, ~52 MB/day, 19,696 launchd runs | launchd agent `com.delorenj.cleanup_screenshots` (`KeepAlive`, `set -x`, no `ThrottleInterval`) restarting every ~10 s. Two causes: `~/gd -> Google Drive/My Drive` is dangling (Drive for Desktop now mounts under `~/Library/CloudStorage/GoogleDrive-*`), and the script calls `/usr/local/bin/fswatch`, an Intel-Homebrew path that does not exist on this Apple Silicon Mac (`/opt/homebrew/bin/fswatch`). Purpose (watch a Drive screenshots inbox, copy the path to the clipboard, delete the file after 2 min) is obsolete: `screencapture` now saves to `~/FUCKING_SCREENSHOTS` | **retired**: booted out, plist moved to `~/Library/LaunchAgents.attic/`, logs truncated. The script still sits in `~/.config/zshyzsh/scripts/cleanup_screenshots/` (unloaded, harmless) |
| (danger, not bytes) `rm -rf` crontab | user crontab `*/2 * * * * rm -rf ~/gd/screenshots/*` | — | companion of the watcher. A no-op while `~/gd` dangled, but real synced folders `My Drive/screenshots` exist under `~/Library/CloudStorage/GoogleDrive-jaradd@gmail.com*`: repointing `~/gd` would have wiped them, and their cloud copy, every 2 minutes | **removed** (the crontab had only this line; saved as `crontab-2026-10-28.txt` in the attic) |
| Reconnect-loop stderr | `~/.openclaw/logs/node.err.log` | 0.8 GiB since 2026-03-27, 165,155 launchd runs | launchd agent `ai.openclaw.node` (`KeepAlive`, `ThrottleInterval 1`) dialing `big-chungus.burro-salmon.ts.net:443`. The OpenClaw gateway there (`openclaw-gateway.service`) is **disabled**, and tailscale serve `:443` now proxies `/` to `:5173`, which answers 502 | **retired**: booted out, plist to the attic, log truncated |
| iOS build run dirs | `~/.cache/tower-of-lost-things/ios/<run>` | 10.9 GiB, 46 dirs, 0.2 to 2.5 GiB each | tower repo `tools/ios.mjs` `build()`, run by the root runner and by hand | **`pruneRuns()` in `ios.mjs`** (tower `8bd2872`): before each build it removes run/preflight/handoff/install/upload dirs >7d, keeping the newest 3 builds for `exportOnly`. It also covers the Linux-side mirror. Backstop: weekly agent, same rule |
| Runner workspaces + diag | `~/actions-runner/*/_work`, `*/_diag` | 7.9 GiB `_work`, 0.23 GiB `_diag` | the 5 runners; `gruvato` keeps a Rust `target` | **weekly agent**: `_work` entries with nothing written within 2 levels for 7d, and `_diag` files >7d, only while no `Runner.Worker` runs (re-checked per runner) |
| Rust build output | `~/code/gruvato/src-tauri/target` (+ runner `_work`) | 4.5 GiB | `cargo`/`tauri build` by hand | none: a dev tree in active use. Recommended: `cargo clean` after a release, or `cargo sweep --time 14` |
| Agent-made scratch clones | `~/.cache/gib-ios*`, `~/gruvato-67`, `~/gruvato-checks`, `~/gruvato-spike` | 8.9 + 5.5 + 1.7 + 1.0 GiB | agents doing delivery/release work by hand (no script; checked green-in-between) and never cleaning up | **weekly agent** for `~/.cache/gib-ios*` + `gib-*.bundle` >7d (clean, no stash, no unpushed commits; bundles only when every head is in `~/code/green-in-between`). `~/gruvato-*` scratch at `$HOME` top level: none. Agents should delete their scratch clone when the delivery is verified |
| App-data backups | `~/gruvato-backups/<date>/` | 10.9 GiB, 7 copies | manual pre-migration backups before gruvato 6.x work | none (tier B) |
| Claude Cowork VM | `~/Library/Application Support/Claude/vm_bundles` | 10.1 GiB | Claude.app (re-downloads after removal) | none (tier B) |
| ChatGPT updater staging | `~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle` | 3.6 GiB | ChatGPT.app's Sparkle updates (bundle id `com.openai.codex`) | none. Delete when ChatGPT is quit |
| Chrome on-device model | `.../Google/Chrome/OptGuideOnDeviceModel` | 4.0 GiB | Chrome | none. Delete with Chrome quit; `chrome://flags` "optimization guide on device model" off stops it |
| Tool caches | `~/Library/pnpm/store`, `~/.cache/uv`, `~/Library/Developer/Xcode/DerivedData`, simulators | 2.1 + 1.3 + 2.4 GiB | normal tool use | **weekly agent**: `pnpm store prune`, `uv cache prune`, DerivedData project dirs >14d, `simctl delete unavailable`. Gradle, CocoaPods and cargo registry are not swept (small after this run) |
| Runaway logs (generic) | `~/Library/Logs/**`, `~/.<tool>/logs/**` | — | any future crash loop | **weekly agent** truncates files >100 MB in place |
| Hub catch-up log | `~/Library/Logs/mobile-deploy-hub/catchup.log` | 1.3 MB since 2026-10-09 (~70 KB/day) | `sh.delo.mobile-deploy-hub.catchup`, `StartInterval 300` (686 runs, exit 0: periodic, not a loop) | weekly agent at 100 MB (years away). Rotation belongs in the hub if it ever matters |
| Per-device Xcode symbols | `~/Library/Developer/Xcode/iOS DeviceSupport` | 6.4 GiB (one entry, `iPad14,5 27.0`) | Xcode on each new iPad OS build (~6.4 GiB per build) | none (tier B). Delete old OS versions when the iPad updates |
| Staged macOS update | Preboot 15.3, `AssetsV2` SFR/MacSoftwareUpdate 2.6, `os.update` snapshots | ~18 GiB combined | macOS auto-downloaded an update and has not applied it | macOS self-manages. Apply the update (restart) now that there is room |
| Diagnostics | `/private/var/db/diagnostics` | 2.3 GiB | unified log | macOS (root-only) |

## Targeted playbook

Run every block as a bash heredoc, not a quoted one-liner: the remote login shell is zsh, and globs, `=` and quotes bite there.

```sh
ssh -o BatchMode=yes hub-mac 'bash -s' <<'EOF'
export PATH=$HOME/.local/share/mise/shims:$HOME/.cargo/bin:/opt/homebrew/bin:$PATH
cf() { diskutil info / | sed -n 's/.*Container Free Space:.*(\([0-9]*\) Bytes).*/\1/p'; }
g()  { awk -v b="$1" 'BEGIN{printf "%.2f GiB", b/1073741824}'; }
busy() { pgrep -x 'Runner\.Worker|xcodebuild' >/dev/null; }   # NOT pgrep -f: on macOS it matches the environment too
B=$(cf); <one category>; A=$(cf); echo "<cat>: $(g $B) -> $(g $A) (+$(g $((A-B))))"
EOF
```

Real yields from 2026-10-28 (15.2 to 71.3 GiB, container free in bytes) are given per step. Today the weekly agent keeps most of these from regrowing, so a repeat run will find far less.

**Step 0, preconditions, re-checked right before every `rm`, not once at the start.** A `Runner.Worker` started five minutes into the 2026-10-28 run. Steps blocked by a busy check are **deferred to the end and retried**, not dropped.

```sh
pgrep -xl 'Runner\.Worker|xcodebuild|Xcode|cargo|rustc|java'      # Runner.Listener x5 = idle runners, fine
ps -eo command | grep -E '/Applications/[^/]+\.app/Contents/MacOS/' | sed -E 's#^(/Applications/[^/]+\.app).*#\1#' | sort -u   # GUI apps running now
```

A GUI app that is running on the console session is in use: skip its cache and record the skip. Do not quit it. On 2026-10-28 Chrome, ChatGPT, Claude, ego lite, Ollama, FL Studio and Gruvato were running.

**A1. Runaway logs and restart loops (2026-10-28: 2.73 GiB in 30 s).** Look for new ones first: `find ~/Library/Logs ~/.[!.]*/logs -maxdepth 3 -type f -size +204800` (100 MB) and the `runs =` count of every agent (`for f in ~/Library/LaunchAgents/*.plist; do l=$(basename "$f" .plist); echo "$(launchctl print gui/$(id -u)/$l 2>/dev/null | awk '/^\truns =/{print $3}') $l"; done | sort -rn | head`). Thousands of runs plus `KeepAlive` means a crash loop. Truncate its log with `: > file` (never `rm` an open log). If the agent is obsolete, retire it reversibly: `launchctl bootout gui/$(id -u)/<label>` and move the plist to `~/Library/LaunchAgents.attic/`. `bootout` alone lasts only until the next login (`RunAtLoad`). Both 2026-10-28 loops are retired: see accumulators.

**A2. Agent scratch clones (7.89).** Re-verify each: `git status --porcelain` empty, `git stash list` empty, every HEAD an ancestor of the real repo's `origin/main` after a fetch (`git -C ~/code/<repo> merge-base --is-ancestor <sha> origin/main`), and `pgrep -x`/`lsof +D` shows nothing using it. Clones under `~/.cache/gib-ios*` and their `gib-*.bundle` files are now swept weekly. Scratch at `$HOME` top level (`~/gruvato-67/repo`, `~/gruvato-checks`, 4.78) is not, so check `ls -d ~/gruvato-* ~/*-checks ~/*-scratch 2>/dev/null` each run. Leave `gruvato-67/data*` (B).

**A3. App caches of apps not running (8.07).** Gate each on `pgrep`/`ps` for the owning app:

```sh
rm -rf ~/Library/Application\ Support/Neo/component_crx_cache        # 2.7, /Applications/Neo.app
find ~/Library/Developer/Xcode/DerivedData -mindepth 1 -maxdepth 1 -exec rm -rf {} +   # 2.4, Xcode/xcodebuild not running
rm -rf ~/Library/Caches/CocoaPods                                      # 0.86
rm -rf ~/Library/Application\ Support/com.docker.install/in_progress   # 2.1, only while /Applications/Docker.app is absent
# Only with the app quit (skipped 2026-10-28, both running):
#   ~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle      3.6, owner is ChatGPT.app (bundle id com.openai.codex)
#   ~/Library/Application Support/Google/Chrome/OptGuideOnDeviceModel  4.0, Chrome
#   ~/Library/Caches/ollama/updates                                    0.2, Ollama
```

Find a cache's owner by bundle id, not by its name: `mdfind "kMDItemCFBundleIdentifier == '<id>'"`.

**A4. Toolchain caches (2026-10-28: rust 1.31, pnpm 2.43, uv 0.10, gradle 4.17).**

```sh
xcrun simctl delete unavailable                                   # 0 on 2026-10-28. simctl erase is B, not A
grep -rIl -e '1\.95' --include='rust-toolchain*' ~/code ~/actions-runner/*/_work 2>/dev/null   # empty, then:
rustup toolchain uninstall 1.95.0-aarch64-apple-darwin            # done 2026-10-28: duplicate of stable. Re-check `rustup toolchain list` for a new duplicate
pnpm store prune                                                  # active store ~/Library/pnpm/store/v11; leave ~/Library/pnpm/store/v10 (tokamak uses it)
uv cache prune                                                    # small: only unreferenced entries
pgrep -xl java || rm -rf ~/.gradle/caches                         # re-downloads on the next Gradle build
/opt/homebrew/bin/brew cleanup                                    # 192 bytes, Homebrew is not the problem
```

**A5. Rust build output (4.19).** No `pgrep -x 'cargo|rustc'` hit: `cd ~/code/gruvato/src-tauri && cargo clean`.

**A6. Loose junk (1.85 of 2.9 nominal; the duplicate `Godot*.app` copies were most likely APFS clones, which free little).** Installers only when the app is verifiably installed (`ls -d /Applications/<App>.app` or `command -v`), duplicate app copies only after `diff -rq`, stray dumps (`~/size_tree.json`), `~/.local/bin/*.old`. **Never `rm -rf ~/.Trash/*`**: remove only installer junk from it, and only items trashed more than 30 days ago (`stat -f '%Sc' -t %F` = when trashed). On 2026-10-28 the whole Trash was one day old.

**Last, when idle: per-run build dirs and runner workspaces (tower 10.65, `_work` 6.46).** Both need `busy` false right before each `rm`; on 2026-10-28 they had to wait for a running job.

```sh
busy || { cd ~/.cache/tower-of-lost-things/ios && find . -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +; }
for w in ~/actions-runner/{gruvato,gib,navi,james-brennan}/_work; do busy && break; find "$w" -mindepth 1 -maxdepth 1 -exec rm -rf {} +; done
busy || rm -rf ~/actions-runner/_work/tower-of-lost-things
```

The tower repo now prunes its own run dirs before each build (newest 3 kept), and the weekly agent sweeps idle `_work`. Expect little here unless the agent stopped running: check `tail ~/Library/Logs/sh.delo.disk-maintenance.log` first.

**Tier B: decisions to put to the owner** (largest first). Put them as a list with the number, not as a deletion:

1. **Claude Cowork VM, 10.1 GiB** (`~/Library/Application Support/Claude/vm_bundles/claudevm.bundle`). "Do you use Cowork on this Mac? If not: quit Claude, delete it." It re-downloads ~10 GiB the first time Cowork is used again.
2. **`~/gruvato-backups`, 10.9 GiB.** "Gruvato 6.7 is merged; keep only the newest two backups (`2026-10-15/...-012517` 1.9 GiB and `2026-10-13/sh.delo.gruvato` 0.9 GiB, the oldest known-good), delete the other five (~8 GiB)?"
3. **Android emulator, 7.5 GiB** (`~/.android/avd` 4.6 + `Android/sdk/system-images` 2.9). "Do you run the Pixel 10 Pro emulator here? The hub deploys Android to the real S26." If no: `avdmanager delete avd -n Pixel_10_Pro`, then `sdkmanager --uninstall` the system image.
4. **iOS Simulator runtime, 7.5 GiB** (the 18 GiB disk image). "Any iOS Simulator work here, or only device builds to the iPad?" If device-only: `xcrun simctl runtime delete BB4C5B29-4E7F-4884-A277-CFE5D5446298` (Xcode re-offers it in Settings > Components).
5. **`iPad14,5 27.0` DeviceSupport, 6.4 GiB.** "Delete? It rebuilds next time the iPad is plugged in and trusted (~10 min)." Hub installs use `devicectl`, so deploys are unaffected.
6. **Apps and their libraries probably not yours, ~35 GiB.** "Whose are these, and still used?" iMovie 3.7, Affinity 3.6, CapCut 2.6 (+0.6 `~/Movies/CapCut`), Play-Doh 1.2, GarageBand 1.0 (+ `/Library/Audio` 4.7), Roblox Studio 0.9 (+ `~/Library/Roblox` 1.4), FL Studio 2.3, `/Library/Arturia` 8.7, `Studio 2.0` 2.3. Delete through Finder / the app's uninstaller; `/Library` items may need an admin password, which agents do not have.
7. **Loose media, ~11 GiB.** `thegrinch.mkv` 2.9, the three meeting recordings 1.6, `~/audio` 2.3, `~/quickdrop` 1.9, `~/music-presets` + `~/Presets` + `~/Splice` 3.5, duplicate `~/Music/verity.m4b` 0.22. "Move to the NAS (`rsync` to big-chungus) and delete locally?"
8. **gruvato leftovers, 2.6 GiB:** `~/gruvato-67` remainder 1.6 (`data/`, `data2/`, `render-b-*` test instances, scripts, logs; its `repo/` is gone), `~/gruvato-spike` 1.0 (Sep 30 experiment).
9. **Neo LocalLLM 2.6, CodingAssistant 1.4, `~/.cache/codex-runtimes` 1.6, `gib-native` 1.0 (bake cache, 15-30 min to rebuild), Docker.raw 1.6, `~/flutter-3.38.1` 1.8.** Each is a "still used?" question.
10. **Voice Memos, 5.8 GiB (class C).** Mention only as: "if you want a last resort, export the recordings to the NAS first". Never delete.
11. **iPhone 18 Pro simulator data, 3.6 GiB** (`xcrun simctl erase 12178C22-2533-44FD-BED8-19ACCDDECFC2`). Reclassified A to B on 2026-10-28: erase wipes the apps and state inside the simulator.
12. **`~/.Trash`, 0.74 GiB** (`agents`, plus a vault-like tree), all trashed 2026-10-27. "Empty the Trash?" Also offer Finder's "Remove items from the Trash after 30 days" (`defaults write com.apple.finder FXRemoveOldTrashItems -bool true`) as the standing bound. It is a deferred deletion, so it needs the owner's yes.
13. **`~/Downloads/dsh-latest-macos-arm64.dmg`, 0.25 GiB.** dsh is not installed, so this is not an installed-app leftover.

If Tier A + B are not enough, the remaining lever is Carrie's account (~31 GiB, probably more): only she can clear it. Ask the user to have her check System Settings > General > Storage while logged in.

## Installed automation

- **`sh.delo.disk-maintenance`** (installed 2026-10-28): `~/.local/bin/disk-maintenance` run by `~/Library/LaunchAgents/sh.delo.disk-maintenance.plist`, Sundays 05:17, loaded in `gui/502`. Canonical copy plus `install.sh` and a README live in `~/code/infra/hosts/carries-macbook-air/` on big-chungus. Edit there, then re-run `install.sh`, which copies, lints and re-bootstraps. It sweeps DerivedData >14d, tower run dirs >7d (newest 3 kept), clean+pushed `~/.cache/gib-ios*` clones/bundles >7d, idle runner `_work` and `_diag` >7d (no `Runner.Worker`), logs >100M (truncated), `simctl delete unavailable`, `pnpm store prune`, `uv cache prune`. It logs a WARNING under 40 GiB free. `disk-maintenance --dry-run` previews. Log: `~/Library/Logs/sh.delo.disk-maintenance.log` (self-truncates at 5 MB). Verified 2026-10-28: dry run, then a real run via `launchctl kickstart` (exit 0, +0.22 GiB of `_diag`). Check: `launchctl print gui/$(id -u)/sh.delo.disk-maintenance | grep -E "state|runs|last exit"`. `runs` resets to 0 on every re-bootstrap.
- **tower-of-lost-things `tools/ios.mjs` `pruneRuns()`** (commit `8bd2872`): run dirs >7d are pruned before each build, newest 3 builds kept. It logs `IOS_PRUNED <n>` / `IOS_PRUNE_WARNING`.
- mobile-deploy-hub bounds its own state: `outbox` keeps the newest 2 IPAs per app (`keepInOutbox`), `handoff-cache` is pruned at 3 days (`find ... -mtime +3` over ssh in `handoff.mjs`), big-chungus staging at 7 days (`pruneStaging`).
- **Retired 2026-10-28** (in `~/Library/LaunchAgents.attic/` with a restore README): `com.delorenj.cleanup_screenshots` (the "cleanup" agent was the biggest leak), the user crontab `*/2 * * * * rm -rf ~/gd/screenshots/*` (removed; the user now has no crontab), and `ai.openclaw.node`.
- No newsyslog entry for user logs (`/etc/newsyslog.d` has only Apple files, and needs sudo), no Time Machine, no brew cleanup job. `homebrew.mxcl.postgresql@18` and `pulseaudio` run but do not clean.
- **Gaps:** no loud alert. The weekly WARNING only lands in a log nobody reads. An ntfy push needs a token on the Mac (`op://` or env, never plaintext), so it is a follow-up. Also not swept: Rust `target/` in dev trees, gradle/cargo registries, DeviceSupport, app-data backups, `$HOME`-level scratch clones, and Chrome/ChatGPT caches (they need the app quit).

## Gotchas

- **`du` sees one Mac, `df` sees one container.** All APFS volumes share one free pool (16 GiB before the 2026-10-28 run, 71 after). Deleting from Data frees it for everyone. "System Data" in Settings is the sum of the unattributed part plus caches: it is not a folder.
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
- **Time budget:** `du -sk -x ~` takes ~3 minutes over the tailscale ProxyCommand; `~/Library` alone ~1 minute. Batch. `survey.sh --quick` took ~4 minutes on 2026-10-28.
- **`pgrep -f` lies on macOS:** it matches the process environment as well as its arguments, so `pgrep -f cargo` hit two `npm exec` MCP servers whose `PATH` contains `~/.cargo/bin` and blocked `cargo clean` for nothing. Busy checks: `pgrep -x <name>` (process name) or `ps -axo command | grep '[n]ame'` (arguments only).
- **Bundle ids are not app names:** `~/Library/Caches/com.openai.codex` belongs to ChatGPT.app, which is running all day. Resolve the owner with `mdfind "kMDItemCFBundleIdentifier == '<id>'"` before deciding the app is idle.
- **Trash age is ctime:** an item's mtime keeps its original date (`agents` said May 24). The time it was trashed is its ctime. `mdls kMDItemDateAdded` returns `(null)` over ssh.
- **Jobs start mid-run:** the root runner (`actions.runner.delorenj-pile-of-dumb-things.carries-macbook-air`, which also serves tower) picked up a job five minutes in. Check `busy` immediately before each runner- or build-dir `rm`, not once.
- **Intel paths in old automation:** `/usr/local/bin/<tool>` in a 2025 script or plist fails on this Apple Silicon Mac (brew is `/opt/homebrew`). With `KeepAlive` that becomes a crash loop and a log leak.
- **launchd over ssh works into `gui/502`** while delorenj is logged in at the console (`stat -f %Su /dev/console`). `bootout` followed immediately by `bootstrap` can fail with "5: Input/output error". `install.sh` retries.
- **Secrets seen on disk (not a disk issue, flagged 2026-10-28):** `~/Downloads/1password-credentials*.json`, `~/Desktop/*.private-key.pem`, and a gateway token inside the retired openclaw plist.

## Run log

- 2026-10-28 — free 15.2 GiB → 71.3 GiB. tier A (container free, diskutil bytes): crash-loop logs 2.7, tower runs 10.7, gib scratch 7.9, gruvato scratch 4.8, gruvato target 4.2, runner _work 6.5, Neo/DerivedData/CocoaPods/docker-install 8.1, rust dup 1.3, pnpm 2.4, uv 0.1, gradle 4.2, junk 1.9. Retired com.delorenj.cleanup_screenshots + its rm -rf crontab and ai.openclaw.node (attic). Bounds: tower ios.mjs retention (8bd2872), weekly sh.delo.disk-maintenance agent (infra 2c3e1ba). Skipped (app running): ChatGPT Sparkle 3.6, Chrome OptGuide 4.0. Tier B untouched.
- 2026-10-28 — initial profile (read-only survey). Free: 16 GiB (97% used, container 17.2 GB free).
