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
for a non-default board. `workitem.search` likewise rejects `project_id`;
do not drop the binding to retry a workspace-wide search. `workitem.retrieve`
with a human-readable key (`AAI-62`) also 404s on a non-default workspace even
when `project_id` is supplied; resolve the UUID first. Instead,
`workitem.list(project_id=..., per_page=100, order_by="-created_at", expand="labels,state")`
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
state after each mutation. Plane may trim the final newline or other outer
whitespace from `description_html`; compare normalized outer whitespace, not
byte-for-byte formatting. If verification fails after a write, inspect the
bound read and activity before retrying. A failed local assertion does not mean
the provider rejected the mutation.

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
(observed on PJAN and JIMB). A hub page-list call can instead fail during wrapper
serialization with `'dict' object has no attribute 'model_dump'` (JIMB,
2026-10-07); that is not evidence that no pages or conventions exist. If the
compatible official MCP route is available, make one project-bound `page` list
read to distinguish the wrapper failure from the provider response; do not repair
the shared wrapper during grooming. Do not infer that the board has no conventions
from a provider 404 or retry against an unbound workspace. For grooming, record
the page-read limitation and use project detail, live state/label/cycle/module
definitions, nearby tickets, and the bound repository's guidance as the available evidence.
`project.get_features` may likewise return 404 (observed on DELO); use the bound
`project.retrieve` fields `cycle_view`, `module_view`, and `page_view` together
with the corresponding project-scoped lists. Do not enable features or invent
cycle/module definitions merely to complete one-ticket grooming.

If native Plane tools are absent, use the live Pipeline MCP Hub at
`https://mcp.delo.sh/mcp` through the installed Python MCP client. Authenticate
with the existing `PLANE_API_KEY` in the Bearer header (never print it), set
`x-workspace-slug` explicitly, initialize the session, and load
`list_domain_tools(domain="plane")` in that same session before dispatching
`call_domain_tool`. Inspect the installed MCP HTTP transport signature before
connecting: current `mcp.client.streamable_http.streamable_http_client` may
accept `http_client=` rather than `headers=`. In that version, create an
`httpx.AsyncClient(headers={"Authorization": "Bearer " + key,
"x-workspace-slug": workspace}, timeout=90)` and pass it as `http_client`;
keep it open around the MCP session. Do not downgrade shared dependencies.
Inspect the live wrapper and domain schemas; current hub
routing uses `call_domain_tool(domain="plane", tool="retrieve_work_item",
arguments={...})` (`tool`, not `tool_name`). Current hub names include
`retrieve_work_item`, `update_work_item`, `manage_work_item_label`, and
`list_work_item_comments`, with `work_item_id` rather than the older wrapper's
`workitem_id`. Pass the bound `project_id` on every Plane domain call.
Unexpanded `retrieve_work_item` on DELO can fail Pydantic
`WorkItemDetail.labels.0` validation because the provider returns UUID strings
while the SDK expects Label objects. Read with
`expand="labels,state,assignees"`; this is a response-shape issue, not an auth
failure. Expand all three even when only labels or state is needed: the hub also
models `WorkItemDetail.assignees` as UserLite objects, so UUID assignee strings
can fail validation if that relation remains unexpanded (JIMB, 2026-10-07).
A write may land before response-model validation fails, so inspect
the expanded bound read and activity before retrying any mutation. Check MCP
`isError` before decoding text as JSON.

