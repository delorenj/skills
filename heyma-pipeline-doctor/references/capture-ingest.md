# Capture & ingest — playbook

Symptoms that land here: the hotkey does nothing; a recording did not appear in
the inbox; `stream` stuck in `error` or `not-ready`; items sitting in the inbox
untranscribed; the inbox reports "empty" while audio is clearly there.

## Capture

**The hotkey is a GNOME custom keybinding**, `Ctrl+\` →
`~/.local/bin/wax-toggle` → `wax rec toggle`. The evdev subsystem described in
WAX-DESIGN.md (`wax/hotkey.py`, physical-keyboard filtering, `Ctrl+Alt+Shift+R`)
**was never built** — there is no fallback listener. If the keybinding is gone,
recording is tray-menu and CLI only.

```bash
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
bin/wax rec start --label test && sleep 3 && bin/wax rec stop
```

### stream states

`wax state --cold` is a pure function of the filesystem — it answers correctly
even after waxd has been SIGKILLed. Use it when you do not trust the daemon.

| State | Means | Do |
|---|---|---|
| `ready` | no sentinels, preflight ok | nothing |
| `recording` | rec.json, no .stop, encoder alive; audio accumulating in `.segs/` | nothing |
| `not-ready` clause `a-finalizing` | stop written, finalizer running | wait; there is a 180 s deadline |
| `not-ready` clause `b-incapable` | preflight failed | read `cause_code`: `no_default_source`, `disk_low`, `inbox_unwritable`, `stream_unwritable` |
| `error-partial` | encoder exited uninstructed | `wax rec salvage` — remuxes a valid Ogg into the inbox and moves every original segment and sentinel to `recovered/orphans/` |
| `error` | sticky catch-all | `wax rec list`, fix the cause, then `wax reset` |

**`wax rec start` never refuses because of residue.** It sweeps prior residue
aside loudly (emitting `session.failed` for the stranded rid) and records. A
recorder blockable by yesterday's crash is worse than the GUI app it replaced.

### Graphical-session shutdown

The encoder's transient scope survives a plain `waxd` restart, but it cannot
keep reading after GDM tears down D-Bus, PipeWire, and WirePlumber. The enabled
`wax-capture-guard.service` runs `wax rec quiesce` before those services stop.
Idle is success; an active capture is cleanly finalized. Confirm the protection
with:

```bash
systemctl --user is-enabled wax-capture-guard.service
systemctl --user is-active wax-capture-guard.service
```

If the guard is absent, run `components/wax/deploy/install-systemd-user`, reload
the user manager, and enable the unit. Do not test it by restarting GDM during a
real recording; the component suite exercises the same FIFO stop and remux path
against an isolated synthetic encoder.

**No default source** is the most common `b-incapable` cause:
```bash
pactl get-default-source && pactl list short sources
```

## Ingest

Two feeds, one inbox:

- **`inbox/`** — the only inbox. Everything local writes here.
- **`dropoff/`** — Syncthing `receiveonly`, 5 devices. `waxd` **copies out of it
  and never writes into it.** Writing into a receive-only folder destroyed a
  recording on 2026-06-29; files added locally are treated as divergent and
  reverted on any reconcile or folder-marker reset.

### The scheduler

```bash
bin/wax pipeline status
bin/wax pipeline enable      # absent var/pipeline.enabled == operator-paused
```

`inbox.state == error` means work is present with no live worker claim for >60 s
(`cause_code=stranded_work`), or the scheduler is off. Read
`state.json → inbox.evidence`.

### The subdirectory blind spot

`state.inbox_items()` historically used `iterdir()` while `reconcile.scan_local()`
used `rglob()`. Anything one directory deeper was invisible to the worker
**forever** — never queued, never counted — while the inbox truthfully reported
"empty". 1.07 GB sat that way.

```bash
find "$HOME/HeyMa/inbox" -mindepth 2 -type f \( -iname '*.ogg' -o -iname '*.mp3' \
  -o -iname '*.m4a' -o -iname '*.wav' -o -iname '*.opus' \) \
  -not -path '*/.stversions/*' -not -path '*/.stfolder/*'
```

Anything listed is stranded. `wax reconcile` adopts it — but only if someone runs
it. Note `.stfolder` and `.stversions` belong to Syncthing; descending into
`.stversions` would re-adopt every historical version of every file.

### Phantom rows

`ledger.counts()` is unfiltered, so rows pointing at the retired `~/audio/` root
inflate `items.pending` permanently while `queue.total` stays 0. That makes the one
count that could signal a real backlog untrustworthy.

```bash
sqlite3 -readonly "file:$HOME/HeyMa/var/wax.db?mode=ro" \
  "SELECT item_id, state, path FROM items WHERE state IN ('pending','archived','transcribed');" \
  | while IFS='|' read -r id st p; do [ -e "$p" ] || echo "PHANTOM $st $id $p"; done
```

Do **not** delete these rows blindly — at least one is genuinely backed up in S3
and is a real historical record.

## Reconcile — read this before you run it

`wax reconcile --rebuild` recomputes every item's state from
(has_backup, has_transcript, in_inbox). `skipped` and `failed` are not in
`infer_states()`'s vocabulary, so without the terminal-state guard it **silently
resurrects items an operator deliberately parked**. Prefer `--dry-run` first, and
confirm `TERMINAL_STATES` is honoured in `reconcile.py` before running it for real.
