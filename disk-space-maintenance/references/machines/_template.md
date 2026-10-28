# <machine> — disk profile

**Last verified:** never (template) — if a run contradicts this file, the run wins: fix the file.

## Identity

OS and version, hardware, disk layout (volumes, LVM/LUKS, APFS container),
role (what runs here), who uses it, how to reach it (ssh alias from
big-chungus), whether passwordless sudo works.

## Baseline

Used/free today, what healthy looks like, what counts as tight and as an
emergency for this disk size.

## Never touch

Concrete paths: personal data, other users' homes, live service state, the
newest backup copies, unpushed repos.

## Space map

| Path | Size | Class | Notes |
|---|---|---|---|

Class: A = rebuildable, delete without asking · B = owner decision · C = never.
List what could not be measured and why.

## Known accumulators

| What regrows | Where | Observed size | Growth driver | Bound today | Recommended bound |
|---|---|---|---|---|---|

## Targeted playbook

Tier A, biggest first, each with expected yield and precondition. Then tier B
items phrased as decisions, with any answers the owner has already given.

## Installed automation

Timers, launchd agents, cron, app retention settings. Gaps.

## Gotchas

## Run log
