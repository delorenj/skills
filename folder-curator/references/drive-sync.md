---
pipeline-status: new
---
# Drive sync — inbound pull + outbound share

Two **independent one-way** rclone syncs against the `automaticai:` remote (a
`type = drive` remote; confirmed in `~/.config/rclone/rclone.conf`). Never run
`bisync` — the repo is a git working tree (see §4). The repo
(`/home/delorenj/code/AutomaticAI/Prospects/JamesBrennan`) is local NVMe
(`/dev/nvme0n1p2`, ext4), **not** a Drive mount, so these are plain host↔Drive copies.

## 1. Inbound — client uploads → repo

`sync-jim-dropbox-from-drive.sh` on a ~5–15 min timer. `rclone copy` (not `sync`)
so it only ever **adds** to `client_dropbox/`, never deletes local files. After the
copy it announces each NEW file on Bloodbank — this is the announce producer the
automation runbook drains.

```bash
#!/bin/bash
# sync-jim-dropbox-from-drive.sh — pull Jim's shared-Drive uploads, then announce.
set -euo pipefail
REPO="/home/delorenj/code/AutomaticAI/Prospects/JamesBrennan"
DROPBOX="$REPO/client_dropbox"
LEDGER="$REPO/.curator/ledger.json"
SRC="automaticai:<JimSharedFolder>"     # <placeholder> — fill with the real shared folder path

pidof -o %PPID -x "$0" >/dev/null && { echo "already running"; exit 0; }

rclone copy "$SRC" "$DROPBOX" \
  --fast-list --transfers=4 --checkers=8 \
  --log-file="$HOME/.local/state/rclone/rclone-jim-dropbox.log" --log-level=INFO

# Announce: one curator.file.received per file whose content-hash is not in the ledger.
for f in "$DROPBOX"/*; do
  [ -f "$f" ] || continue
  h=$(sha256sum "$f" | cut -d' ' -f1)
  grep -q "\"$h\"" "$LEDGER" 2>/dev/null && continue        # already known → skip
  printf '{"id":"%s","file_path":"%s","file_name":"%s","file_hash_sha256":"%s"}' \
    "$h" "$f" "$(basename "$f")" "$h" \
  | bb-emit --type bloodbank.v1.curator.file.received \
            --source urn:33god:cli:sync-jim-dropbox \
            --producer operator:jarad --service folder-curator
done

folder-curator --client-root "$REPO" reindex        # §3
```

`data.id = sha256` keeps the event's `correlationid` stable across the file's
lifecycle. The ledger grep is the coarse announce gate; folder-curator `apply` is the
authoritative content-hash dedup. Consequence: a file routed out of `client_dropbox/`
may be re-downloaded here on the next pull, but its hash is in the ledger, so the
announce skips it and it stays a no-op. `<JimSharedFolder>` is a placeholder the user
must set to the actual shared Drive folder path.

## 2. Outbound — repo → shareable Drive (content-only)

