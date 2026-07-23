# Status Reconciliation

How execution status flows from BMAD stories to Plane without corrupting BMAD truth.

BMAD story: `PLC-E2-S4: Add status reconciliation workflow` (Plane `CAF-120`).

## Design

The BMAD epics artifact (`_bmad_output/planning-artifacts/project-lifecycle-workflow-stack-epics.md`)
stays requirements-only. Execution state lives in a separate status ledger:

```
_bmad_output/planning-artifacts/lifecycle-status-ledger.json
```

The ledger is the single write surface for lifecycle story status. Plane mirrors
the ledger; the BMAD epics document is never edited for status changes.

```
BMAD epics doc (requirements, immutable by status flow)
        |
        v
lifecycle-status-ledger.json (execution state, orchestrator-maintained)
        |
        v  reconcile_status.py
Plane issues (mirrored state + blocker/PR comments)
```

## Ledger Schema

The ledger is a JSON array. Each entry:

| Field | Type | Rule |
| --- | --- | --- |
| `story_id` | string | `PLC-E<epic>-S<story>`, unique across the ledger |
| `caf_id` | string | `CAF-<n>`, unique across the ledger |
| `status` | string | one of `backlog`, `todo`, `in-progress`, `blocked`, `review`, `done` |
| `blocker` | object or null | required non-null when `status` is `blocked`; see below |
| `pr_links` | array of strings | PR URLs; allowed in any status, may be empty |
| `ac_verified` | object or null | required non-null when `status` is `done`; see below |
| `updated` | string | ISO date or datetime of the last ledger edit |
| `title` | string | optional, readability only; never authoritative (BMAD owns titles) |

`blocker` object (all fields required and non-empty when present):

| Field | Type | Rule |
| --- | --- | --- |
| `reason` | string | what is blocking the story |
| `owner` | string | who must act to unblock |
| `date` | string | ISO date (`YYYY-MM-DD`) the blocker was recorded |

`ac_verified` object:

| Field | Type | Rule |
| --- | --- | --- |
| `verified` | bool | must be `true` for `done` |
| `evidence` | string | non-empty pointer to proof (test command, report path, PR) |

## State Mapping Table

Plane CAF project states: `Backlog`, `Todo`, `In Progress`, `Review`, `Done`,
`Cancelled`. Plane has no native Blocked state.

| Ledger status | Plane state | Extra reconciler action |
| --- | --- | --- |
| `backlog` | Backlog | none |
| `todo` | Todo | none |
| `in-progress` | In Progress | none |
| `blocked` | In Progress | posts a blocker comment (reason, owner, date) |
| `review` | Review | none |
| `done` | Done | requires the done gate below before mapping |

`Cancelled` is operator-only in Plane and is intentionally not reachable from
the ledger; cancelling a story is a requirements decision that must go through
the BMAD artifact first.

## Blocked Entry Requirements

A `blocked` entry is invalid unless `blocker.reason`, `blocker.owner`, and
`blocker.date` are all present and non-empty. The reconciler rejects the ledger
(exit 1) otherwise. Because Plane lacks a Blocked state, blocked work is
represented as:

1. Plane state `In Progress`.
2. A Plane comment: `[blocked] <reason> | owner: <owner> | since: <date>`.
3. The ledger entry itself, which is the authoritative blocked record.

When the blocker clears, set `status` back to the real state (`in-progress`,
`review`, ...), set `blocker` to `null`, and update `updated`.

## Done Gate

`status` may move to `done` only when `ac_verified.verified` is `true` and
`ac_verified.evidence` is a non-empty string pointing at the verification
(verifier command output, test run, mirror report, merged PR). The reconciler
rejects (exit 1) any `done` entry without it. This enforces the project rule
that acceptance criteria verification, not code existence, completes a story.

## PR Link Attachment

PR links attach to Plane without changing BMAD requirements:

1. Append the PR URL to the entry's `pr_links` array in the ledger.
2. Run the reconciler with `--apply`; it posts a `[pr-links]` comment on the
   matching Plane issue listing the URLs. (Operators may additionally use the
   Plane issue Links panel by hand; the ledger remains the durable record.)
3. Never edit `project-lifecycle-workflow-stack-epics.md` to add PR links;
   the BMAD artifact carries requirements, not execution breadcrumbs.

PR links are valid in any status, so review evidence can accumulate before
the done gate is satisfied.

## Reconciler Usage

```bash
# Validate the ledger and print intended Plane changes (no network, default)
python3 skills/project-lifecycle/scripts/reconcile_status.py

# Use an alternate ledger (tests, rehearsals)
python3 skills/project-lifecycle/scripts/reconcile_status.py --ledger path/to/ledger.json

# Apply: PATCH Plane issue states and post blocker / PR-link comments
python3 skills/project-lifecycle/scripts/reconcile_status.py --apply
```

- Default mode is dry-run: validate, then print the intended state changes and
  comments. Nothing is written to Plane.
- `--apply` resolves Plane config the same way as `sync_plane_from_bmad.py`
  (`.env` for `PLANE_API_KEY`/`PLANE_AUTOMATIAI_API_KEY` and `PLANE_BASE`,
  `.plane.json` for workspace/project id) and never prints API keys.
- Apply is idempotent: state PATCHes are skipped when the issue already has
  the target state, and tagged comments (`[blocked]`, `[pr-links]`) are skipped
  when an identical tagged comment already exists.

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | ledger valid; dry-run printed or apply completed |
| 1 | validation errors (bad status, done without verification, blocked without blocker/owner/date, duplicates) |
| 2 | runtime errors (missing ledger, bad JSON, config or Plane API failure) |

Verifier:

```bash
python3 skills/project-lifecycle/scripts/test_reconcile_status.py
```
