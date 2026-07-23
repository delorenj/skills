# BMAD And Plane Parity

## Source Of Truth

BMAD is the source of truth for:

- product requirements;
- architecture decisions;
- epics and stories;
- acceptance criteria;
- implementation readiness;
- dev-team handoff detail.

Plane is the execution mirror for:

- assignment;
- ticket status;
- comments and coordination;
- links to PRs;
- lightweight visibility for non-BMAD readers.

## Mapping Rules

- One BMAD epic maps to one Plane epic or milestone when practical.
- One BMAD story maps to one Plane issue.
- The Plane issue title should include the BMAD story ID or stable slug.
- The BMAD story frontmatter or body should include the Plane issue ID once created.
- Plane descriptions should summarize the work and link to the BMAD artifact.
- BMAD artifacts should carry full acceptance criteria.

## Drift Rules

When BMAD and Plane disagree:

1. Prefer BMAD for requirements and acceptance criteria.
2. Prefer Plane for current assignee, comments, and operational status if it is newer.
3. Update the stale side once the discrepancy is understood.
4. If the discrepancy changes scope or user experience, ask the human before merging the interpretation.

## Plane Issue Template

Use this shape when creating or updating Plane issues:

```markdown
BMAD source: <path or URL>

Summary:
<short execution summary>

Acceptance criteria:
- See BMAD story for authoritative AC.
- AC highlights:
  - <short AC 1>
  - <short AC 2>

Dependencies:
- <dependency or none>

Validation:
- <command or manual check>
```

## Mirror Script

For `PLC-*` lifecycle stories, use:

```bash
python3 skills/project-lifecycle/scripts/sync_plane_from_bmad.py
python3 skills/project-lifecycle/scripts/sync_plane_from_bmad.py --create
```

Run the first command as a dry run. It writes `_bmad_output/planning-artifacts/project-lifecycle-plane-mirror-report.md` and should show `would_create` counts before any Plane writes. Run with `--create` only after confirming the dry run will not duplicate existing Plane issues.

## Drift Detection

To detect parity drift between the BMAD lifecycle artifact and the Plane board:

```bash
# Live mode (read-only GETs; key from PLANE_API_KEY/PLANE_AUTOMATIAI_API_KEY env or .env)
python3 skills/project-lifecycle/scripts/detect_plane_drift.py

# Offline mode against saved issues JSON; machine-readable output
python3 skills/project-lifecycle/scripts/detect_plane_drift.py --issues-json issues.json --format json
```

The report separates the two drift classes and suggests the source to update:

- Requirement drift (BMAD is requirements truth): BMAD stories missing Plane issues, Plane lifecycle issues missing BMAD sources, title mismatches, duplicate mirrors. Fix Plane to match BMAD, except orphans, which need review (backfill BMAD or cancel the Plane issue).
- Status drift (Plane is status truth): a declared BMAD `Status:` line conflicting with the Plane state, or a story Plane shows as In Progress/Review/Done/Cancelled while BMAD carries no status marker (Plane-only signal; suppress with `--ignore-plane-only-status`). Fix BMAD to match Plane.

The lifecycle epics doc carries no per-story status markers today, so BMAD status is treated as unknown: Backlog/Todo issues are considered aligned, and only started/closed states surface as status drift.

Exit codes: `0` no drift, `1` drift found, `2` error. Verifier:

```bash
python3 skills/project-lifecycle/scripts/test_detect_plane_drift.py
```

## Status Alignment

- BMAD draft or unvalidated story: Plane Backlog or Todo.
- BMAD ready for implementation: Plane Todo or Ready.
- Work actively being coded: Plane In Progress.
- Code complete but not verified: Plane In Review or equivalent.
- Acceptance criteria verified: Plane Done.
- Blocked externally: Plane Blocked, with blocker note and next safe fallback.

## Anti-Patterns

- Copying the full BMAD spec into Plane.
- Creating Plane issues without a BMAD source for architectural work.
- Updating Plane status while leaving BMAD stale.
- Treating Plane comments as hidden requirements.
- Closing a Plane issue because a PR exists before AC verification.