`sync-client-to-drive.sh` on a systemd user timer, modeled on
`~/.config/zshyzsh/scripts/sync-automaticai-to-company-drive.sh`. `rclone copy -L`
(`-L` follows the repo's symlinks — e.g. `CLAUDE.md`→`AGENTS.md` — copying content).

```bash
REPO="/home/delorenj/code/AutomaticAI/Prospects/JamesBrennan"
SHARE="automaticai:<share>"             # <placeholder> — destination shared folder

rclone copy -L "$REPO" "$SHARE" \
  --fast-list --transfers=8 --checkers=8 --drive-chunk-size=32M \
  --exclude ".*" \
  --exclude ".*/**" \
  --exclude "_bmad/**"       --exclude "_bmad" \
  --exclude "_skf/**"        --exclude "_skf" \
  --exclude "_skf-learn/**"  --exclude "_skf-learn" \
  --exclude "worktrees/**"   --exclude "worktrees" \
  --exclude "node_modules/**" --exclude "node_modules" \
  --exclude "__pycache__/**" \
  --exclude "target/**" \
  --exclude "**/*.sync-conflict-*" \
  --log-file="$HOME/.local/state/rclone/rclone-jim.log" --log-level=INFO
```

**The exclude set, explained:**

- `--exclude ".*" --exclude ".*/**"` drops **all** dotfiles/dotdirs in one stroke:
  `.git`, `.github`, every agent dot-dir (`.claude .agent .agents .bob .cline
  .codebuddy .adal .opencode .qwen .trae …`), `.mise`, `.worktrees`,
  `.project.json`, `.copier-answers.yml`, `.env`, `.env.op`, and `.curator`
  (quarantine — see §5). This pair **subsumes every dot-cache the model script lists
  individually** (`.venv .next .turbo .pytest_cache .mypy_cache .ruff_cache
  .obsidian`), so only NON-dot noise needs explicit excludes below.
- Non-dot noise (has no leading dot, so not caught above): `_bmad`, `_skf`,
  `_skf-learn`, `node_modules`, `__pycache__`, `target`, `worktrees/`,
  `*.sync-conflict-*`.
- **Decision — `_bmad-output/` is INCLUDED.** It holds client deliverables, so it
  syncs. Only `_bmad/` scaffolding is excluded. The `_bmad` glob does not match
  `_bmad-output` (distinct names), so dropping the model script's
  `_bmad-output` exclude cleanly separates the two.

## 3. mtime restore after sync

rclone preserves source mtimes, so an inbound `copy` stamps local files with the
Drive source's mtime — which desyncs `ls -lt`/`llr` from each file's `updated`
frontmatter and reorders `_context-stack.md`. Run `folder-curator reindex`
after the pull (shown in §1) to re-stamp every indexed file's mtime from its
`updated` and regenerate the stack. Outbound `copy` (repo→Drive) does not touch
local mtimes, but running `reindex` there too is a harmless idempotent safeguard.

## 4. Scheduling

systemd **user** timers, modeled on the existing `sync-automaticai.service`/`.timer`
(hourly) — and note the vault sync runs on both `sync-vault.service`/`.timer` and a
cron entry (`30 */2 * * * /home/delorenj/.local/bin/sync-vault-to-drive`) as further
precedent. Inbound wants a tighter cadence than outbound.

```ini
# ~/.config/systemd/user/sync-jim-dropbox.service      (inbound)
[Unit]
Description=Pull Jim's Drive uploads into client_dropbox + announce
Wants=network-online.target
After=network-online.target
[Service]
Type=oneshot
ExecStart=%h/.config/zshyzsh/scripts/sync-jim-dropbox-from-drive.sh
Nice=10
IOSchedulingClass=idle
TimeoutStartSec=15min
[Install]
WantedBy=default.target
```
```ini
# ~/.config/systemd/user/sync-jim-dropbox.timer        (inbound — every 10 min)
[Timer]
OnBootSec=5min
OnUnitActiveSec=10min
Persistent=true
RandomizedDelaySec=2min
Unit=sync-jim-dropbox.service
[Install]
WantedBy=timers.target
```

Outbound reuses the same shape: a `sync-client-to-drive.service` (oneshot →
`sync-client-to-drive.sh`) plus a `.timer` with `OnUnitActiveSec=1h` (match
`sync-automaticai.timer`). Enable with
`systemctl --user enable --now sync-jim-dropbox.timer sync-client-to-drive.timer`.

**One-way push/pull only — bisync is intentionally NOT used.** The repo is
git-tracked; a bidirectional sync against a working tree spawns `*.sync-conflict-*`
files and fights git's own history. Inbound is an additive pull of client uploads;
outbound is a content-only push to a shareable mirror. The two never cross.

## 5. Safety

- **Never sync `.curator/quarantine/`.** It holds quarantined secrets and is covered
  by the `--exclude ".*" --exclude ".*/**"` dot-dir rule (`.curator` is a dotdir) — so
  quarantined credentials never leave the repo. Restated because it is load-bearing:
  a secret that reaches Drive is a leak.
- **`.env` / `.env.op` never sync** — same dot-exclude. Do not add a re-include for
  either.
- **Repo is local NVMe, not a Drive mount** (`findmnt`/`df` confirm `/dev/nvme0n1p2
  ext4`). These syncs are ordinary host↔Drive copies; there is no mount loop to
  guard against.
