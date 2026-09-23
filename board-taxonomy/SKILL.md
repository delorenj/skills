---
name: board-taxonomy
description: How 33GOD models ticket state on a Plane board — which facts belong in a state, which in a label, and which axis a new label joins. Use when adding or renaming a Plane label, deciding between a label and a state, wiring automation that writes to a board, scaffolding a new project board, or reconciling boards that have drifted apart.
---

# 33GOD Board Taxonomy

A Plane board carries several different kinds of fact, and Plane offers only two
carriers for them: **states** and **labels**. Left alone, everything becomes a
label. Measured across the 25 fleet-bound boards on 2026-09-04: **75 distinct
label names, 72 of them on exactly one board**, and `bug` in three different
colours. See [references/field-survey.md](references/field-survey.md).

That happened because nothing was wrong with any single decision. Labels are
authored *at runtime* by whichever agent needs one first — the grooming prompt
says "add `lifecycle:triaged`", the agent finds it missing, and the `label`
MCP tool creates it. Same prompt, same model, different name every time. The
fix is not discipline; it is a declared, closed set.

## The one test

Do not classify a label by what it means. Classify it by **who writes it and
what clears it.** That single question resolves every case below.

| kind | cleared by | carrier | exclusive |
|---|---|---|---|
| **Position** — where it is in the pipeline | a human or agent moving it | Plane **state** | yes, structurally |
| **Latch** — automation recorded a fact | the next pipeline stage | `lifecycle:` label | one per axis |
| **Lease** — a process is holding it right now | the holder, or a sweeper | `agent:` label | one per axis |
| **Facet** — a durable property of the ticket | someone deciding it is false | `xp:`, `risk:`, `needs:`, bare words | no |

### Latch vs lease — the distinction that matters

Ask: **if the process holding this dies, does the label become a lie?**

- `agent:working` — yes. It is a **lease**, not a state. It must self-clear, and
  it must be safe to force-clear, because the thing it describes is a running
  turn that can vanish.
- `lifecycle:triaged` — no. Grooming really did finish; that stays true forever.
  It is a **latch**.

This is operational, not cosmetic. Leases need a TTL and a sweeper. Latches need
neither. Getting it wrong leaves permanent lies on the board.

## The axes

Closed set. Anything with a colon must appear here.

| axis | kind | writer | values |
|---|---|---|---|
| `lifecycle:` | latch, exclusive | automation only | `triaged`, `needs-input`, `blocked` |
| `agent:` | lease, exclusive | automation only | `working`, `failed` |
| `xp:` | facet, exclusive | either | `internal`, `external` |
| `risk:` / `needs:` | facet, multi | either | open within the axis |

Everything else is a **bare word**, descriptive, per-project, and nobody's
business but that board's: `bug`, `docs`, `spike`, `security`.

## Rules

1. **Position never goes in a label.** You have a 9-state machine; use it. A
   label that answers "where is this in the pipeline" is a bug. This is what
   rules out `phase:0/1/2`, `scope:proposed`, `blocked-by:M0`.
2. **One writer per exclusive axis.** Plane cannot enforce exclusivity — GitLab
   has scoped labels (`key::value` replaces within `key`), Plane has nothing —
   so the writer enforces it. Corollary: **if a human has to hand-set it, it
   belongs in the state machine instead.**
3. **A colon means machine-readable and closed.** Bare words are descriptive and
   open. This is checkable: any colon label not in the table above is either a
   mistake or an axis someone forgot to declare.
4. **Colour encodes the axis, not the value** — one family per axis, one shade
   per value within it. Not hypothetical tidiness: by the time the set was
   closed, `lifecycle:triaged` had already reached two colours (teal on JIMB,
   amber on 33GOD), exactly the way `bug` reached three.
5. **Cap the functional set at ~8.** The cost was never filtering — 75 labels
   filter fine. It is that every agent re-invents a name it cannot look up.
   Eight is memorizable. Descriptive labels can grow freely per project.

## Where this is declared

A standards document rots exactly the way those 75 labels did. The taxonomy is
real only where it is (a) in a file the agent already reads and (b) provisioned
by a tool. Both seams exist:

- **Declaration** — `.project.json`, `activity_report.board.exposure_labels`.
  Already on `groomingPrompt`'s read path. Today only `james-brennan` declares
  it, and only for the `xp:` axis.
- **Provision** — `bloodbank/bin/bb-board-scaffold`, `FUNCTIONAL_LABELS`.

Keep those two in agreement. When they disagree, the declaration wins and the
scaffolder is wrong.

