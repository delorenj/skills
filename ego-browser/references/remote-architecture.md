# Remote architecture — how the bridge works

## Why a bridge exists

ego lite ships **only as a macOS application**. Verified 2026-08-14:

- The only binaries published are macOS disk images at
  `cdn.ego.app/setup/macos/{arm64,x64}/*.dmg`.
- Upstream's `install.sh` calls `hdiutil` and `ditto` (both macOS-only) and
  extracts the `ego-browser` CLI from *inside* the `.app` bundle — so the CLI is
  a Mach-O client to a native Mac app, not a portable Node tool.
- The GitHub release archives (`ego-browser-v1.2.3.zip`) contain **no binaries
  at all** — only `SKILL.md`, per-site "learnings", and that macOS installer.
- `lite.ego.app` offers a Mac build only; Windows is a waitlist. Linux is not
  mentioned.

The fleet's agent hosts (`big-chungus`, `ai`) are Linux. Rather than give up the
canonical-browser goal or fragment it per host, the browser lives in exactly one
place — the MacBook that already holds the real Chrome profile — and every host
reaches it through `scripts/ego-browser`.

## Current status — verified live

Brought up and tested 2026-08-23 against `carries-macbook-air` (macOS 26.6.2,
arm64). All six `doctor` checks pass, multi-line heredocs execute, and the
inherited profile is genuinely authenticated (a read-only GitHub check reported
the session as `delorenj`). ego lite was already installed at
`/Users/delorenj/.local/bin/ego-browser` and Remote Login was already enabled,
so the install step below was not needed on this machine.

## The path a call takes

```
agent (any host)
  └─ ego-browser nodejs <<'EOF' … EOF
       └─ buffer stdin, append to audit.log
            └─ ssh -T carries-macbook-air.burro-salmon.ts.net
                 └─ exec '/Users/delorenj/.local/bin/ego-browser' nodejs
                      └─ ego lite (Aqua session) drives the real profile
```

Run **on** a Mac that has ego lite, the shim detects it and execs the local
binary directly — ssh is never involved. The same command therefore works
everywhere, which is the point.

## Configuration

Precedence: environment > `~/.config/ego-browser/config.env` > built-in default.

| Variable | Meaning | Default |
| --- | --- | --- |
| `EGO_BROWSER_HOST` | Mac that owns the browser | `carries-macbook-air.burro-salmon.ts.net` |
| `EGO_BROWSER_REMOTE_BIN` | Skip discovery, use this path | auto-discovered, cached |
| `EGO_BROWSER_SSH_OPTS` | Extra ssh flags | `-o ConnectTimeout=10 -o BatchMode=yes` |
| `EGO_BROWSER_WAIT` | Seconds to wait for a sleeping Mac | `0` |
| `EGO_BROWSER_DISABLE` | `1` hard-stops the bridge | `0` |

## Remote binary discovery

A non-interactive ssh session does not source an interactive shell rc, so the
`ego-browser` command registered during GUI onboarding is often **not on PATH**.
The shim therefore searches, in order: `~/.local/bin`, `/usr/local/bin`,
`/opt/homebrew/bin`, then `command -v`, then inside the app bundles
(`/Applications/ego lite.app/Contents/**`). The result is cached to
`~/.config/ego-browser/remote.env`.

If ego lite moves, delete that cache file or set `EGO_BROWSER_REMOTE_BIN`.

## First-time setup

1. **Ensure ssh works.** `ssh carries-macbook-air.burro-salmon.ts.net true`
   must succeed non-interactively (key-based). Enable Remote Login on the Mac:
   *System Settings → General → Sharing → Remote Login*.
2. **Install ego lite:** `ego-browser install` — runs upstream's installer on
   the Mac over ssh.
3. **Complete GUI onboarding** *on the Mac*: open ego lite, import Chrome data
   (this is what gives agents the logged-in profile), register the CLI.
4. **Verify:** `ego-browser doctor` — all six checks should pass.

Steps 1 and 3 are inherently hands-on: the first needs a macOS setting toggled,
the second is a GUI wizard. Neither can be driven from Linux.

## Keeping the Mac available — applied 2026-08-23

