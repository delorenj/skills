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
4. **Colour encodes the axis, not the value.** Directly prevents the
   three-colours-of-`bug` failure.
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

It clones the reference board's state machine and the functional labels. It only
adds and aligns:

- never deletes a state, and never reorders one it did not create;
- never touches `default` or `is_triage` — a board must have exactly one default
  state, and moving it silently re-homes every new ticket;
- refuses a board reporting zero states, which is the signature of a
  soft-deleted project, not an empty one.

33GOD and JIMB hold byte-identical 9-state machines and either is a sound
reference.

## The ack chip, as a worked example

`agent:working` exists because a ticket sat visibly untouched for the entire
time its agent was booting — 377s, 633s and 2596s measured on three JIMB
tickets. No instruction in an agent's prompt can close that gap, because the gap
*is* the agent starting up. The acknowledgement has to come from the lane, at
dispatch.

Both ticket lanes stamp the chip the moment the Fleet node reports
`invoked: true`, and clear it when that agent's turn ends. Two constraints
shaped it, and both generalise to anything that writes labels:

- **Plane has no per-issue label sub-resource.** Every label write is a full
  replacement of the array, so a writer must re-read the issue first. Trusting
  the webhook payload instead is how you silently delete the agent's own
  `lifecycle:triaged`.
- **A `bloodbank.agent.invocation.*` event carries no board and no ticket** —
  only a correlation id, and that id is *inherited*, not the recomputable
  ticket uuid. So the dispatch side records `correlationid -> ticket` and the
  turn-end side spends it. Store and spend; never try to invert.

Measured: chip on in 339ms of node time, off 271s later, leaving the three
labels the agent had added itself untouched.

## Known gaps

- **The lease has no board-side sweeper.** The chip's expiry lives in n8n
  workflow static data, so if n8n restarts mid-turn a chip can strand with
  nothing to clear it. A `--sweep` on `bb-ack-labels` is the fix.
- **`.project.json` declares only the `xp:` axis, in one repo.** The other three
  axes are baked into the scaffolder instead of declared.
- **`groomingPrompt` still says "using the label names the board already uses"**
  — which, on a board with no labels, tells the agent to invent. It should read
  the declared axes.
- **CANDY and CANDYS accept nothing** — zero states, and a label create 409s as
  a duplicate while GET reports count 0. They are soft-deleted, not empty.
