---
name: pilot
description: >-
  Drive Plane and Trello boards from the command line with `px` (alias of `pilot`), the 33GOD
  board CLI. Use whenever a task reads or writes tickets on a Plane or Trello board from a repo
  (IntelliForia's INT board is Trello; the same commands and --json work there): listing what's in scope,
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

# pilot (`px`): the Plane and Trello CLI for agents

`px` is a zero-dependency Node CLI that wraps the Plane and Trello APIs. It
exists so an agent can read and write a repo's ticket board without knowing the
board's id, where the credential lives, or how the provider's REST surface is
shaped. `.project.json` `ticket_provider.type` picks the provider; a Trello
repo runs the same commands with the same `--json` (see "Trello boards").

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
px todo list                                                                             # what's in immediate scope (the unstarted lanes)
px backlog list                                                                          # what's queued for later (the Backlog lane)
px task list [--group GROUP] [--scope LABEL]                                             # every issue on the board, with its state
px show <ref>                                                                            # print one ticket: lane, labels, people, description, checklists, sub-issues, comments
px task get <ref>                                                                        # one ticket as data: on a legacy board what px show prints; managed: the Krebs snapshot
px task create "<title>" [--state NAME]                                                  # create a ticket; no --state: Backlog (managed: Krebs create, lands in Backlog)
px claim <ref>                                                                           # take a ticket: In Progress, assigned to you, labelled agent:working
px release <ref> [-m MSG]                                                                # give it back: Todo, agent:working and your assignment removed
px close <ref> [-m MSG]                                                                  # finish it: Done, agent:working removed (managed: Krebs complete)
px cancel <ref> [-m MSG]                                                                 # drop it: Cancelled, agent:working removed
px comment <ref> -m MSG                                                                  # leave a note on a ticket without moving it
px idea "<text>"                                                                         # file an idea about px itself into px's own board (PX)
px idea list                                                                             # read the idea box (PX's backlog)
px idea flush                                                                            # deliver ideas still queued locally (~/.local/state/pilot/ideas)
px schema export [-f FILE]                                                               # dump the board's schema as JSON
px schema import [-f FILE]                                                               # apply a schema (no -f: your configured default); managed boards: --dry-run only
px identity verify --employee ID --key-ref op://... --user-id UUID [--board UUID|IDENT]  # prove a key is exactly that employee's native Plane user and a member of the board; secret-free result (Plane boards)
px board list                                                                            # boards in the workspace
px epic list [--include-inactive]                                                        # the live epics on this board, with their epic:<slug> handle
px epic show <ref>                                                                       # an epic and its members on every board, each valid, inactive or unresolvable
px link list <ref>                                                                       # every relation a ticket takes part in, from either end, epic memberships marked
px whoami                                                                                # show the resolved binding, the board's provider and mode
```

On a Krebs-managed board the verbs above take the Krebs flags and an -f payload instead of -m, --state, --dry-run, -d, -l, --parent and --priority; px <command> --help there lists them.

**Documents (no board binding; runs from anywhere)**

```bash
px harvest <document.md> [-o FILE]                 # pull the action items a markdown document states or clearly implies into a provider-agnostic artifact, as standalone sentences with their evidence, grouped by project
px harvest publish <actionitems.json> [--dry-run]  # file a harvest's board groups as tickets on each project's own board; idempotent; held items only with --include-held, the general group only with --general-to
px harvest schema [--list | --activate FILE]       # open the active harvest schema in $EDITOR (backed up before it is overwritten, never deleted); --list shows every schema, * marks the active one
```

**Legacy boards only (no Krebs execution block: every board today)**

```bash
px identity comment <ref> -m MSG --idempotency-key KEY --employee ID --key-ref op://... --user-id UUID  # verify, then post one marked comment as that employee; reconciles by marker before any retry (Plane boards)
px todo create "<title>"                                                                                # add to immediate scope (Todo)
px backlog create "<title>"                                                                             # add to the backlog
px move <ref> <state> [-m MSG]                                                                          # set a ticket's state by name; nothing else changes
px epic create "<title>"                                                                                # create an epic on this board: a ticket labelled epic:<slug>, refused when a live epic has the slug
px epic add <epic> <ref>...                                                                             # make tickets on any board members of an epic (one relation each, read back; a re-run is safe)
px link add <ref> <ref> [--blocks]                                                                      # relate two tickets on any boards; --blocks: the first blocks the second
px board create NAME [-i ID]                                                                            # create a board and apply your default schema
px board delete --force                                                                                 # destroy the bound board and everything on it
```

**Krebs-managed boards only (execution.mode managed|shadow; needs --actor)**

```bash
px task handoff|complete|attention|resume|takeover|status <ref>  # worker lifecycle through Krebs (claim, release, cancel, comment: the top-level verbs)
px task update|review <ref>                                      # field updates and review evidence through Krebs
px task start|heartbeat|finish <ref>                             # supervised run steps (also as px run <op>)
px task plan|reevaluate|override|reconcile|planner [<ref>]       # PM and operator operations
px run <op> <ref>                                                # any Krebs operation from inside a supervised run: start, heartbeat, finish, planner (success never means Done)
```
<!-- /px:surface -->

`px <command> --help` explains one command, says whether it runs on the
board you are standing on, and lists the flags it takes there. On a legacy
board `--dry-run` works on claim, release, close, cancel, comment and move
(and `schema import` takes it on any board): it resolves the ticket and the
lane, prints what would happen, and writes nothing. A flag or extra argument a
command does not read is refused, never silently ignored: `px close PX-3
"fixed it"` fails with `did you mean -m "fixed it"?` instead of closing
without the comment.

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
names the legacy equivalent or says there is none, e.g. `px task handoff` on a
legacy board points at `px move <ref> <next lane> -m MSG`.

## Trello boards

When `ticket_provider.type` is `trello` (IntelliForia), px drives the Trello
board with the same verbs and `--json` keys (`sequence_id` is the card number:
`INT-421` is card 421; `state` is the list id). What differs:

- **Lanes come from the repo's `.momo/config.json` lane map** (Momo's file;
  px only reads it). Lists map to bands: backlog, unstarted, started,
  in_review (reported as group `started`), completed, cancelled.
- **Strict lanes.** `claim` lands on "In Progress" and `close` on the one
  completed list by name. `release` and `todo create` need the band's
  `write_targets` entry in that map. INT's names `unstarted: Priority`
  (landing with PX-17), so there they land on Priority as they land on Todo on
  Plane. Where a map names none, they refuse and say so: pass `--state`, never
  expect px to pick.
- **`px show` prints a card's checklists.** INT keeps acceptance criteria in
  Trello checklists, often nowhere in the description: read them before working
  the card (`checklists` in `--json`, `- [ ]`/`- [x]` lines after the
  description). On Plane the key is `[]`; a task list there is in the
  description.
- **Drift refuses.** If a list the map names was renamed in Trello, commands
  touching that band fail with `code: lane_map_drift`. Fix the map, not px.
- **cancel** on a board with no Cancelled list archives the card and labels it
  `cancelled`; `task list` still counts it, and `move`/`claim`/`release`/`close`
  revive it. A card someone archived by hand is refused for writes.
- `--priority` becomes a label (`High priority` / `priority:high`), `--parent`
  a `Parent: <title>` link on the new card, and `px show` also takes a card id
  or a `trello.com/c/` link.
- `px show INT-421` works from any repo (through the pjangler registry), and
  `px show PX-17` works from IntelliForia. `px idea` still files on PX.
- Plane only: `px identity`, Krebs commands, modules. On a real board run only
  reads; the Trello scratch board for live writes is pilot's
  `test/board-trello` (`mise run px:test:trello -- <args>`).

## Working a ticket

On a legacy board (every board today):

```bash
px show PX-3                          # read it first: lane, labels, description, checklists, sub-issues, comments
px claim PX-3                         # In Progress, assigned to the key's user, agent:working
px comment PX-3 -m "found the cause"  # a note, no move
px move PX-3 "E2E Testing & QA" -m "ready for QA"   # any other lane, strictly by name
px close PX-3 -m "what you did"       # Done, agent:working removed
px release PX-3 -m "blocked on X"     # back to Todo, marker and your assignment removed
px cancel PX-3 -m "superseded by PX-9"              # Cancelled, marker removed
```

Refs accept `PX-3`, `3`, `33GOD-68` (identifiers may start with a digit), or a
raw uuid. **A ref whose prefix names another board is refused** by every verb
that writes, on legacy and managed boards alike: run px from the repo bound to
that board. `px show` is the exception because it only reads: `px show FLUME-15`
finds that ticket from any repo in the workspace (add `--workspace` for a board
in another one). `--json` gives `{ok, ticket}`, the shape of the Krebs get
receipt, and on a legacy board `px task get` prints the same.

An epic's stories hang off it as sub-issues: `px task create "Story" --parent
FLUME-16 --priority high` files one under FLUME-16 on the same board, and
`px show FLUME-16` lists them with their lanes.

Lanes resolve strictly. `in_progress` finds "In Progress", and a Plane group
name (`cancelled`) works only when the board has exactly one state in it; a
miss is an error that lists the board's lanes, never a guess. `--state NAME`
overrides a verb's own lane with the same strictness.

`px move` changes the state and nothing else. `-m` posts the comment even when
the ticket is already in that lane: the comment is the audit record, and two
workflow phases can share one lane. Retrying after an uncertain failure? Check
`moved.changed` before sending `-m` again, or the comment lands twice.

### Field updates on legacy boards

pilot (px): an opinionative Plane CLI for 33GOD

usage: px <command> [args] [flags]
this board: FLUME, legacy

every board
  todo list                       what's in immediate scope (the unstarted
                                  lanes)
  backlog list                    what's queued for later (the Backlog lane)
  task list [--group GROUP]       every issue on the board, with its state
  show <ref>                      print one ticket: lane, labels, people,
                                  description, sub-issues, comments
                                  FLUME-15 works from any repo (a read; refs
                                  naming another board are refused only for
                                  writes)
  task get <ref>                  one ticket as data: on a legacy board what px
                                  show prints; managed: the Krebs snapshot
  task create "<title>" [--state NAME]
                                  create a ticket; no --state: Backlog (managed:
                                  Krebs create, lands in Backlog)
  claim <ref>                     take a ticket: In Progress, assigned to you,
                                  labelled agent:working
  release <ref> [-m MSG]          give it back: Todo, agent:working and your
                                  assignment removed
  close <ref> [-m MSG]            finish it: Done, agent:working removed
                                  (managed: Krebs complete)
  cancel <ref> [-m MSG]           drop it: Cancelled, agent:working removed
  comment <ref> -m MSG            leave a note on a ticket without moving it
  idea "<text>"                   file an idea about px itself into px's own
                                  board (PX)
  idea list                       read the idea box (PX's backlog)
  idea flush                      deliver ideas still queued locally
                                  (~/.local/state/pilot/ideas)
  schema export [-f FILE]         dump the board's schema as JSON
  schema import [-f FILE]         apply a schema (no -f: your configured
                                  default); managed boards: --dry-run only
                                  --dry-run first; --prune removes extra states,
                                  --prune-all labels too
  board list                      boards in the workspace
  whoami                          show the resolved binding and the board's mode
  On a Krebs-managed board the verbs above take the Krebs flags and an -f
  payload instead of -m, --state, --dry-run, -d, -l, --parent and --priority; px
  <command> --help there lists them.

legacy boards only (no Krebs execution block: every board today)
  todo create "<title>"           add to immediate scope (Todo)
  backlog create "<title>"        add to the backlog
  move <ref> <state> [-m MSG]     set a ticket's state by name; nothing else
                                  changes
                                  in_progress finds "In Progress"; a group
                                  (cancelled) only when the board has one state
                                  in it
                                  -m posts the audit comment, even when the
                                  state is already right
  board create NAME [-i ID]       create a board and apply your default schema
                                  -f FILE for a specific schema, --no-schema for
                                  Plane's bare defaults
  board delete --force            destroy the bound board and everything on it

Krebs-managed boards only (execution.mode managed|shadow; needs --actor)
  task handoff|complete|attention|resume|takeover|status <ref>
                                  worker lifecycle through Krebs (claim,
                                  release, cancel, comment: the top-level verbs)
  task update|review <ref>        field updates and review evidence through
                                  Krebs
  task start|heartbeat|finish <ref>
                                  supervised run steps (also as px run <op>)
  task plan|reevaluate|override|reconcile|planner [<ref>]
                                  PM and operator operations
  run <op> <ref>                  any Krebs operation from inside a supervised
                                  run: start, heartbeat, finish, planner
                                  (success never means Done)
                                  px-supervised <ref> --actor ID --run-id ID --
                                  <worker argv> wraps run start

flags:
      --json                      one JSON document on stdout, nothing else
                                  (agents: always)
  -h, --help                      this; px <command> --help for one command
  -v, --version                   print the version
  -w, --workspace SLUG            workspace override (see binding below)
  -b, --board UUID                board override (see binding below)
      --base URL                  Plane base URL (default https://plane.delo.sh)
      --actor ID                  enrolled actor (or PILOT_ACTOR_ID); required
                                  on managed boards

tickets:
  -m, --message MSG               the comment for comment; on a legacy board
                                  also posted with release, close, cancel or
                                  move
      --state NAME                legacy boards: land in this state instead of
                                  the verb's own (strict: exact name, or a group
                                  the board has one of)
      --dry-run                   resolve and print what would happen, write
                                  nothing (legacy ticket writes; schema import
                                  on any board)
  -d, --description TEXT          legacy boards: body text for create; blank
                                  lines, - and 1. lists, # headings and `code`
                                  keep their layout in Plane
  -l, --labels a,b                legacy boards: comma-separated labels for
                                  create, created if missing; lifecycle: and
                                  agent: labels are refused (automation only)
      --parent REF                legacy boards: create it as a sub-issue of
                                  this ticket (an epic), on the same board
      --priority LEVEL            legacy boards: create with this priority
                                  (urgent, high, medium, low, none)
      --group GROUP               task list: one Plane state group (backlog,
                                  unstarted, started, completed, cancelled)

schema and boards:
  -f, --file FILE                 schema file to read or write; on managed
                                  boards, the lifecycle payload JSON
      --prune                     schema import: delete STATES the schema omits
                                  (Plane refuses one that holds issues)
      --prune-all                 schema import: also delete LABELS it omits,
                                  stripping them from every issue. Modules are
                                  never deleted
      --adopt-default             schema import: move the default state even on
                                  a board that holds tickets
  -n, --name NAME                 board create: board name (or the positional)
  -i, --identifier ID             board create: identifier, e.g. PX (default:
                                  from the name)
      --no-schema                 board create: skip the default schema
      --force                     board delete: required

px idea (structured feedback):
      --from NAME                 who is filing it, when no actor is enrolled
      --context TEXT              what you were doing
      --ticket REF                the ticket you were working
      --command CMD               the px command you tried
      --workaround TEXT           what you did instead
      --desired TEXT              the behavior you wanted (also the idea text
                                  when none is given)

Krebs commands (managed boards; -f carries the payload):
      --run-id ID                 supervised run id (or KREBS_RUN_ID)
      --generation N              lease generation
      --revision N                expected ticket revision
      --command-id UUID           command id (default: random)
      --idempotency-key KEY       idempotency key (default: the command id)
      --correlation-id UUID       correlation id (default: the command id)
      --causation-id UUID         causation id (default: the command id)
      --operation-id ID           operation id carried in the payload
      --retry-command UUID        resend the exact persisted command body

binding: the nearest .project.json ticket_provider (walking up from cwd) picks the
  board; ~/.config/pilot/config.json can only fill in the workspace, base URL, key
  and default schema. --board/PLANE_BOARD naming any other board is refused unless
  the Krebs ownership registry lists its manifest (~/.config/krebs/manifests.json,
  or KREBS_MANIFESTS as a JSON array of .project.json paths); otherwise run px from
  a directory whose .project.json binds the board you want.
refs: PX-3, 3 or a uuid; a ref whose prefix names another board is refused,
  except by px show, which only reads and finds any board's ticket in the workspace.
credentials: PLANE_API_KEY, else an op:// reference read through 1Password at use
  time; a managed board uses the enrolled actor's key, never a shared one.
run 'px whoami' to see exactly what resolved. on a legacy board can only comment, move state, claim/release/close/cancel,
and create. It has **no verb for description, priority, or parent updates** on
an existing ticket ( is Krebs-managed only). Do not reach for
 — the Plane REST surface requires workspace/board UUIDs the skill
deliberately hides, and a raw PATCH against the wrong workspace is how tickets
get written to the wrong board. Instead, use the local  venv
to call  — the same stdio route
 documents for label deltas. Write the description HTML to
a temp file first () so the Python
caller can read it without shell-escaping pain. Verify with  afterward —  can come back empty even when the write
landed; trust  length and a visual spot-check of the opener.

### Field updates on legacy boards

`px` on a legacy board can only comment, move state, claim/release/close/cancel,
and create. It has **no verb for description, priority, start-date, or parent
updates** on an existing ticket (`px task update` is Krebs-managed only). Do
not reach for `curl` — the Plane REST surface requires workspace/board UUIDs
the skill deliberately hides, and a raw PATCH against the wrong workspace is
how tickets get written to the wrong board. Instead, use the local
`plane-mcp-server` venv to call `workitem(action="update", project_id=...,
workitem_id=..., description_html=..., start_date=..., priority=..., parent=...)` — the same stdio route `project-lifecycle` documents for label
deltas. Write the description HTML to a temp file first (`cat > /tmp/desc.html
<<'EOF' ... EOF`) so the Python caller can read it without shell-escaping pain.
Verify with `px show <ref> --json` afterward — `description_text` can come
back empty even when the write landed; trust `description_html` length and a
visual spot-check of the opener.

### Labels on legacy boards

`px` has no label-add verb on a legacy board (`task update` is Krebs-only;
`px` refuses `lifecycle:` / `agent:` labels on `task create` anyway). To add
or remove a label on an existing legacy-board ticket, use
`project-lifecycle`'s `scripts/plane_stdio_label.py` — run it with the
plane-mcp-server venv python, never system python (the script imports `mcp`,
and the runtime python's `mcp` has broken transitive deps). Always `px
comment` first so the audit trail lives on the ticket, then add the label
last.

### Epics, links and virtual boards (Plane)

- **Virtual board**: on a board several repos share (TOLT), your repo's
  `.project.json` carries `scope_label` (`repo:game`). px stamps it on every
  create, lists only your repo's tickets (`--scope forge` or `--scope all` to
  look wider) and refuses to claim/move/close/comment another repo's ticket
  (`cross_scope_write`): `cd` to that repo. Never pass `-l repo:...` yourself.
- **Epic**: `px epic create "<title>"` makes a ticket labelled `epic:<slug>`;
  `px epic add <epic> <ref>...` joins tickets on ANY board to it (many-to-many);
  `px epic show <epic>` lists members; `px show <ref>` lists a ticket's epics.
  Never write an `epic:` label by hand, never use `--parent` for an epic
  (that is a same-board sub-issue).
- **Link**: `px link add A B` (relates), `px link add A B --blocks` (A blocks B),
  `px link list A`.
- Relations cannot be removed. px checks before it writes and refuses a pair
  that already has another kind of link; to undo a membership, cancel the epic
  and make a new one. On a refusal read its `code`
  (`relation_type_conflict`, `unknown_board_mode`, `epic_endpoint`...), don't retry.

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

- `--workspace` / `PLANE_WORKSPACE` override the workspace. `--board` /
  `PLANE_BOARD` naming any board other than the bound one is refused unless
  the Krebs ownership registry lists that board's manifest
  (`~/.config/krebs/manifests.json`, or `KREBS_MANIFESTS` holding a JSON array
  of `.project.json` paths). No registry exists on this host, so to work
  another board, `cd` into the repo bound to it.
- `~/.config/pilot/config.json` (`defaultWorkspace`, `base`, `apiKey`,
  `defaultSchema`) is a fallback for when nothing is bound, never an override,
  and it cannot supply a board.

`px whoami` shows what resolved and from which file. Run it first when a
command targets the wrong board.

Credentials come from `PLANE_API_KEY`, or an `op://` reference read through
the 1Password CLI at the moment of use. On a Trello board they are
`TRELLO_API_KEY` and `TRELLO_TOKEN` (values or `op://` references), never
`PLANE_*`, and px never reads `TRELLO_BOARD_ID`. A raw key is never written to
disk, and `px whoami` never prints one.

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
`--desired` alone also works as the idea text. An idea that is a lone
subcommand word (reconcile, ls, help) is refused rather than filed. Then carry
on and solve your task another way.

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

## Spikes and triage

A spike is a label, not a command: `px task create "..." -l spike`. Triage is
the n8n Ticket Grooming lane, which latches `lifecycle:triaged` on its own;
`lifecycle:` and `agent:` labels are automation-only, so `px` refuses them on
create. Need something px can't do? Say so with `px idea`.
