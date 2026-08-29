# The 0.44.3 CLI surface an agent should actually use

Most automation here reaches for polling when a push or a stable id would do. This is
the capability map, verified against the installed binary's `--help`.

## Identify a pane from inside it

```
$ZELLIJ_PANE_ID        # e.g. 3   — `set-pane-color` defaults to this
$ZELLIJ_SESSION_NAME   # e.g. Workspace
$ZELLIJ                # "0" — but see the trap below
```

**Gate hooks on `ZELLIJ_SESSION_NAME`, never on `$ZELLIJ`.** The server does set
`ZELLIJ=0` (`envs::set_zellij("0")`), and the bare pane shell has it — but it is
**absent from the Claude Code and Codex processes themselves**, which is exactly where
hooks run. Sampled from `/proc/<pid>/environ` on 2026-08-23:

| process | `ZELLIJ_SESSION_NAME` | `ZELLIJ` |
|---|---|---|
| pane `zsh` | set | `0` |
| `kimi-co` | set | `0` |
| Claude Code (`2.1.241`) | set | **absent** |
| `codex`, `node-MainThread` | set | **absent** |

Something strips it between the pane shell and the agent (a `tmux: server` also turns up
inside a pane, and the agents may sanitise their own env). The mechanism does not matter;
the consequence does — **a hook gated on `$ZELLIJ` can never fire even once.** Gating on
`ZELLIJ_SESSION_NAME` is also better on its own merits: it is the variable the call
actually needs, so the guard and the requirement are the same check.

Wrap every call in `timeout 1s … || true`. A hook must never block or fail an agent turn.

## Target a tab from outside

Prefer **stable ids** over positions. `position` is display metadata and changes when
tabs are reordered; `tab_id` does not.

```bash
zellij -s Workspace action list-tabs --json --panes --state   # ids, names, state
zellij -s Workspace action go-to-tab-by-id <id>
zellij -s Workspace action rename-tab-by-id <id> "name"
zellij -s Workspace action go-to-tab-name "Deckard"
zellij -s Workspace action query-tab-names
zellij -s Workspace action current-tab-info
zellij -s Workspace action list-panes --json
zellij -s Workspace action list-clients
```

`list-tabs --json` includes two fields nothing on this machine reads:

```
has_bell_notification   # persistent bell — an agent wants attention
is_flashing_bell        # transient, 400 ms
```

Those are the attention signal. See [attention.md](attention.md).

Always run these with `timeout` and `env -u ZELLIJ -u ZELLIJ_SESSION_NAME` when calling
from outside a pane, so a stale inherited env cannot retarget the call.

### `list-panes --json` is 45× slower than `list-panes --tab`

Measured twice on this machine, rock-steady:

| Call | Time |
|---|---|
| `action list-panes --tab` | **104 ms** |
| `action list-panes --json` | **4706 ms** |

`--json` (and `--all`) resolve each pane's running command out of `ps`, which is what
costs the four and a half seconds. `--tab` returns the same `TAB_ID` / `TAB_NAME` /
pane-id columns as a table.

**A hook cannot afford the `--json` path** — it blows straight through any sane
`timeout` and would stall an agent turn. Parse the table instead; its columns are
two-space separated, so tab names containing single spaces (`Ideal Scenario`) survive a
`-F'  '` split intact:

```bash
zellij --session "$S" action list-panes --tab \
  | awk -F'  ' -v p="terminal_$ZELLIJ_PANE_ID" '$4==p {print $1"\t"$3; exit}'
```

The cost is specific to `list-panes`, and it is the `ps` resolution that does it — do
not generalise it to `--json` as a flag. Measured alongside, on the same session:

| Call | Time |
|---|---|
| `list-tabs --json` | 105 ms |
| `list-tabs --json --panes` | 104 ms |

So deckard's 2 s cap is comfortable for the call it actually makes (`list-tabs --json`);
its timeouts were the wedged server, not this. Reach for `list-panes --json` only when
you genuinely need each pane's running command, and never from a hook.

