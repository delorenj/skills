---
name: project-lifecycle
description: Run BMAD-first project lifecycle workflows for Coaching Agent Framework. Use when Codex needs to inspect or initialize BMAD, keep BMAD planning artifacts as the source of truth, mirror BMAD epics/stories into Plane tickets, choose or continue the next ticket autonomously, handle blocked work without idling, update ticket/story status, or coordinate the path from Damian's intent through workflow artifacts, Hermes routing, MCP tools, and database state.
---

# Project Lifecycle

Use this skill to keep CAF delivery on rails: BMAD owns product truth, Plane mirrors execution, and Codex keeps work moving with minimal operator burden.

## Core Contract

- Treat root `_bmad/` and `_bmad_output/` as the cross-stack planning surface.
- Treat `lamp-skills/_bmad/` and `lamp-skills/_bmad-output/` as component history unless a file there is explicitly promoted.
- Make BMAD the source of truth for epics, stories, acceptance criteria, architecture notes, and handoff artifacts.
- Make Plane the coordination mirror for status, assignment, comments, and dev-team visibility.
- Prefer one Plane issue per BMAD story. Put the BMAD artifact path or anchor in the Plane issue.
- Avoid duplicating long requirements in Plane. Summarize there and link back to BMAD.
- When parity is expensive, preserve BMAD accuracy first and degrade Plane to status plus links.

## Startup

1. Run a read-only BMAD health check before planning or ticket work:
   - `npx bmad-method@latest status`
   - inspect `_bmad/_config/manifest.yaml`
   - inspect `_bmad/config.toml`
   - inspect `git status --short`
2. Confirm root BMAD has the expected modules: `core`, `bmm`, `bmb`, `cis`, and `bmp` when autopilot is part of the workflow.
3. Use stable BMAD modules for team handoff unless the user explicitly asks for `next`.
4. If BMAD is missing or stale, update BMAD before creating new planning artifacts.
5. If the repo has both root and component BMAD artifacts, promote or summarize old component content into root artifacts rather than maintaining two product truths.

## Workflows

- For the detailed operating model, read `references/lifecycle-operating-model.md`.
- For BMAD/Plane mirror rules, read `references/bmad-plane-parity.md`.
- For the CAF workflow-artifact architecture path, read `references/workflow-artifact-stack.md`.
- For blocked-work and autonomous next-ticket behavior, read `references/autonomy-and-blockers.md`.
- For dev-team-ready story authoring, use `references/handoff-story-template.md`.
- For status flow from the lifecycle status ledger into Plane, read `references/status-reconciliation.md`.
- For dependency-aware next-ticket selection, read `references/next-ticket-triage.md`.
- For operator-safe Plane sync and failed-write handling, read `references/plane-sync-runbook.md`.
- For capturing Damian's coaching intent before workflow generation, read `references/intent-capture-format.md`.
- For the runtime workflow artifact schema, read `references/workflow-artifact-schema.md`.

## Plane Mirror Helper

- Use `python3 skills/project-lifecycle/scripts/sync_plane_from_bmad.py` to mirror `PLC-*` BMAD stories into Plane.
- Run it without `--create` first. The dry run writes `_bmad_output/planning-artifacts/project-lifecycle-plane-mirror-report.md`.
- Run it with `--create` only after confirming the dry run will not duplicate existing Plane issues.
- Treat the generated report as parity evidence, not as the source of product truth.
- Use `python3 skills/project-lifecycle/scripts/notify_blockers.py` to dry-run or post tagged Plane alerts for blockers that have aged past the configured threshold.

## Default Behaviors

- If asked "what ticket next?" inspect BMAD, Plane, git state, open PRs, and recent work, then choose the highest-leverage unblocked ticket.
- If asked to continue, continue the active BMAD/Plane-linked work item unless newer user instructions clearly supersede it.
- If a ticket blocks on external access, user login, review, or credentials, record the blocker in Plane/BMAD and move to the next safe unblocked item.
- If the same blocking condition repeats, propose or create a durable notification/handoff mechanism before waiting again.
- If code changes are made, keep the BMAD story and Plane issue status aligned before final handoff.
- If creating a handoff for a dev team, include BMAD artifact paths, Plane issue IDs, acceptance criteria, dependencies, and validation commands.
- If creating or promoting a BMAD story for handoff, use `references/handoff-story-template.md` so status, blocker handling, Plane links, source intent, dependencies, implementation notes, and validation are captured consistently.

## Guardrails

- Do not let Plane become a second requirements database.
- Do not create tickets without checking for an existing BMAD story or deciding where the story should live.
- Do not advance a BMAD story to done because code exists; require acceptance criteria and verification.
- Do not block indefinitely if another useful, lower-risk ticket is available.
- Do not mutate generated BMAD installer files by hand unless the task is explicitly to repair the install.
