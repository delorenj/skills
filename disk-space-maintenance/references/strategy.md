# Strategy: measuring, classifying, and making it stick

## The tier model

| Class | Meaning | Examples | Action |
|---|---|---|---|
| **A** | Rebuildable or worthless; regenerates on demand | package caches, build output, DerivedData, simulator caches, docker build cache, dangling images, rotated logs, crash dumps, trash older than N days, old installer/updater downloads | delete without asking, measure |
| **B** | Has value only the owner can judge | media and recordings, downloads, VM images, old repos and worktrees, backups beyond retention, installed apps and games, model weights, AVDs and simulators someone may use, app data (chat, notes) | ask once, as a table |
| **C** | Never | another user's home, the newest copy of any backup, unpushed git work, live databases and volumes, secrets and keychains, OS-managed snapshots and volumes, anything a running service reads | leave it; mention it if it is big |

Rules that keep the tiers honest:

- **Unknown means B.** "Looks like a cache" is not enough; find who writes it.
- **A git repo is B or C until proven pushed.** Check `git status --porcelain`,
  `git stash list` and `git log @{u}..` (or no upstream). A clean, pushed clone
  of something not in use is A only for its build dirs and B as a whole.
- **"Not touched in N days" is a hint, not a verdict.** Toolchains, interpreters
  and runtimes look idle and break everything when removed (big-chungus:
  `mise prune` removed python versions that pipx/uv tools and `~/.local/bin`
  shebangs depended on).
- **In-use beats idle.** A file held open (`lsof`), a target dir a service runs
  from, a cache a daemon holds a lock on: skip it or stop its owner first. On a
  live desktop session an app that is running is in use: skip its cache and
  record the skip; don't quit someone's apps over ssh.
- **Preconditions go stale in minutes.** Check "no CI job / no build running"
  immediately before each `rm`, not once at the start (a runner picked up a
  job five minutes into the carries-macbook-air run). Defer blocked steps to the
  end of the run and retry them; don't drop them.
- **Fresh trash is not junk.** Only items trashed more than ~30 days ago are A;
  anything the owner threw away this week is still their decision.
- **A cleaner aimed at an unverified path is a hazard.** `rm -rf ~/link/dir/*`
  on a dangling symlink is a no-op until someone repoints the link, then it wipes
  the real target (a 2-minute cron did exactly this shape against a synced Google
  Drive folder). Before you "fix" a dangling path, find every job that deletes
  under it.

## Acting on tier-B answers

Once the owner has answered, three patterns keep the execution safe.

**Archive, verify, then delete (media and anything with no other copy).**
1. Pull to the machine that has the room, keeping relative names:
   `rsync -a --partial --files-from=<list> -e "ssh -o BatchMode=yes" host:/Users/x/ dest/`
   (a list file copes with spaces in names; run it in the background, a
   multi-GB pull over tailscale takes tens of minutes).
2. Hash **every file on both sides** (`shasum -a 256` / `sha256sum`), diff the two
   manifests by path, and delete only the items whose every file matches. One
   mismatch means that item stays. Symlinks are skipped by `sha256sum` on a
   regular-files list; check them with `find -type l`.
3. Duplicates: prove "identical" by checksum, not by name, then archive once.
4. Delete on the source with the measure-before/after wrapper, and re-list the
   destination afterwards.

**Live data location check (before deleting any "personal folder").** A folder
the owner calls loose may be an app's working directory. Archive it, leave it
in place and report it when any of these is true:
- a **sync tool** manages it (a `.stfolder` marker does not prove it: read the
  tool's config, `~/Library/Application Support/Syncthing/config.xml` or
  `~/.config/syncthing`, for `<folder path=...>`, `type=` and `ignoreDelete`).
  A `sendreceive` folder with `ignoreDelete=false` propagates the deletion to
  every peer, so an "archive and delete locally" is really "delete everywhere";
  a stale `.stfolder` in a folder the config no longer lists is harmless;
- the installed app's **default data location** is that folder (Splice's
  `~/Splice` with its `.splice` marker) or its prefs (`defaults read`,
  `plutil -p`, app `reg.xml`/`*Prefs.json`) name it;
- another folder symlinks into it (`find ~/Documents ~/Library -maxdepth 3 -type l`).
Finder sidebars and "last open dialog" bookmarks are not configuration.

**Admin-only leftovers: hand off, never escalate.** An agent without sudo
removes everything it has write permission for (a `[ -w ]` walk over the tree
tells you before you delete: an app bundle whose directories are all root-owned
cannot be partly removed, and a half-deleted bundle is worse than none), then
writes one commented, idempotent, copy-pasteable script with the sizes, commits
it in the infra repo and reports the path. Do not try `sudo`, `osascript` admin
prompts or Finder trashing to get around it. Content dirs that are group-writable
can be emptied even when the dir itself (and the app that owns it) cannot be
removed: say which shells are left in the script.

