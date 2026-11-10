# Plane label-delta fallback: hub → local stdio server

When to use: the Pipeline MCP Hub's `manage_work_item_label` (or any hub plane
tool that reads a work item back) fails Pydantic validation on JIMB, and you
need single-label add/remove without replacing the label list.

## Failure signatures (all seen on JIMB, 2026-10-09)

1. **Hub response-model failure — write does NOT land.**
   `manage_work_item_label` returns MCP `isError: true` with:
   `3 validation errors for WorkItemDetail — assignees.0 Input should be a
   valid dictionary or instance of UserLite ... labels.0 ... instance of
   Label`. The handler's internal unexpanded read returns UUID strings where
   the SDK expects objects, and validation fails **before** the mutation.
   Passing `expand` does not help (the handler does not forward it). Always
   read the ticket back before retrying — on JIMB-403 the label was absent,
   confirming nothing landed.

2. **Calling inner tool names directly on the hub — "Unknown tool".**
   The hub exposes exactly three top-level tools: `list_domains`,
   `list_domain_tools`, `call_domain_tool`. Route everything through
   `call_domain_tool(domain="plane", tool="<name>", arguments={...})`.

3. **`uv tool` plane-mcp-server will not start — dependency mismatch.**
   `ImportError: cannot import name 'CustomerWorkItem' from
   'plane.models.customers'`. The editable install points at
   `~/code/plane-mcp-server` source but its site-packages carry an older
   plane-sdk. Do not upgrade it; use the checkout's own venv instead.

## Working route

Run the **source checkout's own venv** as the server process:

    /home/delorenj/code/plane-mcp-server/.venv/bin/python -m plane_mcp

Client: plain `mcp` package (ships with the Hermes runtime venv; `fastmcp`
does NOT import there — `ModuleNotFoundError: No module named 'fastmcp'`).
Run `scripts/plane_stdio_label.py` with the **same venv python** as the
server (`/home/delorenj/code/plane-mcp-server/.venv/bin/python`), not system
python: the script imports `mcp` in its own process, and the Hermes runtime
python's `mcp` install has broken transitive deps (`anyio` missing).

Env the server needs: `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG` (the bound
workspace, e.g. `automaticai`), `PLANE_BASE_URL` (`https://plane.delo.sh`),
plus `PATH` and `HOME` (a stdio server without them cannot find anything).

**Source the workspace env file under `set -a`** — the file assigns without
`export`, so a plain `source` leaves the key a shell variable the child never
sees and the script dies with `PLANE_API_KEY not set`:

    set -a; source ~/DevCloud/plane.<slug>.env; set +a

Then `export PLANE_PROJECT_ID=<board uuid>` bound to the board. Prefix every
run with the bound board's values rather than trusting the script's default.

Call shape: tool `workitem`, `action="manage_label"`, `project_id`,
`workitem_id`, `add_label_id`/`remove_label_id` — one label per call.
Ready-to-run client: `scripts/plane_stdio_label.py`.

**Legacy boards (Plane)**: `px` has NO per-label or description-edit verbs.
Any label add/remove or description update on a legacy-board ticket MUST use
this local plane-mcp route. `px task create` accepts `--labels` at create time
only; `px move` changes state only; `px comment` adds a comment only.

For description or start-date updates on a legacy-board ticket (no `px` verb
exists), use the same stdio route with `action="update"` and
`description_html=` / `start_date=`. Write the description HTML to a temp
file first and pass it as a file argument — shell-escaping multi-paragraph
HTML through argv is fragile and error-prone. A minimal client:

```python
import asyncio, os, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    desc = open(sys.argv[1]).read()
    server = StdioServerParameters(
        command="/home/delorenj/code/plane-mcp-server/.venv/bin/python",
        args=["-m", "plane_mcp"],
        env={"PLANE_API_KEY": os.environ["PLANE_API_KEY"],
             "PLANE_WORKSPACE_SLUG": os.environ["PLANE_WORKSPACE_SLUG"],
             "PLANE_BASE_URL": "https://plane.delo.sh",
             "PATH": os.environ["PATH"], "HOME": os.environ["HOME"]},
    )
    async with stdio_client(server) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("workitem", arguments={
                "action": "update",
                "project_id": os.environ["PLANE_PROJECT_ID"],
                "workitem_id": "<uuid>",
                "description_html": desc,   # or "start_date": "YYYY-MM-DD"
            })
            if res.isError: sys.exit(1)

asyncio.run(main())
```

Verify with `px show <ref> --json` afterward — `description_text` can come
back empty even when the write landed; trust `description_html` length.

Behavior worth knowing:

- The server re-reads the ticket and merges — never a full-list replacement.
- The server itself refuses `agent:working` / pipeline-owned label writes
  (`PLANE_RESERVED_LABELS`), which is a feature.
- Retrieve with `expand="labels,state,assignees"` — unexpanded reads return
  UUID strings for relations, which is exactly what breaks the hub.
- **Label list returns a paginated object** (`{"results": [...]}`) not a bare
  array. When resolving a label name to UUID via the local server's
  `label(action="list", project_id=...)`, unwrap `data.get("results", data)`.
- `description_stripped` can come back empty/None in the local server's
  retrieve shape while `description_html` is intact — verify against
  `description_html`, not the stripped field.
- The server logs a FastMCP banner to stdout; read `res.content[0].text`
  and check `res.isError` — stderr noise is not an error.
- Module membership: hub `manage_module_work_items(add_ids=[...])` takes an
  **array**; the local server's `module(action="manage_workitems")` takes a
  **string**. Verify membership with the module's `list_workitems`.
- Label UUIDs: `GET /api/v1/workspaces/{ws}/projects/{project}/labels/`
  (paginated object, `results`). The `issue-labels/` path 404s on this
  instance. Write curl output to a temp file before parsing it — piping
  curl straight into python trips the security scanner.
