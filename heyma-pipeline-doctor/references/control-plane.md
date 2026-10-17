# Control plane — daemon, config, CLI, deploy, repo hygiene

Symptoms that land here: waxd down or wedged; a `wax` command failing; a setting
that seems to have no effect; the installed unit not matching the repo; docs that
contradict the code.

## Daemon

```bash
systemctl --user status waxd.service
journalctl --user -u waxd.service -n 100 --no-pager
systemctl --user restart waxd.service      # NOTHING hot-reloads; restart after any src change
```

**A quiet journal is not evidence of health.** waxd historically had no
`import logging` at all — 22 h of uptime and 46 processed items produced two lines.
If the journal is empty, confirm logging is actually configured before concluding
anything from its silence.

**Wedged but "active".** systemd reports `active` while the tick is blocked. The
real liveness signal is the state mirror's age:

```bash
echo $(( $(date +%s) - $(stat -c %Y "$HOME/HeyMa/var/state.json") ))s
```

Over ~180 s means the 1 Hz tick has stopped — blocked in `ledger.enrich()`, or
`os.replace` failing.

**Memory.** Use `/proc/<pid>/status` VmRSS, not `systemctl status`. The cgroup
figure counts reclaimable page cache from transcription children and reads ~4 GB
while the daemon's true RSS is ~53 MB.

## Resolving what is actually in effect

Never take a path from a doc. Ask the process — but never print a daemon
environment's *values*: an environ dump can carry a resolved credential, and a
redaction-by-name regex is one rename away from leaking one. Print names only.

```bash
P=$(systemctl --user show -p MainPID --value waxd.service)
tr '\0' '\n' < /proc/$P/environ | grep -E '^(WAX_|OP_|TRANSCRIBE)' | cut -d= -f1   # NAMES only
ls -l /proc/$P/fd | grep wax.db          # which ledger is genuinely open
```

`bin/wax doctor` is the sanctioned way to see resolved *values*: it prints
every resolved variable with its source, redacts credential-named values
(`KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL`) and — deliberately — leaves `op://`
references visible, since the reference is the whole point of storing one. Use
it when the board says a dependency is missing but not why.

## Configuration

Env-only — **there is no config file**, no schema, and no validation. The
knobs are spread across `config.py`, `paths.py`, `component.py`,
`natsclient.py`, `transcribe_adapter.py`, `passes.py`, `worker.py`
(`WAX_SWEEP_INTERVAL_S`, `WAX_DOCUMENT_SCAN_INTERVAL_S`), `documents.py` and
the pass scripts, each with an inline default. Production values live in
`waxd.service` `Environment=` lines and in pass yaml `env:` blocks. Don't
count or memorize them — `wax doctor` prints every resolved variable with its
source, which is both the inventory and the truth.

Consequences worth knowing:

- **A variable can be set and never read.** `WAX_DIARIZATION=1` sat in the unit
  as a no-op for weeks because only falsy values were branched on. Grep before
  believing a knob does anything: `grep -rn WAX_THING components/wax/`.
- **A user unit gets no login shell**, so anything exported in `~/.zshrc` is
  invisible to waxd. `OP_SERVICE_ACCOUNT_TOKEN` *is* present, which is why
  `op read` works from inside the daemon — that is the sanctioned way to get a
  credential at call time without writing one to disk.

## Deploy drift

```bash
diff <(cat components/wax/deploy/systemd/user/waxd.service) ~/.config/systemd/user/waxd.service
systemctl --user daemon-reload    # after ANY unit edit
```

Note `waxd.service` declares `OnFailure=wax-alert.service`, which fires **only
when the waxd process exits**. It has never fired for a stage failure and never
will — it is a crash alert, not a health alert.

## Tests

```bash
cd components/wax && python3 -m pytest tests -q      # or mise run wax:test
```

270 tests (as of 2026-10), seconds to run. Safe: every integration test
isolates itself with `WAX_ROOT` pointed at a temp dir and never touches live
audio or the live ledger.

## CLI surface

```
wax doctor [--json]         # resolved config + probes — start here
wax status                  # both state machines, queue, pass + diarization health
wax catalog [--json]        # safe discovery snapshot for Holocene/n8n
wax rec {start|stop|toggle|cancel|salvage|list|quiesce}
wax state [--cold]          wax items          wax queue        wax history
wax drain                   wax retry [<item>] wax skip         wax reconcile [--rebuild]
wax ep {list|status|run <slug> <item>|run-all <item>|sweep}
wax pipeline {enable|disable|status|list|compile|show|bindings|import <export.json>}
wax documents {list|scan|backfill|run|retry}
wax archive                 wax transcribe     wax events        wax migrate
```

`wax state --cold` is a pure function of the filesystem — correct even after waxd
has been SIGKILLed. Reach for it when you do not trust the daemon.

The `pipeline list|compile|show|bindings|import` and `documents` groups are
operations, not diagnostics — the `wax-pipeline` skill owns their detailed use
(its `references/pipelines-and-n8n.md` and `references/documents.md`, plus
`components/wax/docs/CONTROL-SURFACE.md`).

## Repo hygiene — traps that cost real debugging time

These are not cosmetic. Each one has actively misled someone.

| Trap | Why it hurts |
|---|---|
| `~/audio/var/state.json` | a 2026-07-30 mirror, false in every field, formatted exactly like a live one |
| repo-root `passes.d/` | a registry the runner never loads; editing it changes nothing |
| repo-root `WAX-DESIGN.md` | pre-relocation ancestor naming the retired `~/audio` layout |
| `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` | described the retired n8n pipeline for months; loaded into every agent's context here |
| n8n `r2TUca8smk5HDNZx` | reported `active: true` with a trigger on `~/audio/inbox` |
| a second checkout | whichever `transcribe` PATH finds is the code that runs — the daemon is protected by its `WAX_TRANSCRIBE` pin, but your shell is not |
| `~/.local/bin/transcribe` | since 2026-10 a modified **copy** of the repo shim, not a symlink; PATH resolution roots at `~/.local`. The daemon pin is what protects the pipeline (see incident log 2026-10-17) |

**Rule: if a document disagrees with the code, the document is wrong — fix it in
the same change, or the next person pays the same tax you just paid.**
