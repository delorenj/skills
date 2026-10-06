---
name: project-lifecycle
description: Read and update Plane tickets, comments, and board state for a requested project. Use for ticket CRUD, scoped board audits, and evidence-backed status updates. Route board execution to momo and new-project provisioning to 33god-projects.
---
# Plane ticket operations

Resolve the repository and board from `.project.json` before writing. Use the
Plane MCP or `https://plane.delo.sh/api/v1/workspaces/{workspace}/projects/{project}/`.
Credentials come from the process environment or the approved vault resolver;
never print them. Confirm the target when project identity is ambiguous.

For a non-default Plane workspace, pass the bound board UUID as `project_id`
on every tool call. `workitem.retrieve_by_identifier` does not accept
`project_id` and resolves through the server's default workspace; do not use it
for a non-default board. `workitem.search` likewise rejects `project_id`; do
not drop the binding to retry a workspace-wide search. Instead,
`workitem.list(project_id=..., per_page=100)`
(page if needed), match the ticket's `sequence_id`, then
`workitem.retrieve(project_id=..., workitem_id=<uuid>)`. Use a sparse fieldset
for board surveys when full descriptions would swamp the result. A rejected
`project_id` argument is not permission to retry against the default workspace.

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

For grooming, make `lifecycle:triaged` the final ticket mutation, then read back.
If a previously retrieved item starts returning 404 or disappears from the bound
board list, inspect its bound activity and comments once before any write. A
`deleted` activity is a stop condition: do not comment, classify, recreate, or
restore it under grooming-only authorization; report that grooming is incomplete
and leave `lifecycle:triaged` unadded. Do not retry against the default workspace.
If another writer changes state or labels during the pass, inspect the bound
work item's activity and comments once; do not revert that writer's changes or
reclaim the pipeline lease. Report your own writes separately from the latest
board state. Attribute pre-existing “landed” claims and timestamp read-only git
observations rather than turning them into unverified completion evidence.

An archived board reads as 0 issues and 0 states through the API with no error.
Check `archived_at` (or count in the Plane DB) before calling a board empty.

If a named ticket is omitted by the bound list, do not recreate it or fall back
to an unbound workspace. The archived-workitem endpoint may itself return 404
on a live board. Use an authorized, project-scoped read-only provider lookup to
resolve its UUID and check `deleted_at` / `archived_at`, then retrieve that UUID
through the bound API. A deleted ticket ends grooming: no replacement, restore,
comment, or completion latch without new authorization. Avoid chaining failing
404 calls: the MCP wrapper may open its circuit after three failures and call
the server “unreachable” even when the underlying resource is merely absent.
Use a read-only alternative for activity/comments rather than polling that
circuit or treating its error as proof of a Plane outage.

Project page routes may return HTTP 404 even on a live board with pages enabled
(observed on PJAN). Do not infer that the board has no conventions from that
failure or retry against an unbound workspace. For grooming, record the page-read
limitation and use project detail, live state/label/cycle/module definitions,
nearby tickets, and the bound repository's guidance as the available evidence.
`project.get_features` may likewise return 404 (observed on DELO); use the bound
`project.retrieve` fields `cycle_view`, `module_view`, and `page_view` together
with the corresponding project-scoped lists. Do not enable features or invent
cycle/module definitions merely to complete one-ticket grooming.

If native Plane tools are absent, use the live Pipeline MCP Hub at
`https://mcp.delo.sh/mcp` through the installed Python MCP client. Authenticate
with the existing `PLANE_API_KEY` in the Bearer header (never print it), set
`x-workspace-slug` explicitly, initialize the session, and load
`list_domain_tools(domain="plane")` in that same session before dispatching
`call_domain_tool`. Inspect live schemas: current hub names include
`retrieve_work_item`, `update_work_item`, `manage_work_item_label`, and
`list_work_item_comments`, with `work_item_id` rather than the older wrapper's
`workitem_id`. Pass the bound `project_id` on every Plane domain call.
Unexpanded `retrieve_work_item` on DELO can fail Pydantic
`WorkItemDetail.labels.0` validation because the provider returns UUID strings
while the SDK expects Label objects. Read with
`expand="labels,state,assignees"`; this is a response-shape issue, not an auth
failure. A write may land before response-model validation fails, so inspect
the expanded bound read and activity before retrying any mutation. Check MCP
`isError` before decoding text as JSON.

If the hub's `manage_work_item_label` fails on its internal unexpanded read,
passing `expand` to that action does not help: the current handler does not
forward it. Do not infer malformed live data or a pipeline-label problem from
that model error alone. A separately installed official Plane MCP/SDK may have
a compatible response model (DELO observed hub failure while local
`plane-sdk==0.2.20`, `WorkItemDetail.labels: list[str] | list[Label]`, succeeded).
Read back the bound ticket and activity first to determine whether a write
landed. If not, verify the installed client's unexpanded bound read and use
that unmodified server's official `workitem(action="manage_label",
project_id=..., workitem_id=..., add_label_id=...)` action via
`fastmcp.Client(get_stdio_mcp())`, with the existing environment key, explicit
workspace and correct Plane base URL. Verify all preserved fields and the
label activity afterward. Never monkeypatch the tool, directly PATCH the full
label list, clear `agent:working`, or repair unrelated source during grooming.
If no compatible tool route works, report the marker as incomplete.

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
