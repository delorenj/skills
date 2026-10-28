# macOS playbook (generic)

Machine-specific paths and decisions live in the machine profile. Commands are
tier A unless marked **B**. Quit the owning app before deleting its caches.

## Find it

```bash
df -h /System/Volumes/Data                         # the Data volume is where user bytes live
diskutil apfs list | grep -E 'Container disk|Capacity|Name:|Role'   # all volumes share one container
diskutil info / | grep -iE 'purgeable|free space'
tmutil listlocalsnapshots /
du -sh ~/.[!.]* ~/* 2>/dev/null | sort -rh | head -30
du -sh ~/Library/* ~/Library/{Caches,Application\ Support,Containers,Group\ Containers}/* 2>/dev/null | sort -rh | head -40
```

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
| Simulator devices | `~/Library/Developer/CoreSimulator/Devices` | `xcrun simctl delete unavailable`; `xcrun simctl erase all` is **B** |
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
| Installers | `~/Downloads/*.{dmg,pkg,zip}`, updater caches | A when the app is already installed; otherwise **B** | — |
| Trash | `~/.Trash` | empty | Finder "Remove items from the Trash after 30 days" |
| CI runner | `~/actions-runner/_work`, `_diag` | only between jobs (`ps` for `Runner.Worker`) | prune `_diag` and old `_work` dirs on a schedule |

## Bounding on macOS

No systemd here. The equivalents:

- **launchd user agent** in `~/Library/LaunchAgents/<label>.plist` with
  `StartCalendarInterval`, running a script that lives in a git repo. Load with
  `launchctl bootstrap gui/$(id -u) <plist>` (or `launchctl load` on older
  releases); check with `launchctl print gui/$(id -u)/<label>`. Over ssh there
  is no GUI session: bootstrap into `gui/<uid>` only works while that user is
  logged in at the console; otherwise use `user/<uid>`.
- **newsyslog** (`/etc/newsyslog.d/*.conf`, needs sudo) for log rotation, or
  rotate in the same launchd script for user logs.
- Finder's 30-day trash auto-empty.
- `periodic` daily scripts (sudo) for system-level jobs.