If the hub's `manage_work_item_label` fails on its internal unexpanded read,
passing `expand` to that action does not help: the current handler does not
forward it. Do not infer malformed live data or a pipeline-label problem from
that model error alone. To resolve a label name to its UUID before calling
`manage_label`, use the local server's `label(action="list", project_id=...)`
tool — the project-scoped REST route `issue-labels/` 404s on this self-hosted
edition (MILK-6, 2026-10-22), so the v1 REST surface is not a working resolver.
A separately installed official Plane MCP/SDK may have
a compatible response model (DELO observed hub failure while local
`plane-sdk==0.2.20`, `WorkItemDetail.labels: list[str] | list[Label]`, succeeded).
Read back the bound ticket and activity first to determine whether a write
landed. If not, verify the installed client's unexpanded bound read and use
that unmodified server's official `workitem(action="manage_label",
project_id=..., workitem_id=..., add_label_id=...)` action via
`fastmcp.Client(get_stdio_mcp())`, with the existing environment key, explicit
workspace and correct Plane base URL. Prefer the plain `mcp` package over
`fastmcp.Client`: `fastmcp` is not importable in the Hermes runtime venv
(JIMB-403, 2026-10-09) while `mcp` ships with it. Spawn the checkout's own
interpreter (`/home/delorenj/code/plane-mcp-server/.venv/bin/python -m
plane_mcp`; the `uv tool` install points at the same source but carries an
older SDK and dies on import) and drive it with `ClientSession` over
`mcp.client.stdio.stdio_client(StdioServerParameters(command=..., args=["-m",
"plane_mcp"], env={PLANE_API_KEY, PLANE_WORKSPACE_SLUG, PLANE_BASE_URL, PATH,
HOME}))`. Call shape: tool `workitem`, `action="manage_label"`, `project_id`,
`workitem_id`, `add_label_id`/`remove_label_id` — one label per call; the
server re-reads the ticket first (no full-list replacement) and refuses
pipeline-owned labels itself. The server prints its FastMCP banner and
per-request log lines to stderr; redirect `2>/dev/null` when parsing stdout. Confirmed end-to-end on JIMB-403: the hub error
fired *before* the write (label absent on read-back) and the local route
landed it. Error signatures and a ready-to-run client:
`references/plane-mcp-fallback.md`, `scripts/plane_stdio_label.py`. Run the
script with the plane-mcp-server venv python, not system python — it imports
`mcp` and the runtime python's `mcp` has broken transitive deps — and prefix
the run with `env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV`: a Hermes session
exports PYTHONPATH into its own runtime venv and that value leaks into the
child venv, breaking `pydantic_core` imports there even under the right
interpreter (MILK-2, 2026-10-22). The stdio server reads `PLANE_API_KEY`
(and `PLANE_WORKSPACE_SLUG`) from its own environment — unlike `px`, which
resolves an `op://` reference at use time, the spawned server sees only what
you export. A Hermes agent shell does not export these, so materialize them
before the run and never print the key: source the workspace's plane env file
(`~/DevCloud/plane.<slug>.env` on this host), then
`export PLANE_PROJECT_ID=<board uuid>` bound to the board. If the key is still
unset, run `px whoami --json` from the bound repo and resolve the credential
the same way `px` does rather than guessing at config paths. The script honors
`PLANE_PROJECT_ID` / `PLANE_WORKSPACE_SLUG` as overrides, and the fleet shell
can export both for ANOTHER board (observed 33GOD values pointing the
JIMB-defaulted script at the wrong project → HTTP 404, JIMB-407, 2026-10-09).
Prefix every run with the bound board's values
(`PLANE_PROJECT_ID=<board uuid> PLANE_WORKSPACE_SLUG=<slug>`) rather than
trusting the script's default. Verify all preserved fields and the
label activity afterward. On that local server's `workitem retrieve`, `description_text` can come back
empty even when a `description_html` update landed (JIMB-404, 2026-10-09); verify a description write
with a plain project-scoped REST GET of the work item's `description_html`, never by replaying the
update or trusting `description_text`. Never monkeypatch the tool, directly PATCH the full
label list, clear `agent:working`, or repair unrelated source during grooming.
If no compatible tool route works, report the marker as incomplete.
Inspect that route's own live schema for every action; do not transfer argument
shapes from the hub to the local server. For example, the hub's
`manage_module_work_items(add_ids=[<uuid>])` takes an array, while local
`module(action="manage_workitems", add_ids="<uuid>")` takes a string. An array
on the latter is refused before the handler runs (JIMB, 2026-10-07); correct
the call against the loaded schema or use the hub's declared action, then verify
membership with the bound module list. Do not repair unrelated server code.
Local module/cycle `manage_workitems` can return `None` on success, represented
by empty MCP content and no structured result. Check `isError` first; empty
successful content is not a JSON parse error or proof the write failed. Verify
bound membership before retrying the mutation (JIMB, 2026-10-07).

