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
  from, a cache a daemon holds a lock on: skip it or stop its owner first.

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
   weekly rotation on a chatty host, journald without `SystemMaxUse`.
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

1. The writer's own knob: log size and keep count, retention days, `auto_prune`,
   `cleanupPeriodDays`, `EXECUTIONS_DATA_PRUNE`, docker `log-opts`.
2. Rotation: logrotate (Linux, with its own state file for user-level configs)
   or newsyslog (macOS). Use `copytruncate` when the writer holds the file open
   with O_APPEND.
3. Age rules: systemd-tmpfiles (`e <dir> - - - 7d`, `x` to protect live paths)
   or a launchd agent running `find -mtime`.
4. A scheduled prune script with a dry-run mode and an alert on failure.

Then add a **loud early warning** if the machine has monitoring: absolute
threshold (under 15% free) plus a trend (`predict_linear`, fills within 7 days).
The cheapest emergency is the one you hear about a week ahead.
