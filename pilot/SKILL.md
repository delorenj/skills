---
name: pilot
description: >-
  Drive Plane boards from the command line with `px` (alias of `pilot`), the 33GOD Plane CLI. Use
  whenever a task reads or writes tickets on a Plane board from a repo: listing what's in scope,
  creating a todo or backlog item, claiming, releasing, closing, cancelling or commenting on a
  ticket, moving it to a named lane, capturing a board's schema (states, labels, modules, feature
  toggles) and replaying it onto a fresh board in seconds, or checking which board and mode the
  current repo is bound to. Also the way to file an idea about the CLI itself: `px idea "..."` puts
  a feature request straight into Pilot's own backlog, which is how this tool evolves. Triggers
  include "what's on the board", "add a todo", "create a ticket", "claim/close/cancel this ticket",
  "move it to In Progress", "file this to the backlog", "what board is this repo on", "export the
  board schema", "set up a new board", "px", "pilot". Prefer this over hand-rolled curl against the
  Plane API: px already resolves the board binding, credentials, label deltas and retry behavior.
  Do NOT use for GitHub issues, for Plane workspace administration, or for orchestrating work
  across a board (that is the momo skill).
pipeline-status: new
---

# pilot (`px`): the Plane CLI for agents

`px` is a zero-dependency Node CLI that wraps the Plane API. It exists so an
agent can read and write a repo's ticket board without knowing the board's
UUID, where the credential lives, or how Plane's REST surface is shaped.

**Run it with `--json`.** Every command emits one JSON document on stdout, and
in `--json` mode nothing else is written there, not even for a bad flag.
Errors come back as `{"ok": false, "error": "..."}` with exit 1. Parse that;
don't scrape the human output.

## The commands

This block is generated from px's own command table, the same one `px --help`
prints and px dispatches from, so it cannot disagree with the CLI. If it ever
seems to, `px --help` is right: file the discrepancy with `px idea`.

<!-- px:surface -->
**Every board**

```bash
px todo list                             # what's in immediate scope (the unstarted lanes)
px backlog list                          # what's queued for later (the Backlog lane)
px task list [--group GROUP]             # every issue on the board, with its state
px task create "<title>" [--state NAME]  # create a ticket; no --state: Backlog
px claim <ref>                           # take a ticket: In Progress, assigned to you, labelled agent:working
px release <ref> [-m MSG]                # give it back: Todo, agent:working and your assignment removed
px close <ref> [-m MSG]                  # finish it: Done, agent:working removed (managed: Krebs complete, evidence in -f)
px cancel <ref> [-m MSG]                 # drop it: Cancelled, agent:working removed
px comment <ref> -m MSG                  # leave a note on a ticket without moving it
px idea "<text>"                         # file an idea about px itself into px's own board (PX)
px idea list                             # read the idea box (PX's backlog)
px idea flush                            # deliver ideas still queued locally (~/.local/state/pilot/ideas)
px schema export [-f FILE]               # dump the board's schema as JSON
px board list                            # boards in the workspace
px whoami                                # show the resolved binding and the board's mode
```

**Legacy boards only (no Krebs execution block: every board today)**

```bash
px todo create "<title>"        # add to immediate scope (Todo)
px backlog create "<title>"     # add to the backlog
px move <ref> <state> [-m MSG]  # set a ticket's state by name; nothing else changes
px schema import [-f FILE]      # apply a schema (no -f: your configured default)
px board create NAME [-i ID]    # create a board and apply your default schema
px board delete --force         # destroy the bound board and everything on it
```

**Krebs-managed boards only (execution.mode managed|shadow; needs --actor)**

```bash
px task handoff|complete|attention|resume|takeover|status <ref>  # worker lifecycle through Krebs (claim, release, cancel, comment: the top-level verbs)
px task get|update|review <ref>                                  # provider reads and evidence through Krebs
px task start|heartbeat|finish <ref>                             # supervised run steps (also as px run <op>)
px task plan|reevaluate|override|reconcile|planner [<ref>]       # PM and operator operations
px run start|heartbeat|finish <ref>                              # a step of a supervised run (success never means Done)
```
<!-- /px:surface -->

`px <command> --help` explains one command and says whether it runs on the
board you are standing on. `--dry-run` works on claim, release, close, cancel,
comment, move and schema import: it resolves the ticket and the lane, prints
what would happen, and writes nothing. A flag a command does not read is
refused, never silently ignored.

`px task claim|release|close|cancel|comment|move` are accepted as aliases of
the top-level verbs, so the Krebs spelling and the obvious guess both work.

## Which kind of board you are on

A board is **legacy** unless its repo's `.project.json` carries an `execution`
block in `managed` or `shadow` mode, in which case it is **Krebs-managed**.
Every board is legacy today: Krebs is installed but no board is enrolled.
`px whoami` prints the mode.

- On a legacy board px writes Plane directly.
- On a Krebs-managed board, `claim`, `release`, `close`, `cancel`, `comment`
  and `task create` become signed Krebs commands, every command needs an
  enrolled actor (`--actor` or `PILOT_ACTOR_ID`), and direct writes (`move`,
  `todo create`, `schema import`, ...) are refused.

A command that does not run on the current board fails with a message that
names what to run instead, e.g. `px task handoff` on a legacy board points at
`px move <ref> <next lane> -m MSG`.

