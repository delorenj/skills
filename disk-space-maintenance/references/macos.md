# macOS playbook (generic)

Machine-specific paths and decisions live in the machine profile. Commands are
tier A unless marked **B**. The owning app must not be running when its caches
go. On a live desktop session (someone at the console, or agents driving a
browser), skip the caches of apps that are running and record the skip. Do not
quit them over ssh. Resolve a cache's owner by bundle id, not by its name:
`mdfind "kMDItemCFBundleIdentifier == 'com.openai.codex'"` is ChatGPT.app, not a
"Codex" app.

## Find it

```bash
df -h /System/Volumes/Data                         # the Data volume is where user bytes live
diskutil apfs list | grep -E 'Container disk|Capacity|Name:|Role'   # all volumes share one container
diskutil info / | grep -iE 'purgeable|free space'
tmutil listlocalsnapshots /
du -sh ~/.[!.]* ~/* 2>/dev/null | sort -rh | head -30
du -sh ~/Library/* ~/Library/{Caches,Application\ Support,Containers,Group\ Containers}/* 2>/dev/null | sort -rh | head -40
# runaway logs and the crash loops that write them (thousands of runs + KeepAlive = loop)
find ~/Library/Logs ~/.[!.]*/logs -maxdepth 3 -type f -size +204800 2>/dev/null     # >100 MB (512-byte blocks)
for f in ~/Library/LaunchAgents/*.plist; do l=$(basename "$f" .plist); echo "$(launchctl print gui/$(id -u)/$l 2>/dev/null | awk '/^\truns =/{print $3}') $l"; done | sort -rn | head
```

- **Measure deltas in bytes:** `diskutil info / | sed -n 's/.*Container Free Space:.*(\([0-9]*\) Bytes).*/\1/p'`.
  `df -h` rounds to whole GiB and hides most single-step yields.
- **Over ssh the login shell is often zsh:** unmatched globs abort the line and
  `=` gets expanded. Send command blocks as `ssh host 'bash -s' <<'EOF' ... EOF`
  instead of quoted one-liners.
- **Busy checks:** never `pgrep -f` on macOS. It matches the process
  environment too, so `pgrep -f cargo` hits every process whose `PATH` holds
  `~/.cargo/bin`. Use `pgrep -x <name>` (process name) or
  `ps -axo command | grep '[n]ame'` (arguments only).

- `du` over ssh cannot read TCC-protected dirs (Mail, Messages, Photos,
  Safari, some Containers) unless the ssh daemon has Full Disk Access; missing
  sizes there are "unmeasured", not zero.
- Other users' homes need sudo. Estimate their share as Data used minus
  everything you measured, and say it is an estimate.
- `timeout` is not installed by default; `gtimeout` comes with coreutils.
- Non-interactive ssh shells lack Homebrew on PATH: use `/opt/homebrew/bin/brew`.

## "System Data" decoded

Settings lumps these into System Data; check each:

| Item | Where | Reclaim |
|---|---|---|
| Simulator runtimes | `/Library/Developer/CoreSimulator/{Images,Cryptex,Volumes}` (mounted as their own APFS disks) | `xcrun simctl runtime list`, then `xcrun simctl runtime delete <id>` for unused ones (**B** if the build needs that iOS version) |
| Simulator devices | `~/Library/Developer/CoreSimulator/Devices` | `xcrun simctl delete unavailable`; `xcrun simctl erase <udid>` / `erase all` is **B** (wipes the apps and state inside) |
| Local snapshots | APFS | `com.apple.TimeMachine.*`: `sudo tmutil thinlocalsnapshots / 999999999999 4`. `com.apple.os.update-*` belong to the OS updater: leave them; they go after the update completes or a reboot |
| Swap and sleep image | VM volume | reboot after the memory hog is gone |
| Other users | `/Users/<other>` | never touch; tell the owner |
| Caches and logs | `~/Library/Caches`, `~/Library/Logs`, `/Library/Caches` | see below |

## Usual suspects and their commands

