---
pipeline-status: new
---
# scheduling — nightly / weekly / reactive

Read when wiring the cadences to run unattended. Two execution tiers:

- **Deterministic** (tune-up sweep, reap, consolidate loop) → plain systemd/cron, no agent.
- **Agentic** (optimization prune review, cross-bank pollination, novel synthesis, karpathy Ingest)
  → a headless agent invocation, because they need judgment. Schedule these as `claude -p` runs of
  this skill, or run them interactively.

This host schedules with **user systemd units** (see `~/docker/systemd/` and `~/docker/scripts/*.service`).
Prefer that over crontab for logging/`systemctl status`.

## Cadence map

| Cadence | Deterministic (systemd) | Agentic (headless `claude -p`) |
|---|---|---|
| nightly | `tune-up.sh` → reap if orphans → `consolidate` working set | karpathy-wiki of new memories |
| weekly | (none) | optimization: prune review → pollination → synthesis; karpathy Lint |
| reactive | reap after container recreate; ad-hoc sweep | on-demand run of any single workflow |

## Nightly deterministic wrapper

Drop this at `~/docker/stacks/ai/hindsight/maint-nightly.sh` (chmod +x):

```bash
#!/usr/bin/env bash
set -uo pipefail
SKILL_DIR="$HOME/.claude/skills/hindsight-maintenance"
source "$SKILL_DIR/scripts/hs-lib.sh"

REPORT="$("$SKILL_DIR/scripts/tune-up.sh")"; echo "sweep: $REPORT"

# Reap only if orphans exist and the container is up (the script self-guards both).
"$SKILL_DIR/scripts/reap-orphans.sh" --apply || true

# Consolidate banks with a real unconsolidated backlog (cap the fan-out).
hs_db "SELECT bank_id FROM ${HS_SCHEMA}.memory_units
       WHERE consolidated_at IS NULL AND consolidation_failed_at IS NULL
         AND fact_type IN ('experience','world')
       GROUP BY 1 HAVING count(*) >= 20 ORDER BY count(*) DESC LIMIT 20;" \
  | while read -r b; do [ -n "$b" ] && hindsight bank consolidate "$b"; done
```

### systemd user units

`~/.config/systemd/user/hindsight-maint-nightly.service`:
```ini
[Unit]
Description=Hindsight nightly memory maintenance (deterministic)
After=network-online.target

[Service]
Type=oneshot
ExecStart=%h/docker/stacks/ai/hindsight/maint-nightly.sh
```

`~/.config/systemd/user/hindsight-maint-nightly.timer`:
```ini
[Unit]
Description=Run Hindsight nightly maintenance at 03:30

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable: `systemctl --user daemon-reload && systemctl --user enable --now hindsight-maint-nightly.timer`
(`loginctl enable-linger $USER` so it runs while logged out). Check: `systemctl --user list-timers | grep hindsight`.

## Agentic runs (headless)

The wiki, prune, pollination, and synthesis passes want an agent. Schedule them by pointing headless
Claude Code at this skill — a second service/timer (e.g. `03:50` nightly for the wiki, `Sun 04:30` weekly):

```ini
ExecStart=/usr/bin/zsh -lc 'cd %h/docker && claude -p "Run the hindsight-maintenance nightly karpathy-wiki workflow across all banks with new memories, then stop." --dangerously-skip-permissions'
```

For weekly, swap the prompt to "Run the hindsight-maintenance weekly optimization workflow: consolidate,
prune review (report candidates, do not delete without confirmation), cross-bank pollination, novel
synthesis." Note the prune step will surface candidates but a fully-unattended run must NOT delete —
keep deletion interactive, or have the agent only *report* prune candidates into `infra`.

## Reactive triggers

- **After `docker compose up -d --force-recreate`** (the orphan-maker): immediately run
  `~/.claude/skills/hindsight-maintenance/scripts/reap-orphans.sh --apply`. Wire it as a wrapper
  around your recreate command, or a `docker compose` post-up step, so orphans never accumulate.
- **Stuck-queue alert** (pending backlog with an idle worker): run `scripts/tune-up.sh`, then reap.
- **On demand**: `claude -p "Run the hindsight-maintenance <tune-up|optimization|karpathy-wiki> workflow."`