`workitem(action="update")` on the local plane-mcp-server accepts
`description_html`, `start_date`, `priority`, and `parent` in one call.
Verify a description write by reading `description_html` back (length and
structure); `description_text` can come back empty even when the write
landed.
Creating a comment can bump the ticket's `updated_at` without changing its
fields. Verify protected fields, comments and activity; a timestamp-only change
is not evidence of a concurrent scope edit. Do not replay the comment.
The official server's list-tool annotation may describe a bare list while the
actual comments or activity response is a paginated object with `results`
(observed on JIMB, 2026-10-07). Inspect the returned shape before asserting
verification failed. If writes succeeded and only the verifier's list-shape
assumption failed, resume with read-only verification; never replay the mutation
batch or add a second rationale comment. Confirm pagination as well as content.

An editable `uv tool` installation may point at newer `plane_mcp` source while
its environment still carries an older SDK. An import failure such as
`cannot import name 'CustomerWorkItem'` is a dependency mismatch, not a Plane
permission failure. Inspect the source checkout's declared dependencies and
use its already-installed matching `.venv/bin/python` when available (observed
`plane-sdk==0.2.20` there on JIMB, 2026-10-07); verify imports and discover the
tool schemas before calling it. Do not upgrade shared fleet dependencies or
patch tool source under one-ticket grooming authorization.

Bound read batches may hit the provider's HTTP 429 limit when other grooming
turns share the key. Limit the fallback client's read concurrency, respect
`Retry-After` when supplied, and retry only failed reads after backoff or switch
to the compatible official tool. Do not replay a mixed mutation batch: verify
which writes landed first. A hub-session failure does not prove the credential
is invalid when a project-scoped provider GET still succeeds.

Project-scoped PQL and count routes are not supported on every self-hosted
Plane edition (JIMB observed PQL rejection and count HTTP 404). Use a bounded
`workitem.list(project_id=..., per_page=100)` with pagination and filter the
returned items client-side; check module/cycle membership with their bound
`list_workitems` actions. The tool may return a JSON `error` object or an
`Error:` string while MCP `isError` is false; treat either as a failed read,
never as an empty successful result.

A board audit reports findings first. Apply only requested or already-authorized
changes. Keep batching bounded to the named project and task.

## Completion and deployment

Close implementation work only against its acceptance evidence. A main-branch
merge is not proof of deployment: a deployed/live claim requires verification
of the running artifact and user-visible behavior. Use existing board states.
Generate changelogs or audience reports through `activity-report` when requested.
Send notifications only when the task authorizes the channel and recipients.

Plane can strip a description's trailing newline on save (JIMB observed).
It can also wrap a multi-root HTML fragment in one `<div>...</div>` on the bound
read (AAI-47, 2026-10-07) while the description activity retains the submitted
fragment, and decode entities such as `&rarr;` to `→` (AAI-48). After a comparison
failure, inspect the bound read/activity once. If only boundary whitespace, that
exact outer wrapper, equivalent entity encoding, or Plane-added
`rel="noopener noreferrer"` on otherwise unchanged links differs, normalize
those specific differences for verification. Plane added that link security
attribute on JIMB-388 (2026-10-08), while the description activity retained the
submitted HTML. Do not strip arbitrary attributes or inner markup, rewrite the
description, or replay the mutation batch merely to satisfy byte equality.
Compare requested and returned HTML after stripping boundary whitespace before
calling that a concurrent edit. If only the verifier fails, inspect the bound
activity/comments once, retain the confirmed write, and resume with the remaining
mutations; do not rewrite the description or replay a mixed mutation batch.

## Event boundary

Plane writes are normalized through the signed n8n ingress at
`https://n8n.delo.sh/webhook/plane`, the only producer of `repo.task.*` /
`repo.board.*` facts. Never emit one yourself, before or after CRUD. Explicit PM judgments remain separate decisions. Use
`bloodbank-integration` and its event-journey reference for transport diagnosis.
Do not claim automatic hooks exist without checking the installed configuration.
