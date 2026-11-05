---
name: target-watch
description: Watch a person across every inbound channel (email, texts/RCS/iMessage, group chats, Telegram, Slack, Google Chat, WhatsApp, calls, voicemail) and turn their messages into Plane tickets, Telegram pings and a ringing phone. Use when the operator says watch <person>, add a target, alert me when <person> texts/emails/calls, make my phone ring when <person> writes, stop watching <person>, quiet hours, or asks which people are watched.
---

# target-watch: alerts keyed on a person, not a provider

The service README is the authority:
`~/code/33GOD/bloodbank/services/target-watch/README.md`
(sections "Add a target", "Ring", "Add a provider", "Deploy", "Proofs"). Read it before acting.

## Where things live

| What | Where |
|---|---|
| One target = one TOML file | `<client repo>/.watch/<person-id>.toml`, e.g. `~/code/james-brennan/.watch/jim-brennan.toml` |
| Discovery globs | `~/code/*/.watch/*.toml`, `~/code/33GOD/*/.watch/*.toml`, `services/target-watch/targets/*.toml` (the selftest only) |
| List every watched person | `~/code/33GOD/bloodbank/services/target-watch/.venv/bin/target-watch check` |
| Service code, units, Candybar Gmail poll | `~/code/33GOD/bloodbank/services/target-watch/` |

**Real targets never go in bloodbank: that repo is PUBLIC.** A person's handles, and the
operator's cell for `ring:`, belong in the private repo the person belongs to. A person
with no client repo goes in a private repo the operator names.

## Add a target

1. Collect handles from evidence, not guesses: emails (Gmail search via `gog`), E.164
   numbers, the contact label as it appears on the operator's phone (RCS events carry the
   label, not a number; check Candystore `messaging.rcs.received` for the exact string),
   platform ids (`slack:U…`, `telegram:<id>`). Record known non-handles (business lines,
   shared inboxes, the operator's own addresses) as comments so nobody adds them later.
2. Write `<repo>/.watch/<id>.toml` from the README template. Sink:
   - `kind = "plane"` with `repo = "~/code/<repo>"` (px binds the board from `.project.json`),
     `state = "Backlog"` (Todo makes the PM fleet start work), `coalesce_hours = 24`; or
   - `kind = "notify_only"` for no tickets.
   - `notify = ["telegram:7564050286", "ring:+12152083549"]`: Telegram DM to the operator,
     then a ring on his cell. Optional `ring_cooldown_minutes` (default 10) and
     `ring_quiet_hours = "22:00-07:00"` (America/New_York; Telegram still goes out).
3. Run `target-watch check`; it must print `ok`.
4. Prove it: `target-watch replay --since <ISO> --target <id>` shows what would have matched.
5. Commit the file in the client repo, push, and merge. Targets hot-reload within 30 s, so
   nothing needs a restart. Only a bloodbank code change needs
   `systemctl --user restart target-watch-sink target-watch-match`.

To stop watching someone, delete the file. To mute just the phone, drop the `ring:` entry.

## Gotchas

- A new provider becomes watchable by adding an `x-sender` block to its inbound schema, not
  by touching any target.
- A live ring test without a ticket: a scratch `notify_only` target plus
  `target-watch --targets <file> --state-dir <scratch> sink --from-file det.json`. The
  detection's `ordering_key` must be `watch:<watch_id>`.
- Calls the operator answers on his cell are invisible; only forwarded or missed calls reach
  Telnyx and the bus.
- In an agent shell, `hermes` may resolve to a wrapper or a shell function; the units pin
  `~/.local/bin/hermes -p 33god-pm`.
