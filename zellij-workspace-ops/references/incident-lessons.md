# Incident Lessons

Load only for the matching task. Historical versions and incidents are evidence
to verify against the current installation, not universal current facts.

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
restores the wrong invocation. See [references/agent-sessions.md](agent-sessions.md).

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