## Measurement traps

| Trap | What happens | Do instead |
|---|---|---|
| Hardlinked caches (uv, pnpm, bun, cargo, nix) | `du` shows the cache at full size; deleting it frees only the bytes not linked into a live venv or node_modules | Expect 30-60% of the shown size; trust `df` before and after |
| Docker "RECLAIMABLE" | Counts shared layers per image, so it overstates | Measure `df` around the prune |
| Deleted but open | `rm` on a log a process holds frees nothing; `df` and `du` disagree | `lsof +L1`; truncate in place (`: > file`) or restart the holder |
| APFS purgeable and snapshots (macOS) | Finder counts purgeable as free and `df` does not; local snapshots pin deleted blocks | Read `diskutil info /` and `tmutil listlocalsnapshots /`; deleted space can stay pinned until a snapshot thins |
| Sparse images (VM disks, Docker.raw, simulator images, qcow2) | `ls -l` shows the ceiling, not the use | Use `du -sk` (allocated), never `ls` |
| G vs GiB, and Prometheus vs df | Different tools disagree by about 7% and by reserved blocks | Pick one unit per report and say which |
| Concurrent cleaners | Two sessions pruning at once collide on locks (uv) and double-count wins | Check for another active cleanup first; attribute only your own deltas |
| Root-owned files in user caches | `rm` and `uv cache prune` fail partway | Find them (`find ~/.cache -user root`), chown with sudo, then prune |
| Compression is not deletion | zstd-compressed transcripts stop being resumable by their app | Compress only data nothing reads live; say so |

## Pile vs accumulator

A **pile** is bytes already on disk. An **accumulator** is the thing that keeps
writing them. Each cleanup should end with a two-column list:

| Accumulator | Bound now |
|---|---|
| e.g. syslog at 430 MB/day, weekly rotation | daily + maxsize 400M, keep 3 |

Typical accumulators, roughly in order of how often they bite:

1. **Logs without rotation**: app logs under `$HOME`, systemd `StandardOutput=append:`
   files (systemd cannot cap them), pm2, per-run logs nobody deletes, syslog with
   weekly rotation on a chatty host, journald without `SystemMaxUse`. Worst case:
   a **crash-looping service** (launchd `KeepAlive`, systemd `Restart=always`)
   whose stdout/stderr go to a file. One that restarted every 10 s with `set -x`
   wrote 1.9 GiB in a month. Restart counts give it away (`launchctl print ... runs`,
   `systemctl show -p NRestarts`).
2. **Package and tool caches**: uv, pip, npm, pnpm, bun, cargo, go, gradle, maven,
   CocoaPods, Homebrew, mise or asdf versions, HuggingFace models.
3. **Build output**: Rust `target/`, `node_modules`, `.venv`, Xcode DerivedData,
   Gradle build dirs, CI runner `_work`, release staging and outboxes.
4. **Container images and build cache**: docker build cache (305 GB on
   big-chungus once), old tags, anonymous volumes.
5. **State databases with no retention or vacuum**: SQLite event stores, agent
   session DBs, n8n executions, hook receipts. SQLite never shrinks without `VACUUM`.
6. **Temp dirs that nothing cleans**: a custom `TMPDIR`, test `mkdtemp` leaks,
   headless browser profiles killed with SIGKILL.
7. **Updaters and installers**: each downloaded release kept forever (`.dmg`,
   `.deb`, app version dirs).
8. **Backups and dumps** kept locally when a deduplicating backup already has them.
9. **Agent transcripts and session stores**: big, append-only, rarely re-read.

## Choosing a bound

Order of preference, closest to the source first:

0. **Stop a writer that does nothing useful.** A crash loop or a client of a
   retired service is fixed by retiring it reversibly: unload it, move its unit
   or plist into an attic dir with a restore note, then truncate its log.
   Rotating a crash loop's log treats the symptom.
1. The writer's own knob: log size and keep count, retention days, `auto_prune`,
   `cleanupPeriodDays`, `EXECUTIONS_DATA_PRUNE`, docker `log-opts`. For per-run
   build dirs, prune at the start of the next run in the tool that creates them
   (age limit plus "keep newest N", so resume/rollback still works).
2. Rotation: logrotate (Linux, with its own state file for user-level configs)
   or newsyslog (macOS). Use `copytruncate` when the writer holds the file open
   with O_APPEND.
3. Age rules: systemd-tmpfiles (`e <dir> - - - 7d`, `x` to protect live paths)
   or a launchd agent running `find -mtime`.
4. A scheduled prune script with a dry-run mode and an alert on failure. On Linux the scheduler is a Candybar (`candybar` skill), not a new timer or cron line.

Then add a **loud early warning** if the machine has monitoring: absolute
threshold (under 15% free) plus a trend (`predict_linear`, fills within 7 days).
The cheapest emergency is the one you hear about a week ahead.
