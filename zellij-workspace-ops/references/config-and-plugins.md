# config.kdl and the plugin system

## config.kdl is hand-edited and authoritative

`~/.config/zellij` is a **symlink** to `/home/delorenj/.config/zshyzsh/zellij`, a git
repo. Edits are commits.

Until 2026-08-23 this was not true, and it is the single reason the user believed
"nothing I do to my zellij config ever works":

- `zellij` was a zsh **function**, not the binary. `zellij-wrapper.zsh` lived in
  `$ZSH_CUSTOM` (= the zshyzsh repo root), so oh-my-zsh's `*.zsh` glob auto-sourced it,
  and it ran `setup-zellij.sh` — a `sed` pass over `config.kdl` — on the first `zellij`
  invocation of **every shell**.
- `setup-zellij-v2.sh` was worse: a hard `cp config.template.kdl → config.kdl` from a
  template frozen at 2026-08-06.
- Evidence: a stray bare KDL node `Default: true` (a comment that lost its `//`) was
  removed and reintroduced **four times** across git history. Nobody did that by hand.

All four files are now deleted. **Verify before trusting any config edit:**

```bash
whence -v zellij      # must print the binary path, NOT "shell function"
ls ~/.config/zellij/config.template.kdl   # must not exist
```

If any of them reappear, something restored them. Delete again and find the restorer.

Deleting them cost nothing: the only value those scripts computed was `copy_command`,
and `scripts/copy-command.sh` already does its own wayland/x11/OSC-52 detection, so the
static value in `config.kdl` is correct on every platform.

## What hot-reloads and what does not

Zellij 0.44.3 watches `config.kdl` and sends `ConfigWrittenToDisk`, which calls
`propagate_configuration_changes`.

| Change | Live session? |
|---|---|
| Keybinds | **Yes** |
| Theme, `default_mode`, most options | **Yes** |
| `post_command_discovery_hook` | **Yes** (pty thread is reconfigured) |
| `load_plugins` entries | **No — new session only** |
| `plugins { … }` aliases | **No — new session only** |
| `default_layout` | **No** — applies at session creation |

`background_plugins` is read once, at startup, and passed into `plugin_thread_main`
(`zellij-server/src/lib.rs`). The reconfigure path does not re-run it. Since this user
never restarts his session, **a `load_plugins` entry alone will never take effect for
him.**

To load a plugin into the running session:

```bash
zellij pipe --plugin file:/absolute/path/to/plugin.wasm --name <pipe_name> -- '<payload>'
```

The CLI launches the plugin if it is not already running. Do both: add the
`load_plugins` line for future sessions *and* pipe it in for this one.

## Plugin URL identity is exact-match

The URL string is the plugin's identity **and** its permission-cache key. Two rules
follow:

- **`file:~/…` is not tilde-expanded.** This silently killed four plugins. Absolute
  paths only.
- Permissions are cached in `~/.cache/zellij/permissions.kdl`, keyed by that exact
  path. Because `~/.config/zellij` is a symlink, the same file is reachable by two
  different absolute paths — use the `~/.config/zellij/...` form consistently, which is
  what the existing grants use.

Currently granted there: `zellij_visual_notifications`, `zellij-new-tab-next-to-current`,
`zellij-attention`, `room`. **Permissions have never been the blocker** for any of the
plugin problems investigated — do not spend time on that hypothesis.

### Never alias a custom `.wasm` in the `plugins {}` block

The `plugins {}` block is for aliasing **built-in** plugins (`zellij:` prefix) only.
A custom `.wasm` must be referenced by its full `file:` URL directly in the binding:

```kdl
bind "Ctrl y" {
    LaunchOrFocusPlugin "file:/home/delorenj/.config/zellij/plugins/room.wasm" {
        floating true
        move_to_focused_tab true
    }
    SwitchToMode "normal"
}
```

**Why the alias fails**, so the error is recognisable: zellij's keybinding parser calls
`RunPluginOrAlias::from_url()` at config-parse time and passes `None` for the alias
dictionary. A bare name like `"room"` has no URL scheme, so URL parsing fails, the
fallback alias lookup finds nothing, and you get an *alias error at config load*. The
`file:` scheme is handled natively by `RunPluginLocation::parse()`, which bypasses the
alias resolver entirely.

| Plugin type | Reference format |
|---|---|
| Built-in | `zellij:name` — e.g. `zellij:share`, `zellij:session-manager` |
| Custom `.wasm` | `file:/absolute/path` |
| Remote | `https://…` |

**No variables in plugin URLs.** Neither `~` nor `$HOME` is expanded — zellij takes the
string literally. Older docs on this machine show `file:$HOME/…` because a now-deleted
setup script `sed`-expanded `$HOME` before zellij ever saw the file. That script is gone,
so `$HOME` in a plugin URL is now just as broken as a tilde. Absolute paths only.

## No version gate — stop rebuilding plugins

Checked three ways:

1. All ten installed `.wasm` files export the same set (`load pipe plugin_version
   render update _start`) and import exactly one host symbol,
   `zellij::host_run_plugin_command`.
2. The zellij binary contains **no** version-mismatch error string.
3. `room.wasm`, built against zellij-tile **0.41.1**, has a log line proving it loaded
   in 3.4 ms under 0.44.3.

The only real consequence of an older build is cosmetic: pre-0.43 plugins know
`Style.palette` but not `Style.styling`, so they render a 16-colour approximation
instead of the full theme. `CommandName` ordinals are append-only, so host calls still
mean the same thing.

**If an agent claims plugins must be rebuilt to match the zellij version, it is wrong.**
That belief has already cost this user time.

## Installed plugin inventory

| Plugin | Status | Note |
|---|---|---|
| `room` | wired, working | `Ctrl y` pane switcher |
| `zellij-new-tab-next-to-current` | wired, blocked upstream | see below |
| `zellij_visual_notifications` | his own build | animation engine — see [attention.md](attention.md) |
| `zellij-attention` | installed, never loaded | can only rename tabs; cannot animate |
| `zjstatus` | installed, never loaded | status bar; **cannot** flash one specific tab |
| `zellij-workspace` | installed, never bound | fuzzy layout picker → applies to running session |
| `zellij-choose-tree`, `zellij-favs`, `monocle`, `zbuffers` | installed, never bound | navigation candidates for a 30-tab session |

The recurring pattern: binary acquired, config line never written. **Check wiring
before debugging behaviour.**

## new-tab-next-to-current: a known dead end

Do not re-attempt without new upstream information.

- The plugin loads and gets permissions (9 × `Permissions granted` in the log) and logs
  **zero** `Triggered:` lines — the `Alt t` pipe never reaches it.
- A real plugin bug was found and fixed (zellij delivers tab-creation and focus-change
  as two separate `TabUpdate` events; the first still reports the *old* tab as active).
  That patch is committed at `delorenj/zellij-new-tab-next-to-current@ad54a7e`.
- With the patch the move is computed correctly and dispatched — and zellij ignores it.
  **`run_action(Action::MoveTab)` is a silent no-op from inside a plugin** on 0.44.3, as
  is shelling out via `run_command`. The identical CLI command works externally.
- `zellij action new-tab` has **no `--index`**, so there is no CLI route either.
- `MessagePlugin { launch_new true }` is not a workaround: it injects a fresh
  `_zellij_id` UUID into the plugin configuration, spawning a **new instance per
  keypress**.

One experiment remains worth ten minutes: the plugin's `run_command` may simply lack
`ZELLIJ_SESSION_NAME` in its environment. Try
`zellij --session "$ZELLIJ_SESSION_NAME" action move-tab left` from inside it.
Otherwise: file the issue and move on.
