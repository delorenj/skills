---
name: zellij-workspace-ops
description: |
  Debug, configure, and extend delorenj's single-session zellij workspace and the agent surfaces bound to it. Use when touching files in ~/.config/zellij, when a zellij CLI call hangs or times out, when deckard or zellij-driver misbehave, when agent panes come back suspended after a crash, when wiring a zellij plugin or keybind, when tab attention/notification does not reach the user, or when an agent must find/focus/rename a tab from outside a pane. Triggers: zellij, config.kdl, load_plugins, MessagePlugin, zellij pipe, zellij action, override-layout, session-layout.kdl, resurrection, start_suspended, post_command_discovery_hook, agent-pane, zellij-doctor, unwedge, Workspace session, ZELLIJ_PANE_ID, deckard, DECKARD_PLUGIN, tab attention, visual bell, zjstatus, zellij plugin wasm. Do NOT use for tmux, for generic terminal-emulator config (alacritty/ghostty), for deckard's internal Rust architecture (read that repo), or for Bloodbank event schemas (bloodbank-integration).
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

## The traps

Each of these cost real time. They are non-obvious and they repeat.

**1. `load_plugins` is read once, at session start.**
Verified in source (`zellij-server/src/lib.rs` passes `background_plugins` into
`plugin_thread_main` at startup; the `ConfigWrittenToDisk` handler does not re-run
them). Adding a `load_plugins` entry does **nothing** for a running session, and this
user never restarts his. To load a plugin into the live session, use
`zellij pipe --plugin file:/abs/path --name <pipe>` — the CLI launches it on demand.
Keybinds *do* hot-reload; background plugins do not.

**2. `file:~/...` is not tilde-expanded.** Four separate plugins were silently dead
from this one character class. Always absolute.

**3. There is NO plugin API version gate in 0.44.3.**
All plugins share one host import (`zellij::host_run_plugin_command`) and the binary
carries no version-mismatch string. A plugin built against zellij-tile **0.41.1**
(`room.wasm`) demonstrably loads in 3.4 ms on 0.44.3. If a doc or an agent tells you
plugins must be rebuilt to match the zellij version, that is **false** and following it
wastes a day. The only real cost of an old plugin is cosmetic: pre-0.43 builds know
`Style.palette` but not `Style.styling`, so they get 16-colour approximation.

**4. Zellij discovers a pane's command from `ps`.**
So shell *function* wrappers leak their expanded form into `session-layout.kdl`, and a
command that only exists as a function cannot be replayed. This is why resurrection
restores the wrong invocation. See [references/agent-sessions.md](references/agent-sessions.md).

**5. `config.kdl` used to be a generated artifact. It is not any more.**
Until 2026-08-23, `zellij` was a zsh *function* in `$ZSH_CUSTOM` that ran a `sed` pass
over `config.kdl` on the first invocation of every shell, and `setup-zellij-v2.sh` would
`cp` a frozen template over it. Hand edits reverted with no explanation. Those files are
now deleted. **If `zellij-wrapper.zsh`, `setup-zellij*.sh`, or `config.template.kdl`
reappear, something restored them — delete them again.** Sanity check:
`whence -v zellij` must print the binary path, not "shell function".

**6. `/usr/bin/rustc` shadows rustup on PATH and has no `wasm32-wasip1` std.**
Building any zellij plugin fails with `can't find crate for core`, which reads exactly
like a missing target — so `rustup target add` "fixes" nothing, because the target *is*
installed. Pin `RUSTC`:
```bash
T=~/.rustup/toolchains/1.95.0-x86_64-unknown-linux-gnu
RUSTC="$T/bin/rustc" "$T/bin/cargo" build --release --target wasm32-wasip1
```

**7. Attribution: bus events carry no pane id.**
A field census over 85 live `bloodbank.evt.agent.>` envelopes found no
`pane|tab|zellij|pid|tty` field at all. `data.working_directory` plus `actor.cli` is the
only attribution available there. The `deckard.evt.attention` subject *does* carry
`zellij_pane_id`. Inside a pane, `$ZELLIJ_PANE_ID` and `$ZELLIJ_SESSION_NAME` are real
and are the correct source.

## The surrounding system

Five services bind to this one session. Breaking the zellij CLI breaks most of them, so
check `systemctl --user status` for these before blaming a component:

| Unit | Role |
|---|---|
| `zellij-workspace.service` | `ensure-zellij-workspace --watch` keeps `Workspace` alive; hardcodes that name |
| `deckard@Workspace.service` | Stream Deck surface; tab per key, press to focus |
| `nanoleaf-panels.service` | Physical light wall: zellij tabs → Hive, agent tree → Honeycomb |
| `zellij-web.service` | `zellij web` on :8082, fronted at `z.delo.sh` (token auth enforced) |
| `zellij-driver.service` | Agentboard → zellij control bridge on :8084 |

## House rules for changes here

- `~/.config/zellij` is a **symlink into the `zshyzsh` git repo**. Every change is a
  commit. Commit and push; never leave config edits uncommitted.
- Never write a `.bak` beside a file in that repo — the pre-commit guard blocks it and
  git already is the backup.
- Prefer a change that works on the running session. If it genuinely requires a new
  session, say so explicitly and let the user choose when.
