#!/usr/bin/env python3
"""Single-label add/remove on a Plane ticket via the local plane-mcp-server.

Fallback for when the Pipeline MCP Hub's manage_work_item_label fails its
response-model validation (UUID-vs-object Pydantic error) before writing.

Usage:
    python3 plane_stdio_label.py <workitem_uuid> <label_uuid> [--remove]

Environment (required):
    PLANE_API_KEY         plane.delo.sh API key
Optional overrides:
    PLANE_PROJECT_ID      board uuid (default: JIMB a8a12be1-...)
    PLANE_WORKSPACE_SLUG  default automaticai
    PLANE_BASE_URL        default https://plane.delo.sh

Verified end-to-end on JIMB-403 (2026-10-09): hub route failed pre-write,
this route landed the label, read-back confirmed.

Always prints the ticket's labels/state/priority afterward as verification.
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PY = "/home/delorenj/code/plane-mcp-server/.venv/bin/python"
DEFAULT_PROJECT = "a8a12be1-b3ab-44f4-ab24-abe8829aeb72"  # JIMB

USAGE = "usage: plane_stdio_label.py [workitem_uuid label_uuid [--remove]]"


def server_env() -> dict[str, str]:
    env = {
        "PLANE_API_KEY": os.environ["PLANE_API_KEY"],
        "PLANE_WORKSPACE_SLUG": os.environ.get("PLANE_WORKSPACE_SLUG", "automaticai"),
        "PLANE_BASE_URL": os.environ.get("PLANE_BASE_URL", "https://plane.delo.sh"),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/home/delorenj"),
    }
    return env


async def run(project: str, workitem: str, label: str | None, remove: bool) -> None:
    params = StdioServerParameters(command=SERVER_PY, args=["-m", "plane_mcp"], env=server_env())
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            if label:
                action = "remove_label_id" if remove else "add_label_id"
                res = await session.call_tool(
                    "workitem",
                    {
                        "action": "manage_label",
                        "project_id": project,
                        "workitem_id": workitem,
                        action: label,
                    },
                )
                print(f"{action} isError: {res.isError}")
                if res.isError:
                    print((res.content[0].text if res.content else "")[:500])
                    sys.exit(1)

            res = await session.call_tool(
                "workitem",
                {
                    "action": "retrieve",
                    "project_id": project,
                    "workitem_id": workitem,
                    "expand": "labels,state,assignees",
                },
            )
            ticket = json.loads(res.content[0].text)
            labels = sorted(l["name"] for l in ticket.get("labels", []))
            state = ticket.get("state")
            state_name = state.get("name") if isinstance(state, dict) else state
            print("labels:", labels)
            print("state:", state_name, "| priority:", ticket.get("priority"))


def main() -> None:
    if not os.environ.get("PLANE_API_KEY"):
        sys.exit("PLANE_API_KEY not set")
    project = os.environ.get("PLANE_PROJECT_ID", DEFAULT_PROJECT)

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    remove = "--remove" in sys.argv
    if len(args) != 2:
        sys.exit(USAGE)
    asyncio.run(run(project, args[0], args[1], remove))


if __name__ == "__main__":
    main()
