# Diagnosing a wedged zellij

The presenting symptom is always the same and always misleading: **`zellij action …`
hangs forever instead of failing.** Every downstream surface — deckard, nanoleaf,
`ensure-zellij-workspace` — then reports its own unrelated-looking error.

Run this first. It is read-only and prints repairs without running them:

```bash
~/.config/zellij/scripts/zellij-doctor.sh
```

To apply the repairs (dry-run by default):

```bash
~/.config/zellij/scripts/zellij-unwedge.sh          # shows the plan
~/.config/zellij/scripts/zellij-unwedge.sh --yes    # applies it
```

## Why a hang and not an error

A zellij CLI client connects to a unix socket at
`/run/user/1000/zellij/contract_version_1/<session>`. If the server is not *accepting*,
the connection sits in the kernel accept queue indefinitely. There is no timeout and no
error. `timeout` is the only thing that ends it, which is why every consumer reports a
timeout rather than a refusal.

Read the queue directly — column 3 is pending, column 4 is the backlog limit:

```bash
ss -lx | grep -F "/zellij/contract_version_1/Workspace"
#  pending == backlog  →  the server is not accepting anything
#  pending == 0        →  healthy
```

## The three causes seen so far

### 1. The server process is SIGSTOP'd

```bash
ps -o stat= -p "$(pgrep -f -- '--server .*/Workspace')"
```

`T` (with `l` for multi-threaded) means stopped. Confirm with
`cat /proc/<pid>/wchan` → `do_signal_stop`, and `/proc/<pid>/task/*/stat` showing most
threads in `T`.

On 2026-08-23 the server had been stopped with 51 of 53 threads parked, accept queue
pinned at 4097/4096. Resume with `kill -CONT <pid>` — but **stop the pollers first**
(see below) or the queue refills faster than it drains and the fix looks like a no-op.

The stop signal's origin was never identified. `TracerPid` was 0 (not a debugger) and
the process had no controlling terminal (so not SIGTTIN/SIGTTOU). Suspect anything that
suspends heavy processes — a gaming/GPU-freeing script, a memory guardian, a stray
`kill -STOP`. If it recurs, that is the thing to hunt.

### 2. Polling amplifiers keep the queue full

Two things poll this session hard:

- **deckard**, every 500 ms with a 2000 ms cap — ~100k connections over 14 hours if
  none are accepted. Fix the root cause *and* set `DECKARD_PLUGIN` so it stops polling
  at all (see below).
- **`ensure-zellij-workspace --watch`**, every 30 s. Its health check is
  `zellij --session Workspace action query-tab-names`; when that hangs it concludes the
  session is dead and spawns another `attach --create`.

Always `systemctl --user stop deckard@Workspace.service zellij-workspace.service`
before touching the server, then clear stranded clients:

```bash
pkill -f '/home/delorenj/.local/bin/zellij.*(action|list-sessions)'
```

### 3. The resurrection cache enumerator

`/tmp/zellij-1000/zellij-log/zellij.log` contained **56,312** occurrences of:

```
Failed to read created stamp of resurrection file:
  creation time is not available on this platform currently
```

It fires once per directory in `~/.cache/zellij/contract_version_1/session_info/`,
which had grown to 378 dirs / 113 MB. This is what makes `zellij list-sessions` hang
specifically.

The filesystem is ext4 and **does** report `Birth:` (`stat` proves it), so this is the
downloaded 0.44.3 release binary failing `statx`, not a filesystem limitation. You
cannot fix the binary from here. You can stop feeding it — `zellij-unwedge.sh` step 4
prunes to the 40 most recent, always keeping `Workspace`.

Most of those dirs are one-off agent sessions (`sir-fix-a-lot-pjan21-v17-spec` and
friends). Pruning is safe; each holds only a serialized layout you will never resurrect.

## Healthy baselines

Measure against these, from the same machine:

| Check | Healthy |
|---|---|
| `zellij action query-tab-names` | ~12–105 ms |
| Accept queue pending | 0 |
| Server `stat` | `Sl`, wchan `futex_do_wait` |
| Stranded CLI clients | 0 |
| `session_info/` dirs | < 50 |

A round-trip of ~1200 ms is *recovering*, not healthy — it means the backlog is still
draining. Re-measure before concluding anything.

## Deckard specifically

Deckard has a purpose-built zellij plugin that pushes topology over a pipe, and a CLI
fallback that polls. The plugin is selected **only** by an environment variable —
there is no CLI flag:

```
DECKARD_PLUGIN=/home/delorenj/code/deckard/plugin/target/wasm32-wasip1/release/deckard_zellij.wasm
```

Set via a systemd drop-in at
`~/.config/systemd/user/deckard@.service.d/plugin.conf`. Without it deckard logs
`production plugin is not configured; using CLI fallback` at startup and polls forever.

Expect a brief `plugin emitted no valid topology within 2s` burst on restart — that is
the plugin loading while the CLI is still slow. If those lines stop within ~20 s, it is
on the plugin path. Confirm in the zellij log:

```bash
grep -a "Loaded plugin.*deckard_zellij" /tmp/zellij-1000/zellij-log/zellij.log | tail -1
```

## Grep recipes for the log

```bash
L=/tmp/zellij-1000/zellij-log/zellij.log
grep -a "Loaded plugin" "$L" | tail          # what actually loaded, and when
grep -ac "creation time is not available" "$L"   # resurrection enumerator noise
grep -a "\[new-tab-right\]" "$L" | tail      # a plugin's own trace
grep -aiE "error|panic" "$L" | tail -30
```

A plugin that logs `Permissions granted` but never logs its own trigger line is
**loaded but never piped to**. That distinction is the whole diagnosis.