## Working a ticket

```bash
px claim PX-3                         # In Progress, assigned to the key's user, agent:working
px comment PX-3 -m "found the cause"  # a note, no move
px move PX-3 "E2E Testing & QA" -m "ready for QA"   # any other lane, strictly by name
px close PX-3 -m "what you did"       # Done, agent:working removed
px release PX-3 -m "blocked on X"     # back to Todo, marker and your assignment removed
px cancel PX-3 -m "superseded by PX-9"              # Cancelled, marker removed
```

Refs accept `PX-3`, `3`, `33GOD-68` (identifiers may start with a digit), or a
raw uuid. **A ref whose prefix names another board is refused**: run px from
the repo bound to that board.

Lanes resolve strictly. `in_progress` finds "In Progress", and a Plane group
name (`cancelled`) works only when the board has exactly one state in it; a
miss is an error that lists the board's lanes, never a guess. `--state NAME`
overrides a verb's own lane with the same strictness.

`px move` changes the state and nothing else. `-m` posts the comment even when
the ticket is already in that lane: the comment is the audit record, and two
workflow phases can share one lane. Retrying after an uncertain failure? Check
`moved.changed` before sending `-m` again, or the comment lands twice.

### agent:working

`agent:working` is how a human tells "an agent is on this" from "nobody has
touched this". The n8n Ticket Pickup Chip owns it during an agent turn and
keeps it at turn end only when the ticket was claimed (moved to the state
named In Progress, or assigned). Apart from that, only `px claim` (adds it)
and `px release|close|cancel` (remove it) touch it. Never add or remove it by
hand.

Labels and assignees are written as deltas on a fresh read: Plane's `PATCH`
replaces the whole list, so px re-reads the ticket and adds or removes only its
own ids. Assignment is a union, so claiming never unassigns a teammate.

### Events

px publishes nothing on the bus for its Plane writes. The n8n `Plane →
Bloodbank` normalizer turns the webhook into `bloodbank.repo.task.created` /
`updated` / `appended`. Creating or moving a ticket with px is how an agent
announces it, so never publish those facts yourself.

## Where the board comes from

The nearest `.project.json` → `ticket_provider`, walking up from the current
directory, picks the board. That file is the SSOT the whole fleet uses, so
every agent in a repo resolves to the same board.

- `--workspace` / `--board` and `PLANE_WORKSPACE` / `PLANE_BOARD` override it,
  but a board other than the bound one must be registered in the Krebs
  ownership registry (`~/.config/krebs/manifests.json` or `KREBS_MANIFESTS`),
  or px refuses. No registry exists on this host, so to work another board,
  `cd` into the repo bound to it.
- `~/.config/pilot/config.json` (`defaultWorkspace`, `base`, `apiKey`,
  `defaultSchema`) is a fallback for when nothing is bound, never an override.

`px whoami` shows what resolved and from which file. Run it first when a
command targets the wrong board.

Credentials come from `PLANE_API_KEY`, or an `op://` reference read through
the 1Password CLI at the moment of use. A raw key is never written to disk.

## The idea box: read this part

`px idea "..."` is a direct line into Pilot's **own** backlog (PX).

It is the one command that ignores your current repo's board on purpose.
`px todo create` is about the repo you're standing in; `px idea` is about the
tool you're standing on. It works from any repo on any host.

**Use it.** If you reach for `px` and it can't do the thing you wanted, that
gap is the single most valuable signal this tool can receive. Don't work
around a missing command silently and don't hand-roll curl to route around it.
File it:

```bash
px idea "bulk-close every issue in a completed cycle" \
  --context "cleaning up after a release, closed 14 by hand" \
  --command "px close" --workaround "a shell loop over px close" --json
```

The idea is queued locally first (`~/.local/state/pilot/ideas`), so a failed
delivery is never lost: it comes back as `queued` with the reason, and
`px idea flush` delivers it later. A repeat of the same idea is deduplicated.
`--desired` alone also works as the idea text. Then carry on and solve your
task another way.

## Standing up a new board

Setting up a board by hand is ~10 minutes of clicking through feature toggles,
default states, labels and modules. Instead:

```bash
px board create "New Thing" -i NEW   # ~3 seconds, fully set up
```

`board create` applies the configured default schema (`defaultSchema` in
`~/.config/pilot/config.json`; on this host the 33GOD lane canon). Pass
`-f FILE` for a one-off schema, or `--no-schema` for Plane's bare defaults.
`px schema export -f FILE` captures a board you like.

**`schema import` is an upsert keyed on name, never a replace.** Running it
twice writes nothing the second time. Run `--dry-run` first; it prints the
exact plan. What the schema doesn't mention is reported as `extra` and left
alone: `--prune` removes extra states (Plane refuses one that holds issues),
`--prune-all` also removes extra labels (stripping them from every issue), and
modules are never removed. The default state never moves on a board that
already holds tickets unless you pass `--adopt-default`.

Covers states, labels, modules and the project feature toggles. Does **not**
cover estimates or views: they are absent from Plane's public v1 API.
`Triage` cannot be a custom state name (Plane reserves it); px says so in
plain words.

## What isn't built yet

`spike` (PX-3) and a triage pipeline (PX-4) are open questions, tracked in the
idea box rather than guessed at. Need one of them, or anything else px can't
do? Say so with `px idea`.
