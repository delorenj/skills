---
name: pilot
description: Drive Plane boards from the command line with `px` (alias of `pilot`), the 33GOD Plane CLI. Use whenever a task involves reading or writing tickets on a Plane board from a repo — listing what's in scope, creating a todo or backlog item, dumping a board's states and labels, or checking which board the current repo is bound to. Also the way to file an idea about the CLI itself: `px idea "..."` puts a feature request straight into Pilot's own backlog, which is how this tool evolves. Triggers include "what's on the board", "add a todo", "create a ticket", "file this to the backlog", "what board is this repo on", "export the board schema", "px", "pilot". Prefer this over hand-rolled curl against the Plane API — it already resolves the board binding, credentials, and retry behavior. Do NOT use for GitHub issues, for Plane workspace administration, or for orchestrating work across a board (that is the momo skill).
pipeline-status: new
---

# pilot (`px`) — the Plane CLI for agents

`px` is a zero-dependency Node CLI that wraps the Plane API. It exists so that
an agent can read and write a repo's ticket board without knowing the board's
UUID, where the credential lives, or how Plane's REST surface is shaped.

**Run it with `--json`.** Every command emits a stable machine-readable object
on stdout, and in `--json` mode nothing else is written there — no banners, no
progress. Errors come back as `{"ok": false, "error": "..."}` with exit 1.
Parse that; don't scrape the human output.

## The commands

```bash
px todo list                    # what's in immediate scope
px todo create "<title>"        # add to immediate scope
px backlog list                 # what's queued for later
px backlog create "<title>"     # add to the backlog
px task list                    # every issue, no state filter
px task create "<title>" --state "In Progress"

px idea "<text>"                # file an idea about px itself
px idea list                    # read the idea box

px schema export [-f FILE]      # dump states + labels as json
px whoami                       # show the resolved board binding
```

Useful flags: `-d/--description`, `-l/--labels a,b` (labels are created if they
don't exist), `--state NAME`, `-w/--workspace`, `-b/--board`, `--from NAME`.

`todo` and `backlog` are presets over the same `task` primitive — they differ
only in which state a new issue lands in. There is one code path, so the
shortcuts cannot drift from the thing they wrap.

## Where the board comes from

Binding resolves in this order, highest first:

1. flags (`--workspace`, `--board`, `--base`)
2. env (`PLANE_WORKSPACE`, `PLANE_BOARD`, `PLANE_BASE`)
3. `~/.config/pilot/config.json`
4. **repo-root `.project.json` → `ticket_provider`** ← the normal path
5. defaults (`https://plane.delo.sh`)

Step 4 is the one that matters: `.project.json` is the SSOT the whole fleet
already uses, so every agent in a repo resolves to the same board. If a command
reports no binding, the repo probably isn't a pjangler CommonProject — run
`px whoami` to see exactly what resolved and from which file.

Credentials come from `PLANE_API_KEY`, or an `op://` reference read through the
1Password CLI at the moment of use. A raw key is never written to disk.

## The idea box — read this part

`px idea "..."` is a direct line into Pilot's **own** backlog.

This is the one command that ignores your current repo's board on purpose.
`px todo create` is about the repo you're standing in; `px idea` is about the
tool you're standing on. An idea filed from any repo, on any host, lands in the
PX board tagged `idea` and `from-agent`, with attribution for who filed it and
what they were doing at the time.

**Use it.** If you reach for `px` and it can't do the thing you wanted, that
gap is the single most valuable signal this tool can receive — you are the
user, mid-task, with the context fresh. Don't work around a missing command
silently and don't hand-roll curl to route around it. File it:

```bash
px idea "wish px could bulk-close every issue in a completed cycle" \
  --from "$AGENT_NAME" \
  --context "was cleaning up after a release and closed 14 by hand"
```

Then carry on and solve your task another way. The point is that the roadmap
becomes a product of real usage rather than guesswork.

## What isn't built yet

`px schema import` is deliberately absent. Its semantics are genuinely
undecided — idempotent upsert vs. replace-the-world, and what should happen to
tickets sitting in a state that an imported schema removes. Running it returns
a clear error pointing at the idea box rather than guessing and destroying a
board. `spike` and a triage pipeline are likewise deferred until there's a real
need recorded.

If you need one of these, say so through `px idea` — that's the mechanism.
