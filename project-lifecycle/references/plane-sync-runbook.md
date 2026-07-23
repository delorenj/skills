# Plane Sync Runbook

BMAD story: `PLC-E6-S2: Create Plane sync runbook` (Plane `CAF-137`).

## Purpose

Use this runbook when lifecycle tickets need to be recreated, audited, status
synced, or checked for drift. BMAD owns requirements. Plane mirrors execution
state for team visibility.

## Required Local Files

- `_bmad_output/planning-artifacts/project-lifecycle-workflow-stack-epics.md`
  is the BMAD source for lifecycle stories.
- `_bmad_output/planning-artifacts/lifecycle-status-ledger.json` is the
  execution status ledger.
- `.plane.json` identifies the Plane workspace/project.
- `.env` provides Plane credentials and base URL.

`.plane.json` must include:

```json
{
  "workspace": "automaticai",
  "project_id": "bf80b541-4aed-4942-bc49-f3c25253397f"
}
```

`.env` may include:

```text
PLANE_BASE=https://plane.delo.sh
PLANE_API_KEY=...
```

`PLANE_AUTOMATIAI_API_KEY` is also accepted by the lifecycle scripts for
backward compatibility.

## Secret Handling

Never print Plane API keys, `.env` contents, or request headers in logs,
reports, Plane comments, PR bodies, or chat handoffs. If a command fails,
report the failed command, response class, and remediation path without
including the secret value.

## Standard Sync Flow

Run these from the repository root.

### 1. Inspect Current State

```bash
git status --short --branch
python3 skills/project-lifecycle/scripts/lifecycle_snapshot.py
```

Confirm the branch is expected and local unrelated files are not staged.

### 2. Dry-Run BMAD-To-Plane Mirror

```bash
python3 skills/project-lifecycle/scripts/sync_plane_from_bmad.py
```

Expected healthy result:

```text
stories=26 existing=26 created=0 would_create=0
```

This writes:

```text
_bmad_output/planning-artifacts/project-lifecycle-plane-mirror-report.md
```

The dry run is safe and should be run before any create/update action.

### 3. Create Missing Plane Issues

Only run create mode after confirming the dry-run would not duplicate existing
issues.

```bash
python3 skills/project-lifecycle/scripts/sync_plane_from_bmad.py --create
```

If issues are created, commit the updated mirror report or story parity
artifact that records the Plane issue IDs. Do not copy long requirements into
Plane; keep BMAD as the requirement source and put links/summaries in Plane.

### 4. Check Requirement And Status Drift

```bash
python3 skills/project-lifecycle/scripts/detect_plane_drift.py --ignore-plane-only-status
```

Healthy output:

```text
Requirement drift findings: 0
Status drift findings: 0
RESULT: NO DRIFT
```

Use `--format json` when another tool needs machine-readable output. Use
`--issues-json <file>` for offline rehearsals.

### 5. Validate Status Ledger

```bash
python3 skills/project-lifecycle/scripts/reconcile_status.py
```

Default mode is a dry run. It validates:

- allowed status names;
- blocked entries include reason, owner, and date;
- done entries include `ac_verified.verified=true` and evidence;
- duplicate `story_id` or `caf_id` values are rejected.

### 6. Apply Status Updates To Plane

Only apply after the dry run is correct.

```bash
python3 skills/project-lifecycle/scripts/reconcile_status.py --apply
```

Apply mode patches Plane states and posts tagged comments for blockers and PR
links. It is intended to be idempotent: identical tagged comments should not be
posted repeatedly.

### 7. Regenerate Next-Ticket Triage

```bash
python3 skills/project-lifecycle/scripts/triage_next_ticket.py --write-report
```

This writes:

```text
_bmad_output/planning-artifacts/lifecycle-next-ticket-triage-report.md
```

Use that report to choose the next unblocked ticket. Do not skip dependency
gates just because Plane appears to show a later ticket as available.

## Failed Plane Writes

If `sync_plane_from_bmad.py --create` or `reconcile_status.py --apply` fails:

1. Stop write actions immediately.
2. Record the failed command, timestamp, affected CAF/story IDs, and sanitized
   error message.
3. Re-run the corresponding dry-run command.
4. Run `detect_plane_drift.py --ignore-plane-only-status`.
5. If Plane partially changed, update the lifecycle status ledger or mirror
   report to match the proven state before applying again.
6. If the failure is auth, DNS, TLS, or API availability, record the blocker in
   the relevant lifecycle story and move to the next safe unblocked ticket.

Never retry a write loop blindly. Verify what changed first.

## Operator Handoff Checklist

- BMAD source artifact path included.
- Plane issue IDs or CAF IDs included.
- Dry-run output summarized.
- Apply output summarized when a write occurred.
- Drift result included.
- No secrets printed.
- Next-ticket triage result included.
