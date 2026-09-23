---
name: project-lifecycle
description: Read and update Plane tickets, comments, and board state for a requested project. Use for ticket CRUD, scoped board audits, and evidence-backed status updates. Route board execution to momo and new-project provisioning to 33god-projects.
---
# Plane ticket operations

Resolve the repository and board from `.project.json` before writing. Use the
Plane MCP or `https://plane.delo.sh/api/v1/workspaces/{workspace}/projects/{project}/`.
Credentials come from the process environment or the approved vault resolver;
never print them. Confirm the target when project identity is ambiguous.

- Use `board-taxonomy` for states, labels, and exclusive axes. Reuse declared
  values; do not invent effort, sprint, priority, or pipeline-position labels.
- Creating a ticket does not imply creating its board. Route missing-board
  setup to `33god-projects`, preserving the current task's authorization.
- Artwork, mascots, and art-theme documents are optional requested deliverables.
- A request to select a next ticket returns a recommendation. Starting work or
  assigning it requires execution scope; route board orchestration to `momo`.

## Ticket writes

Read existing issues to avoid duplicates. Write the requested outcome, acceptance
criteria, relevant dependencies, and actual priority. Preserve unrelated fields.
Prefer `px` (see `pilot`): `px task create`, `px move <ref> <state>` on legacy
boards (refs like `33GOD-68` work), `px claim` / `px close`. A Plane `PATCH` with
`labels` replaces the whole list and there is no per-label endpoint, so re-read
and change one label at a time (px 0.2.2 and the Plane MCP `manage_label` do);
never touch the pipeline-owned `agent:working`. Verify the provider's returned
state after each mutation.

An archived board reads as 0 issues and 0 states through the API with no error.
Check `archived_at` (or count in the Plane DB) before calling a board empty.

A board audit reports findings first. Apply only requested or already-authorized
changes. Keep batching bounded to the named project and task.

## Completion and deployment

Close implementation work only against its acceptance evidence. A main-branch
merge is not proof of deployment: a deployed/live claim requires verification
of the running artifact and user-visible behavior. Use existing board states.
Generate changelogs or audience reports through `activity-report` when requested.
Send notifications only when the task authorizes the channel and recipients.

## Event boundary

Plane writes are normalized through the signed n8n ingress at
`https://n8n.delo.sh/webhook/plane`, the only producer of `repo.task.*` /
`repo.board.*` facts. Never emit one yourself, before or after CRUD. Explicit PM judgments remain separate decisions. Use
`bloodbank-integration` and its event-journey reference for transport diagnosis.
Do not claim automatic hooks exist without checking the installed configuration.