## Scaffolding a new board

Plane exposes **no template API** on this instance — `/templates/`,
`/project-templates/` and `/workitem-templates/` all 404 — and **no issue
types** (404), which is why classification has to be labels at all. States *are*
fully writable over v1.

```bash
bb-board-scaffold                          # dry run over every fleet board
bb-board-scaffold --to DELO,DNET --apply
bb-board-scaffold --from JIMB --all --apply
```

It clones the reference board's state machine and provisions the functional
labels.

**States** it only adds and aligns:

- never deletes a state, and never reorders one it did not create;
- never touches `default` or `is_triage` — a board must have exactly one default
  state, and moving it silently re-homes every new ticket;
- refuses a board reporting zero states, which is the signature of a
  soft-deleted project, not an empty one.

**Labels** it adds, and **recolours where they have drifted**. Colour is
cosmetic — unlike a state's group it can be corrected without moving anything —
so this is what actually keeps one name to one colour across 25 boards. Any
colon label outside the closed set is reported as `? undeclared colon labels`
and never touched: deleting a label strips it from every ticket carrying it,
and that does not come back.

33GOD and JIMB hold byte-identical 9-state machines and either is a sound
reference. Note that `--all` excludes the reference board itself, so its own
labels go unreconciled; follow with `bb-board-scaffold --to <ref> --apply`.

## The ack chip, as a worked example

`agent:working` exists because a ticket sat visibly untouched for the entire
time its agent was booting — 377s, 633s and 2596s measured on three JIMB
tickets. No instruction in an agent's prompt can close that gap, because the gap
*is* the agent starting up. The acknowledgement has to come from the pipeline.

The n8n **Ticket Pickup Chip** workflow (`wWXgCZiiIBWaRRzE`, n8n-nodes-bloodbank
0.7.2) owns it. It listens on one ordered durable trigger for the gateway's
`agent.invocation.started` / `.completed` / `.failed` events whose echoed
`data.context.reason` is `ticket-grooming` or `ticket-delegation`, adds the label
when the turn starts and removes it when the turn ends. Three constraints shaped
it, and all generalise to anything that writes labels:

- **Plane has no per-issue label sub-resource.** Every label write is a full
  replacement of the array, so a writer must re-read the issue first and change
  one label. Trusting the webhook payload instead is how you silently delete the
  agent's own `lifecycle:triaged`.
- **The chip is stateless.** The gateway echoes the command's `data.context`
  (board, ticket, workspace, reason) onto every invocation event, so there is no
  `correlationid -> ticket` store to lose on a restart.
- **A claim outranks the lease.** `agent:working` is also pilot's claim marker
  (`px claim` adds it). At turn end the chip leaves it on if, since it went on, the
  ticket moved into *In Progress* or gained an assignee. Parking in Needs
  Attention or Awaiting Decision is not a claim, so that chip comes off.

Agents never write it: both lane prompts say the pipeline owns it, and the Plane
MCP refuses `agent:working` writes (`PLANE_RESERVED_LABELS`). An hourly *Stale
Chip Sweep* removes a chip whose last turn ended at least 10 minutes ago, unless
the ticket was edited since.

## Known gaps

- **`.project.json` declares only the `xp:` axis, in one repo.** The other three
  axes are baked into the scaffolder instead of declared.
- **`groomingPrompt` still says "using the label names the board already uses"**
  — which, on a board with no labels, tells the agent to invent. It should read
  the declared axes.
- **An archived board reads as empty.** The API returns 0 states and 0 issues
  with no error (and a label create 409s as a duplicate). CANDYS looked
  "soft-deleted" this way until 2026-09-23; it was only archived, and is now
  candystore's live board (82e56896, nine lanes). Check `archived_at`, or count
  in the Plane DB, before calling a board empty. CANDY is genuinely deleted.
- **Thirteen undeclared colon labels are still live**, reported by the
  scaffolder's lint and left alone because deleting one strips it from its
  tickets. JIMB carries `phase:0/1/2`, `scope:proposed|gated|exploratory|
  completed`, `sprint:shadow-foundation`, `violation:quiet|amber-attention`;
  DECK carries `blocked-by:M0`, `needs:hardware`, `risk:unverified`; INFR
  carries `project:DeLoContainers`, `stack:media`. `phase:`, `scope:` and
  `blocked-by:` are Rule 1 violations — position wearing a label — and want
  migrating into the state machine. `needs:` and `risk:` are declared open axes
  and are fine. The rest are undeclared axes someone should either declare or
  demote to bare words.