The bridge is only as good as the Mac's uptime, and this one was dropping off
the tailnet every few minutes. The cause was **not** the idle timer. It runs
**lid closed (clamshell)** on AC, and its own log named the culprit:

```
Sleep  Entering Sleep state due to 'Clamshell Sleep' ... Using AC (Charge:100%)
```

macOS sleeps on lid-close regardless of the idle sleep setting, so `pmset -c
sleep 0` alone does nothing for a clamshell machine. The setting that matters
is `disablesleep`, which is global rather than per-power-source.

Applied and verified:

```bash
sudo pmset -c sleep 0 disksleep 0 standby 0 autopoweroff 0
sudo pmset -a disablesleep 1 womp 1 tcpkeepalive 1
```

On Apple Silicon `autopoweroff` does not exist and is silently ignored — that
is expected, not a failed command. `standby`, `sleep` and `disksleep` all apply.

Confirm with `pmset -g custom` (AC should read `sleep 0`, `disksleep 0`) and
`pmset -g | grep SleepDisabled` (should read `1`). These persist across reboots.

**Battery caveat.** `disablesleep` is global, so if AC is ever lost the machine
stays awake and drains instead of sleeping. macOS still force-sleeps at critical
battery, so this won't corrupt anything — but before unplugging it to travel,
undo it:

```bash
sudo pmset -a disablesleep 0
```

`womp 1` (wake on network) and `tcpkeepalive 1` were already set and are worth
keeping: they let the Mac recover its tailnet presence if it ever does sleep.

## The launchd GUI session — tested, not a problem

This was flagged as the main unknown before the Mac was reachable. It has now
been tested end to end on macOS 26.6.2 (arm64) and **it is not an issue**: a
plain non-interactive ssh session reaches ego lite's services fine, drives the
real profile, and returns page data. `ego-browser doctor` passes all six checks.

The reasoning behind the original concern still holds in general — a process
started from ssh lands in a different launchd bootstrap namespace than the Aqua
session — but ego lite evidently does not depend on a Mach service that the
namespace blocks. Keep the remedies below only as a fallback if a future macOS
or ego lite release regresses this:

1. Keep the Mac logged in to its GUI session with ego lite running.
2. Launch via `ssh mac 'open -a "ego lite"'` — `open` hands off to the GUI session.
3. Last resort: `launchctl asuser $(id -u) …`, which needs root on the Mac.

`doctor` check 6 distinguishes the cases: it now reports plainly when a failure
is an application-level error rather than a broken connection, so a bad probe
can never again be misread as a launchd problem.

## Pitfall: ssh eats stdin

This bit the bridge during bring-up and is worth knowing before editing the
script. **`ssh` reads and discards stdin even when running a remote command.**
A liveness probe like `ssh host true` placed before the forwarding call will
silently swallow the agent's entire heredoc; ego lite then receives empty input
and opens an interactive REPL, which returns a banner and exit code 0. The
result is a call that looks like it succeeded but ran nothing.

Two guards are in place, and both should stay:

- `ssh_ctl()` adds `-n` (stdin from /dev/null) and is used for **every** control
  or probe call. Only `ssh_pipe()` may touch stdin.
- The agent's script is buffered to a temp file **before** any ssh runs.

The audit log is the giveaway if this ever regresses: an entry with a header but
no script body means stdin was consumed upstream.

## Invocation forms

Verified against the shipped CLI:

| Form | Result |
| --- | --- |
| `ego-browser nodejs` + piped stdin | **works** — this is what the bridge uses |
| `ego-browser` + piped stdin, no command | prints usage; does not run the script |
| `ego-browser nodejs -e '<script>'` | hangs waiting on stdin over ssh — avoid |

Do not put `.cell` / `.end` in a piped script; those are interactive-REPL
commands only.

## Deliberate non-goals

- **No stealth.** No fingerprint spoofing, no captcha solving, no OTP
  interception. ego lite works by being a genuine browser on a genuine profile;
  gates are cleared by the human. Adding evasion would break both the security
  model and the reason this approach is trustworthy in the first place.
- **No silent fallback.** When the Mac is down, the bridge fails loudly. A
  fallback to headless Chrome or WebFetch would silently swap an authenticated
  session for an anonymous one and return confidently wrong results.
