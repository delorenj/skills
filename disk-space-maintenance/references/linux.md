# Linux playbook (generic)

Machine-specific paths and decisions live in the machine profile; this is the
catalogue to fall back on. Commands are tier A unless marked **B**.

## Find it

```bash
df -hT -x tmpfs -x overlay; df -i /                    # inodes run out too
gdu -n -x -p -o /tmp/home.json /home                   # fast whole-tree export (~1 min for 2 TiB)
sudo du -xh --max-depth=2 / 2>/dev/null | sort -rh | head -40
sudo lsof -nP +L1 | awk '$7>104857600'                 # deleted but open
/usr/bin/find / -xdev -type f -mmin -1440 -size +200M -printf '%s %p\n' | sort -rn | head
```

In interactive zsh, `find` may be a function or alias (bfs on big-chungus); call
`/usr/bin/find`. For a big gdu export, stream it (ijson) instead of `json.load`.

## Usual suspects and their commands

| Area | Where | Reclaim | Bound |
|---|---|---|---|
| Docker build cache | `/var/lib/docker` | `docker builder prune -af` | weekly `docker builder prune --filter until=168h` |
| Docker images | | `docker image prune -af --filter until=168h` (keep locally built images a compose file names) | scheduled prune |
| Docker anonymous volumes | 64-hex names, unattached | `docker volume ls -qf dangling=true` and keep only 64-hex names | never named volumes |
| Container logs | `/var/lib/docker/containers/*/*-json.log` | truncate | `daemon.json` `log-opts: max-size 50m, max-file 3` (new containers only) |
| journald | `/var/log/journal` | `journalctl --vacuum-size=1G` | `journald.conf.d`: `SystemMaxUse=1G`, `MaxRetentionSec=3week` |
| syslog | `/var/log/syslog*` | delete rotated | logrotate daily + `maxsize`; drop chatty sources in rsyslog |
| User logs | `~/.local/state`, `~/.pm2`, `~/.cache/*/log*`, app dirs | `: > file` if held open | user logrotate (own state file, fired by a Candybar), copytruncate |
| apt / snap | `/var/cache/apt`, `/var/lib/snapd/snaps` | `apt-get clean`; remove disabled snap revisions | `APT::Keep-Downloaded-Packages "false"`; `snap set system refresh.retain=2` |
| Old kernels | `/boot`, `/usr/lib/modules` | **B** `apt autoremove --purge` (keep running + one) | — |
| uv / pip | `~/.cache/uv`, `~/.cache/pip` | `uv cache prune` (`--force` only after stopping lock holders) | weekly prune |
| npm / pnpm / bun / yarn | `~/.npm`, `~/.local/share/pnpm`, `~/.bun/install/cache` | `npm cache clean --force`, `pnpm store prune`, `bun pm cache rm` | weekly prune |
| Rust | `~/.cargo/registry`, `~/.rustup/toolchains`, `*/target` | `cargo cache -a` (cargo-cache), remove unused toolchains, sweep idle `target/` | never `cargo clean` a target a service runs from |
| Go | `~/.cache/go-build`, `~/go/pkg/mod` | `go clean -cache` (`-modcache` is **B** offline) | — |
| Gradle / Maven | `~/.gradle/caches`, `~/.m2` | `gradle --stop`, then delete `caches/` (or old versions only) | — |
| Toolchain managers | `~/.local/share/mise/installs` | **B**, version by version, after checking shebangs and pins | never `mise prune` blind |
| HuggingFace | `~/.cache/huggingface/hub` | **B**: `huggingface-cli scan-cache` / `delete-cache`; keep what services load | — |
| Temp | `/tmp`, custom `$TMPDIR` | age sweep | systemd-tmpfiles `e <dir> - - - 7d`, with `x` lines for sockets and live dirs |
| Trash | `~/.local/share/Trash` | items whose `.trashinfo` `DeletionDate` is over 14 days old | scheduled expiry |
| CI runners | `actions-runner*/_work` | only between jobs | prune after N days idle |
| Android | `~/.android/avd/*/snapshots`, SDK system images | **B** for AVDs; snapshots are A when the emulator is off | — |
| SQLite state | app `.sqlite`/`.db` | `VACUUM` while the writer is idle; delete old rows by the app's rule | app retention + `auto_vacuum=INCREMENTAL` |

## Bounding patterns that worked (big-chungus, 2026-10)

- A user-level logrotate: `logrotate -s ~/.local/state/user-logrotate/status <conf>`
  from a daily systemd user timer, with the config generated in part at run time
  so new repos' log dirs are picked up automatically.
- An age sweep script with a RULES table (glob, age, delete-or-gzip) for
  one-file-per-run logs that no rotation knob covers.
- A daily state-maintain job: retention DELETEs plus `VACUUM` for SQLite stores.
- Daily docker prune plus weekly cache prune, each with `--dry-run` and an
  `OnFailure=` alert unit.
- systemd-tmpfiles user rules on the custom `TMPDIR`, with tighter 2-day clocks
  for `go-build*`, `pytest-of-*`, `tmp.*`.
