# Field survey — 25 fleet-bound Plane boards, 2026-09-04

Every number here was measured against the live instance
(`https://plane.delo.sh`), not read from a doc. Reproduce with
`bloodbank/bin/bb-ack-labels` (labels) and `bb-board-scaffold` (states, dry run).

## Labels

**75 distinct names across 25 boards. 72 of them exist on exactly one board.**

| reach | label | note |
|---|---|---|
| 23/25 | `agent:working` | provisioned deliberately, same day |
| 4/25 | `bug` | three different colours: `#ef4444`, `#f78da7`, `#ff6900` |
| 3/25 | `spike` | three different colours: `#00d084`, `#8ed1fc`, `#a855f7` |
| 1/25 | the other 72 | one board each |

`lifecycle:triaged`, `xp:internal` and `xp:external` are each on **JIMB only** —
not because other boards cannot hold them, but because JIMB is the only board
grooming has been exercised on.

Thirteen boards carry nothing but the ack chip: DELO, DNET, DOCS, DRUMJ, HERPM,
HOLOC, JACPM, KEEP, MKTJNG, SIDE, SSBNK, VOXXY, ZSHYZH.

A hypothesis worth recording as **disproved**: labels are *not* shadowing
modules or cycles. Checked every board's labels against its own module and cycle
names, normalised — zero collisions. The 75 are genuinely distinct facts, badly
housed.

## States

**6 distinct state machines across 25 boards.**

| boards | machine |
|---|---|
| 18 | Plane stock 5: Backlog, Todo, In Progress, Done, Cancelled |
| 2 — **33GOD, JIMB** | the 9-state 33GOD machine, **byte-identical to each other** |
| 2 — CANDY, CANDYS | zero states (soft-deleted, not empty) |
| 1 — DECK | stock 5 + In Review |
| 1 — HEYMA | stock 5 + Ready for QA |
| 1 — PJAN | 7 states |

The 33GOD machine, in sequence order:

| group | state | note |
|---|---|---|
| backlog | Backlog | |
| unstarted | Todo | default |
| started | In Progress | |
| completed | Done | described |
| cancelled | Cancelled | |
| started | Awaiting Decision | blocked on a decision, permission, or feedback |
| unstarted | Needs Re-evaluation | strategic checkpoint; treat the premise as a proposal |
| started | E2E Testing & QA | agent declares implementation ready |
| started | Ready for Documentation | complete, pending skill/doc updates |

Descriptions are the part that drifted even between the two good boards: 33GOD
describes 5 of 9, JIMB describes 4.

## Platform capabilities

Probed directly; all results are from live calls.

| capability | result |
|---|---|
| `/templates/` | 404 |
| `/project-templates/` | 404 |
| `/workitem-templates/` | 404 |
| `/issue-types/` | 404 — classification must be labels |
| state create / delete | **works**, description round-trips |
| per-issue label sub-resource | 404 — label writes are full-array replacement |
| `?labels=` / `?labels__in=` filters | **silently ignored**, returns the whole board |
| label list | **paginates** — an unpaged existence check reports false negatives |
| rate limit | 429 `error_code 5900` after ~34 quick requests |

## Why the drift happened

Plane's API accepts label **UUIDs** only, so nothing appears by writing a name.
But the agent holds a `label` MCP tool with a `create` action
(`plane-mcp-server/plane_mcp/tools/label.py`), and `groomingPrompt` instructs it
to add `lifecycle:triaged` last. On a board without the label the agent creates
it, then attaches it.

So the taxonomy is authored at runtime, per board, by whichever agent needs a
name first, against no shared definition. Nothing enforces agreement and nothing
reports disagreement. Three colours of `bug` is the predictable result, not an
anomaly.