| Area | Where | Reclaim | Bound |
|---|---|---|---|
| Xcode DerivedData | `~/Library/Developer/Xcode/DerivedData` | delete (Xcode closed) | launchd agent: delete items unused for 14d |
| Device support | `~/Library/Developer/Xcode/iOS DeviceSupport/*` | keep only versions of devices still connected | same agent |
| Archives | `~/Library/Developer/Xcode/Archives` | **B** (keep shipped builds with dSYMs you may need) | — |
| Xcode extras | `~/Library/Developer/Xcode/CodingAssistant`, `~/Library/Developer/XCPGDevices` | A when regenerable | — |
| CocoaPods | `~/Library/Caches/CocoaPods`, `~/.cocoapods/repos` | `pod cache clean --all` | — |
| Homebrew | `$(brew --cache)`, `/opt/homebrew/Caskroom`, old kegs | `brew cleanup -s --prune=all`; `brew autoremove` | `HOMEBREW_CLEANUP_MAX_AGE_DAYS`, `brew cleanup` in a weekly agent |
| Android | `~/Library/Android/sdk/{system-images,ndk,build-tools}`, `~/.android/avd`, `~/.gradle` | old NDKs and build-tools via `sdkmanager --uninstall`; AVD snapshots; `gradle --stop` then `~/.gradle/caches` | — |
| Flutter / Dart | `~/.pub-cache`, extra flutter SDK copies | `flutter pub cache clean` (**B** offline) | — |
| JS | `~/.npm`, `~/Library/pnpm`, `~/.local/share/pnpm`, `~/Library/Caches/Yarn`, `~/.bun` | `npm cache clean --force`, `pnpm store prune`, `yarn cache clean` | — |
| Python / uv | `~/.cache/uv`, `~/Library/Caches/pip` | `uv cache prune`, `pip cache purge` | — |
| Rust | `~/.rustup/toolchains`, `~/.cargo/registry`, `*/target` | `rustup toolchain list` and uninstall unused; sweep idle targets | — |
| Docker Desktop | `~/Library/Containers/com.docker.docker` (Docker.raw is sparse) | `docker system prune` while running; uninstall leftovers if Docker is gone | resource limit on disk image size |
| Electron apps | `~/Library/Application Support/<App>/{Cache,Code Cache,GPUCache,CachedData,Service Worker/CacheStorage}` | delete those subdirs with the app quit | — |
| Browsers | `~/Library/Caches/Google`, `.../Chrome/*/Service Worker`, old Chrome versions in the app bundle | clear caches; profile data is **B** | — |
| Claude desktop | `~/Library/Application Support/Claude/vm_bundles` | **B**: VM image for its sandbox; it is re-downloaded if removed | — |
| iOS backups | `~/Library/Application Support/MobileSync/Backup` | **B** | — |
| Messages / Mail / Photos | `~/Library/Messages/Attachments`, `~/Library/Mail`, `~/Pictures/*.photoslibrary` | **B** or **C**, never from a script | — |
| Installers | `~/Downloads/*.{dmg,pkg,zip}`, updater caches | A when the app is verifiably installed (`ls -d /Applications/<App>.app`, `command -v`); otherwise **B** | — |
| Duplicate app copies | `~/Desktop/<App> 2.app` etc. | A after `diff -rq`, keep one. Finder duplicates are APFS clones, so expect little back | — |
| Trash | `~/.Trash` | A only for items trashed >30 days ago, and installer junk. The trash date is the item's **ctime** (`stat -f '%Sc'`); mtime keeps the original date and `mdls kMDItemDateAdded` is often `(null)`. Fresh items are **B** | Finder "Remove items from the Trash after 30 days" (`FXRemoveOldTrashItems`). It deletes later what the owner trashed now, so ask first |
| CI runner | `~/actions-runner/_work`, `_diag` | only between jobs (`pgrep -x Runner.Worker`), re-checked right before each `rm` | prune `_diag` and idle `_work` entries on a schedule |
| Crash-loop logs | `~/Library/Logs/*`, `~/.<tool>/logs/*`, a plist's `StandardErrorPath` | `: > file` (never `rm` a log a process holds) | retire the looping agent (below); truncate logs >100M in a weekly agent |

## Bounding on macOS

No systemd here. The equivalents:

- **launchd user agent** in `~/Library/LaunchAgents/<label>.plist` with
  `StartCalendarInterval`, running a script that lives in a git repo. Load with
  `launchctl bootstrap gui/$(id -u) <plist>` (or `launchctl load` on older
  releases); check with `launchctl print gui/$(id -u)/<label>`. Over ssh,
  bootstrapping into `gui/<uid>` works while that user is logged in at the
  console (`stat -f %Su /dev/console`; verified on macOS 26). Otherwise use
  `user/<uid>`. `bootout` followed immediately by `bootstrap` can fail with
  "5: Input/output error", so retry for a few seconds. Prove a calendar agent
  fires with `launchctl kickstart -p gui/<uid>/<label>` and read its log. `runs`
  resets to 0 on every re-bootstrap. Worked example with an installer:
  `~/code/infra/hosts/carries-macbook-air/` (`disk-maintenance.sh`, plist, `install.sh`).
  **launchd starts the job in `/`, which is read-only on macOS**: `cd "$HOME"` at
  the top of the script (or set `WorkingDirectory`). Otherwise tools that drop a
  temp file into their cwd fail (`pnpm store prune` gave `EROFS ... open
  '/_tmp_...'` while the agent still exited 0). Log each command's exit code,
  and test with `cd / && env -i HOME=$HOME PATH=<agent PATH> <cmd>`, not from an
  ssh shell that starts in `$HOME`.
- **Retiring a looping or obsolete agent:** `launchctl bootout gui/<uid>/<label>`
  and move the plist to `~/Library/LaunchAgents.attic/` with a README of restore
  commands. `bootout` alone lasts only until the next login when the plist has
  `RunAtLoad`. Old scripts that call Intel Homebrew paths (`/usr/local/bin/*`)
  fail on Apple Silicon, and under `KeepAlive` that becomes a crash loop.
- **newsyslog** (`/etc/newsyslog.d/*.conf`, needs sudo) for log rotation, or
  rotate in the same launchd script for user logs.
- Finder's 30-day trash auto-empty.
- `periodic` daily scripts (sudo) for system-level jobs.
