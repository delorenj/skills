---
name: zellij-workspace-ops
description: 'Debug, configure, and extend delorenj''s single-session zellij workspace
  and the agent surfaces bound to it. Use when touching files in ~/.config/zellij,
  when a zellij CLI call hangs or times out, when deckard misbehaves,
  when agent panes come back suspended after a crash, when wiring a zellij plugin
  or keybind, when tab attention/notification does not reach the user, or when an
  agent must find/focus/rename a tab from outside a pane. Triggers: zellij, config.kdl,
  load_plugins, MessagePlugin, zellij pipe, zellij action, override-layout, session-layout.kdl,
  resurrection, start_suspended, post_command_discovery_hook, agent-pane, zellij-doctor,
  unwedge, Workspace session, ZELLIJ_PANE_ID, deckard, DECKARD_PLUGIN, tab attention,
  visual bell, zjstatus, zellij plugin wasm. Do NOT use for tmux, for generic terminal-emulator
  config (alacritty/ghostty), for deckard''s internal Rust architecture (read that
  repo), or for Bloodbank event schemas (bloodbank-integration).

  '
metadata:
  pipeline-status: new
---

# Zellij Workspace Ops

The user runs **one** zellij session, named `Workspace`, holding ~16–30 tabs, most of
them an AI coding agent. He has ADHD: a tab he cannot see does not exist, and he will
not split into multiple sessions. Every recommendation must survive that constraint.

This skill exists because a 2026-08-23 forensic pass found that **almost nothing here
fails the way it appears to fail.** The observable symptom is nearly always two or
three layers away from the cause. Read the Traps before you form a hypothesis.

## Operating principles

- **The log is the oracle.** `/tmp/zellij-1000/zellij-log/zellij.log` answers most
  questions in one grep and almost nothing on this machine reads it. It is how we
  proved a plugin was loading but never triggering, and how we found 56,312 identical
  resurrection errors. Grep it *before* theorizing.
- **Run `zellij-doctor.sh` first, always.** `~/.config/zellij/scripts/zellij-doctor.sh`
  is read-only and checks the eight things that have actually broken. A hanging
  `zellij action` is a symptom of the server, not of your command.
- **Never restart, kill, or detach the `Workspace` session** to fix something. It holds
  live agent conversations. Everything in this skill is designed to work on a running
  session or to be deferred to the next natural restart.
- **A missing config line is more likely than a broken component.** The dominant
  historical failure mode is a two-step job abandoned after step one: the binary gets
  installed and the config line never gets written. Check wiring before you debug code.
- **Prove it changed.** "Should work now" is not a result. Confirm with the log, with
  `zellij action list-tabs --json`, or with the plugin's own debug output.

## Triage table

| Symptom | Read first | Likely cause |
|---|---|---|
| `zellij action`/`list-sessions` hangs or times out | [references/diagnosing.md](references/diagnosing.md) | Server SIGSTOP'd, or saturated accept queue, or 300+ dirs in the resurrection cache |
| Deckard/Nanoleaf shows stale or no tab state | [references/diagnosing.md](references/diagnosing.md) | Downstream of the CLI hang; or `DECKARD_PLUGIN` unset so it polls |
| A config edit "does nothing" | [references/config-and-plugins.md](references/config-and-plugins.md) | `load_plugins` needs a NEW session; or a tilde path; or the edit was reverted |
| A plugin loads but never acts | [references/config-and-plugins.md](references/config-and-plugins.md) | Pipe never reaches it — check the log for the plugin's own trigger line |
| Agent panes come back with an ENTER/ESC prompt | [references/agent-sessions.md](references/agent-sessions.md) | `start_suspended true` + wrapper leak into `session-layout.kdl` |
| Need to find/focus/rename a tab from outside | [references/cli-surface.md](references/cli-surface.md) | Use stable ids, not positions |
| Want a louder tab alert | [references/attention.md](references/attention.md) | The renderer must change, not the tab name |
| Want to iterate on a layout without restarting | [references/cli-surface.md](references/cli-surface.md) | `zellij action override-layout` |

## Detailed procedures

Read [incident lessons](references/incident-lessons.md) only for the
matching implementation or diagnosis.

## The surrounding system

Four services bind to this one session. Breaking the zellij CLI breaks most of them, so
check `systemctl --user status` for these before blaming a component:

| Unit | Role |
|---|---|
| `zellij-workspace.service` | `ensure-zellij-workspace --watch` keeps `Workspace` alive; hardcodes that name |
| `deckard@Workspace.service` | Stream Deck surface; tab per key, press to focus |
| `nanoleaf-panels.service` | Physical light wall: zellij tabs → Hive, agent tree → Honeycomb |
| `zellij-web.service` | `zellij web` on :8082, fronted at `z.delo.sh` (token auth enforced) |

`zellij-driver.service` (the Agentboard → zellij bridge on :8084) is **retired**: Agentboard
was killed 2026-09-23, the unit is disabled, `zellij-web` no longer `Wants=` it, and the
`z.delo.sh/agentboard` Traefik route is gone. Do not re-enable it to fix anything here.

## House rules for changes here

- `~/.config/zellij` is a **symlink into the `zshyzsh` git repo**. Every change is a
  commit. Commit and push; never leave config edits uncommitted.
- Never write a `.bak` beside a file in that repo — the pre-commit guard blocks it and
  git already is the backup.
- Prefer a change that works on the running session. If it genuinely requires a new
  session, say so explicitly and let the user choose when.