## Drive a pane

```bash
zellij action send-keys --pane-id terminal_3 Esc        # bulk-dismiss suspended panes
zellij action set-pane-color --pane-id 3 --bg '#3a1a1a' --fg '#ffd0d0'
zellij action set-pane-color --reset
zellij action focus-pane-id terminal_3
zellij action write-chars / paste / dump-screen
```

`set-pane-color` is the cheapest loud visual available with zero plugin work: a short
background hue cycle on the offending pane is impossible to miss. It defaults to
`$ZELLIJ_PANE_ID`, so a hook can colour its own pane with no lookup.

## Layouts at runtime — this fully works

The user's stated blocker ("I'd have to quit and risk my tabs") is not true on 0.44.3:

```bash
zellij action override-layout ./layouts/draft.kdl \
    --apply-only-to-active-tab \
    --retain-existing-terminal-panes    # panes not named by the layout survive

zellij action override-layout --layout-string '<raw kdl>'   # no file at all
zellij action new-tab --layout draft --cwd ~/code/foo       # try it in a throwaway tab
zellij action dump-layout > layouts/current.kdl             # capture what you have
```

`--retain-existing-terminal-panes` is the safety valve that makes this non-destructive.
Edit the file, re-run, watch it change — seconds, no restart.

Also available: `next-swap-layout` / `previous-swap-layout`, `stack-panes`.

`zellij action new-tab` has **no `--index`** — there is no CLI route to positional
insertion.

## Pipes — the push channel

```bash
zellij pipe --name <pipe> -- '<payload>'                       # all running plugins
zellij pipe --plugin file:/abs/path.wasm --name <pipe> -- '…'  # launches if not running
zellij pipe --plugin … --plugin-configuration k=v --name … -- '…'
tail -f log | zellij pipe --name logs --plugin …               # streams stdin
```

`--plugin-configuration` is part of plugin identity: the same wasm with different
configuration is a **different** plugin for routing purposes.

## Whole-session

```bash
zellij action save-session      # force serialization now — useful to test hooks
zellij action dump-layout
zellij action rename-session
zellij subscribe --pane-id 3 --format json --ansi   # live render stream (0.44.0+)
zellij watch                    # read-only attach
zellij web --start              # HTTP surface; token auth enforced
```

`save-session` is the fastest way to test a `post_command_discovery_hook` change
without waiting 60 s for the next tick.

`zellij subscribe` is an underused external feed: it streams a pane's viewport and
scrollback to any process, no plugin required.

## What plugins can and cannot do

From inside a WASM plugin:

- `set_timeout(f64)` needs no permission, fires `Event::Timer`; returning `true` from
  `update()` forces a re-render. Timer → mutate → re-render is a working animation loop
  at any framerate.
- Subscribable events: `TabUpdate`, `PaneUpdate`, `CommandChanged`,
  `CommandPaneExited` (carries exit code), `CwdChanged`, `PaneClosed`,
  `PermissionRequestResult`, `RunCommandResult`, `WebRequestResult`.
- **No sockets.** Plugins run under wasmi + wasmi_wasi with file I/O and env vars only.
  `web_request` and `run_command` are the sanctioned escape hatches; `run_command` to a
  helper binary makes any transport reachable in practice.
- `run_action(Action::MoveTab)` is a **silent no-op** from a plugin. Assume other
  client-relative actions may be too, and verify before relying on one.
- `TabInfo` exposes `position` but **no tab id**, which limits id-based actions from
  inside a plugin.

## Calling any of this from a hook

```bash
[ -n "${ZELLIJ_SESSION_NAME:-}" ] || exit 0    # NOT $ZELLIJ — see above
timeout 1s zellij action … >/dev/null 2>&1 || true
```

Never let a zellij call fail an agent turn. If the session is wedged these calls hang,
and an unguarded hook hangs the agent with it — that is precisely how the 2026-08-23
outage stayed invisible for fourteen hours.
