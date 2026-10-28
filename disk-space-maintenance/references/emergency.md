# Emergency: under ~3% free, or writes failing

Goal: **10-20% headroom in minutes, with zero risk**, so shells, package managers,
databases and the survey itself work again. Do the full workflow afterwards.

Rules for this mode:

- Only tier A. Nothing that needs a decision. Nothing that needs a working build tool.
- Check first that something running isn't actively filling the disk; if it is,
  stop it (`lsof +L1`, the "written in the last 48h" list, `iotop`, `fs_usage` on macOS).
- One command at a time, `df -h` after each, stop as soon as there is headroom.

## Linux, fastest safe wins

```bash
df -h /; sudo -n true && echo sudo-ok
# 1. Deleted-but-open files: often gigabytes, free in one second
sudo lsof -nP +L1 | awk '$7>104857600'        # truncate via /proc/<pid>/fd/<n>: sudo truncate -s0 /proc/PID/fd/N
# 2. Docker build cache and dangling images (always rebuildable)
docker builder prune -af; docker image prune -f
# 3. Journal and rotated logs
sudo journalctl --vacuum-size=500M
sudo find /var/log -type f \( -name '*.gz' -o -name '*.[0-9]' \) -delete
# 4. Package manager caches
sudo apt-get clean            # or: dnf clean all / pacman -Sc
uv cache prune 2>/dev/null; npm cache clean --force 2>/dev/null; pnpm store prune 2>/dev/null
# 5. Trash and temp older than a day
rm -rf ~/.local/share/Trash/files/* ~/.local/share/Trash/info/*   # only if the owner already threw it away
/usr/bin/find /tmp "${TMPDIR:-/tmp}" -xdev -mindepth 1 -mtime +1 -delete 2>/dev/null
```

If the disk is so full that `apt`/`docker` themselves fail, start with step 1 and
`journalctl --vacuum-size`, which need no free space.

## macOS, fastest safe wins

```bash
df -h /System/Volumes/Data; tmutil listlocalsnapshots /
# 0. Runaway logs: truncate in place (the writer keeps its fd). Then stop the loop that wrote them (macos.md, "Retiring")
find ~/Library/Logs ~/.[!.]*/logs -maxdepth 3 -type f -size +204800 2>/dev/null    # >100 MB; then : > <file>
# 1. Xcode build products and simulator junk (Xcode not running)
rm -rf ~/Library/Developer/Xcode/DerivedData/*
xcrun simctl delete unavailable
xcrun simctl runtime delete --notUsedSinceDays 30 2>/dev/null   # runtimes not used recently (Xcode 15+)
# 2. Per-run build dirs and CI runner workspaces older than a week (pgrep -x Runner.Worker must be empty)
# 3. User caches (apps rebuild them; skip apps that are running)
du -sh ~/Library/Caches/* | sort -rh | head      # then rm -rf the biggest caches of apps NOT running
# 4. Package managers
/opt/homebrew/bin/brew cleanup -s --prune=all 2>/dev/null
pnpm store prune 2>/dev/null; npm cache clean --force 2>/dev/null; uv cache prune 2>/dev/null
# 5. Time Machine local snapshots (needs sudo; os.update snapshots are system-managed: leave them)
sudo tmutil thinlocalsnapshots / 999999999999 4
# 6. Trash: only installer junk and items trashed >30 days ago (ctime = trash date). Fresh trash is the owner's call
```

On carries-macbook-air, steps 0 and 2 alone bought 20 GiB (crash-loop logs 2.7,
tower run dirs 10.7, runner `_work` 6.5) without touching anything anyone was using.

When "System Data" is huge in Settings and none of this moves it, the space is
usually simulator runtimes (`/Library/Developer/CoreSimulator`), local snapshots,
swap in the VM volume, or another user's account. See [macos.md](macos.md).

After headroom is back: return to step 1 of the main workflow. The emergency was
caused by an accumulator, and it is still running.
