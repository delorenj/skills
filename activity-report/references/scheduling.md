# Scheduling

One systemd user timer per project, from two template units and one drop-in.

## Units

`assets/systemd/activity-report@.service` and `activity-report@.timer` are
copied verbatim to `~/.config/systemd/user/`. The instance name is the pjangler
slug: `activity-report@james-brennan.timer` starts
`activity-report@james-brennan.service`, which runs
`%h/.local/bin/activity-report run --project james-brennan` with a PATH of
`~/.local/bin`, mise shims and the system dirs, `Nice=10`, idle IO, and a
90-minute start timeout (two compose passes of a headless agent).

The timer's own `OnCalendar` is a default. The project's schedule lives in

```
~/.config/systemd/user/activity-report@<slug>.timer.d/schedule.conf
[Timer]
OnCalendar=
OnCalendar=*-*-* 03:00:00 America/New_York
```

rendered from `activity_report.schedule.at` and `.timezone` by
`schedule.render_dropin`. The empty `OnCalendar=` resets the template's value;
systemd requires the reset before a new value in a drop-in. `Persistent=true`
runs a missed night at the next boot; that is safe because the portal row's id
is derived from (project, window end, visibility) and the event carries the run
id, so a catch-up overwrites rather than duplicates. `AccuracySec=1min` keeps
the run near the minute the label is computed from.

## Commands

- `activity-report install-timer --project <slug>` (or
  `scripts/install-timer.sh --project <slug>`): copies the units if absent or
  changed, writes the drop-in, `daemon-reload`, `enable --now` the timer, checks
  lingering, prints `list-timers`. Needs the `~/.local/bin/activity-report` shim
  (`activity-report init`) because the unit's `ExecStart` points at it.
- `activity-report timer-status --project <slug>`: `list-timers` for the
  timer, the drop-in as installed versus what the config says, and the last 20
  journal lines of the service.
- Lingering: without `loginctl enable-linger $USER` the user manager stops at
  logout and the timer sleeps with it. This host lingers already; the installer
  prints a note when a host does not.

## Dry parallel nights

To run a project's report every night without writing anything the reader
sees, set the dry flag on the service instance, not the timer:

```
~/.config/systemd/user/activity-report@<slug>.service.d/dry.conf
[Service]
Environment=ACTIVITY_REPORT_DRY=1
```

then `systemctl --user daemon-reload`. `run.sh` treats the variable exactly as
`--dry-run`: the event is emitted with `generator.dry_run: true` (so it shows in
Candystore), and verify, the portal row, retain and the durable html copy are
skipped. `raw.txt`, `.md`, `.html` and `.event.json` are all written under
`runtime/activity-report/<slug>/` for reading the next morning. Remove the
drop-in and reload to go live.

## The james-brennan cutover

The old job (`james-brennan-daily-update.timer` at 03:00, `scripts/daily-update-*`
in the repo, the repo-local `daily-update` skill) keeps writing the two portal
rows until this skill has proven itself on the same nights. Order:

1. Wire the project: `activity_report` block in `.project.json` with
   `schedule.at: "03:30"` and the portal block; `activity-report init`;
   `ensure-labels --confirm` once; label the tickets that must or must not be
   surfaced.
2. `activity-report install-timer --project james-brennan`, then the
   `dry.conf` drop-in above. The new timer runs at 03:30 dry while the old one
   runs at 03:00 for real, so both see the same day.
3. Each morning compare `runtime/activity-report/james-brennan/<label>-{internal,external}.raw.txt`
   against `runtime/daily-update/<date>-{internal,client}.md`, and the
   `dry_run: true` events in Candystore against what the old job published.
   Tune `lint.banned_terms`, the exposure labels and the templates from what the
   comparison shows; the lint's denied-title check is the one most likely to
   need tuning.
4. Cutover, in this order and last: remove `dry.conf` and reload; set
   `schedule.at` back to `"03:00"` and re-run `install-timer`; `systemctl --user
   disable --now james-brennan-daily-update.timer`; delete the old scripts, the
   old skill and their mise tasks; `timer-status` the next morning.

Two things the comparison will show that are not bugs: the new job's window
runs from the previous report's window end rather than a calendar day
(`window.basis: previous_report`), and the external row's id changes because it
is derived from the window end instead of the date, so the first live night
adds a row rather than overwriting the old job's.

## intelliforia

The `team-update-*` user timers on this host are dead (their scripts moved
under the repo's skill and were never re-pointed). Migration when it is wanted:

- `activity_report` block with `audiences: ["external"]` only; there is no
  team-only reader for that project.
- Trello is not a supported board; collect reports `board.status: unsupported`
  and the digest carries no tickets, which the external register does not need.
- The published page is the durable html: point `output.durable_html_dir` at
  the site's content directory and let the site's own publish pick it up (a
  dedicated `output.site_dir` key is the natural follow-up if the site wants a
  different name or an index).
- `portal: null`; the html is the deliverable.
- Then delete the four `team-update-*` units and their timers.
