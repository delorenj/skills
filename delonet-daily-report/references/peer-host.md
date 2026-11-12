# Running the daily report on another host

The skill is host-neutral. Everything a host owns lives outside the skill, in the environment
or `~/.config/33god/host.env` (see SKILL.md, "Host-owned values"). This is the recipe for a
peer host: a Mac with a BSD userland, Candybar as the clock, and no 1Password service token.

## What the host needs

| need | why |
|---|---|
| Python 3.11+ first on the job's PATH | `reportctl` uses `datetime.UTC`; it exits 2 naming the version it found. macOS's `/usr/bin/python3` is 3.9: a launchd job has no mise or Homebrew PATH, so set one |
| `~/.config/33god/host.env` (mode 0600) | `SECRET_RESOLVER=interim`, `RESEND_API_KEY_REF`, `DDR_MAIL_FROM`, `DDR_CONFIG` if not the default |
| the interim store | `~/.config/33god/secrets.env` (0600) + `refmap.tsv` + the `env-op-resolve` binary (delonet-dotenv skill); the Resend ref must have a row in both |
| a report.json | from `assets/example-config.v2.json`: `~/`-relative state and archive dirs, this host's `project_roots`, sections that exist here only |

## BSD portability, and how the scripts stay clear of GNU

`nightly.sh` is bash 3.2 and BSD-safe by construction: no `date -d`, `readlink -f`, `sed -i`,
`flock` or `timeout`; yesterday's date is computed by `python3 -c` with `zoneinfo` in the config's
timezone; the symlink walk uses plain `readlink`. Its PATH is *appended* (`~/.local/bin`, the mise
shims, `/opt/homebrew/bin`, `/usr/local/bin`) so a host whose PATH already works keeps resolving
the same python3.

## Scheduling

One Candybar manifest, runner `exec`, argv `<skill>/scripts/nightly.sh nightly`, the schedule and
timezone in the manifest (06:00 America/New_York on big-chungus). It is idempotent: a verified
report is not regenerated, and `distribute` is safe to repeat. A missed fire is recovered by the
second manifest (`nightly.sh ensure`), which delivers the verified report or generates it first.
Never a timer, cron entry or Hermes cron job.

## Proving a run

`nightly.sh nightly --date YYYY-MM-DD` against a past date proves the chain without waiting for
the schedule. Then check the artifact, not the exit status alone:

```text
reportctl --config PATH verify --date YYYY-MM-DD      # ok: true
```

and look at the delivery: a 2xx from Resend is not a message in an inbox.
