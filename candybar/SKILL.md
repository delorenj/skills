---
name: candybar
description: Candybar is the only way to schedule recurring or background work on this host. Use whenever a task says schedule, scheduled, cron, crontab, systemd timer, .timer, OnCalendar, recurring, periodic, nightly, hourly, daily, weekly, every N minutes, background job, poll loop, n8n Schedule Trigger, hermes cron create, cronjob tool, or migrate a cron job. Covers registering a candybar.toml, per-runner manifests, migrating a native clock through the ledger, exceptions and proof of done.
---

# Candybar: the single clock

The live docs outrank this skill. Before acting read `~/code/33GOD/candybar/README.md`
("Register a candybar", "Runner kinds", "Migrate a cron job onto candybar") and
`deploy/migration/README.md`. Policy text: `~/.agents/AGENTS.md`, "Recurring schedules".

## The one rule

Candybar owns WHEN recurring work runs. Never create a crontab entry, a new
systemd `.timer`, `systemd-run --on-*`, `at`/`batch`, a launchd interval, a Hermes
internal recurring job (`cronjob` tool, or `hermes cron create` without
`--scheduler external`), an n8n Schedule Trigger, or a private recurring
sleep/poll loop. Execution is free: a systemd `.service`, a Hermes job pinned
`scheduler=external`, an n8n webhook workflow or any exec argv. Candybar fires it.

Not schedules, so allowed: bounded retries and loops inside one invocation,
event-driven workers, and session-scoped waits (Claude Code CronCreate, `/loop`,
ScheduleWakeup, Kimi CronCreate). Those die with the session; never use them to
install durable recurring system work.

## Pick the runner

| Need | Runner | Notes |
|---|---|---|
| Script or any command | `exec` | Table form with absolute `argv`; metered; `on_failure` argv for alerts |
| Existing systemd service | `systemd` | Keep the `.service`, retire only its `.timer` |
| Hermes agent (LLM) job | `hermes` | Needs a Hermes job pinned `scheduler: external`; runner takes profile + hex job_id |
| Hermes `no_agent` script | `exec` | Run the script directly, not through `hermes` |
| n8n workflow | `n8n` | Webhook-triggered, active, responds on finish, zero Schedule Triggers |
| Faster than once a minute | none | Not schedulable. Use an event-driven worker, or loop inside one invocation, or ask the user for an exact exception record |

## Install a new job (no native clock exists)

Run from `~/code/33GOD/candybar`. API default `http://127.0.0.1:8700`; off-box
`export CANDYBAR_API_URL=https://candybar.delo.sh`.

1. Put the script or `.service` in its own repo, committed and pushed. Never add a `.timer`.
2. Write `candybar.toml` next to the job source. Required: `name` (lowercase slug), a 5-field `schedule`, and exactly one of `entrypoint` or `[candybar.runner]`. Optional: `description`, `tags`, `timezone` (IANA, default UTC), `noise`, `enabled`. Unknown keys are rejected.
3. For anything with side effects set `enabled = false`, then `uv run candybar register <dir-or-file>`. Register is create-only: duplicate name is 409. Later changes use `uv run candybar edit <name> [--schedule --timezone --description --tags --noise]`; a runner change needs `curl -X PATCH $API/candybars/<id> -H 'content-type: application/json' -d '{"runner":{...}}'`.
4. Read back: `uv run candybar show <name> -n 5` and `uv run candybar next`. Check state, runner, schedule, timezone.
5. Prove a terminal invocation: `uv run candybar run <name> --wait` for side-effect-free jobs. For jobs with side effects do not test-run; wait for the first scheduled fire and read `uv run candybar history <name> -n 5`. Then confirm the job's actual effect.
6. `uv run candybar resume <name>` to enable.
7. `uv run candybar doctor --repo . --live --json` (read-only). Confirm no new bypass and no competing native clock.
8. Commit and push the manifest.

## Minimal manifests

```toml
[candybar]                       # exec
name = "my-job"
schedule = "*/5 * * * *"
timezone = "America/New_York"
enabled = false
[candybar.runner]
kind = "exec"
argv = ["/abs/path/script.sh"]   # absolute or bare command
timeout_s = 600
# on_failure = ["ntfy-publish", "--topic", "alerts"]
```

```toml
[candybar.runner]                # systemd: the .service stays
kind = "systemd"
unit = "my-job.service"
```

```toml
[candybar.runner]                # hermes: job already pinned scheduler=external
kind = "hermes"
profile = "33god-pm"
job_id = "a1b2c3d4e5f6"
```

```toml
[candybar.runner]                # n8n: webhook workflow, no Schedule Trigger
kind = "n8n"
webhook = "candybar/nightly-digest"
```

New Hermes agent job (VERIFY FIRST, untested recipe): create it pinned external
so Hermes' own ticker is not a second clock, e.g.
`hermes -p <profile> cron create --scheduler external --paused '<schedule>' '<prompt>'`.
Check `hermes cron create --help` and read the job back before registering. A pin
on a running gateway may need `hermes-gateway-restart --reason`, never raw systemctl.

## Migrating an existing cron line or timer

The ledger is `deploy/migration/ledger.yaml`; one scheduler per job at every step.
1. Add a ledger entry (id like `systemd:foo.timer`, `crontab:N`, `hermes:<profile>:<job>`), `status: planned`.
2. Retire the re-enabler first: the owning repo's installer, mise task or README step must stop re-enabling the old clock. Commit and record it in `source_of_truth.commit`.
3. `uv run candybar migrate plan <id> --write`; commit the ledger.
4. `uv run candybar migrate cutover <id> [--wait 600]` (registers disabled, retires native, enables; auto-rolls back on failure).
5. `uv run candybar migrate verify <id>` (exit 3 until the first scheduled fire). Commit the ledger.
6. `migrate status [--probe]` to inspect; `migrate rollback <id>` to restore native; `migrate decommission <id> --reason '...'` to retire for good, then delete the job's old units and installers.

## Exceptions

The only standing exception is `candybar-watchdog.timer` (AD-22, a scheduler must
not watch itself). It does not exempt crank-watchdog or other agent schedules.
Any other exception is an exact entry in `deploy/scheduling-policy.json` that the
user approves with owner, scope and reason. Never self-grant one. Doctor findings
stay visible; do not auto-disable unfamiliar timers.

## Done means

Manifest committed and pushed; registration read back through the API; a terminal
invocation and its intended effect proven; competing native clocks off; doctor
shows no new bypass. Registration or dispatch alone is not proof.
