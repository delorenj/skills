#!/usr/bin/env python3
"""Write a deterministic context-compaction checkpoint artifact.

Default output matches the required heartbeat artifact:
memory/context-compaction-latest.md
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def _ensure_three(items: list[str], filler: str) -> list[str]:
    out = [i.strip() for i in items if i and i.strip()]
    while len(out) < 3:
        out.append(filler)
    return out[:3]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic context compaction checkpoint markdown")
    parser.add_argument("--output", default="memory/context-compaction-latest.md", help="Output markdown path")
    parser.add_argument("--active-task", action="append", default=[], help="Active task (repeatable)")
    parser.add_argument("--decision", action="append", default=[], help="Decision made (repeatable)")
    parser.add_argument("--blocker", action="append", default=[], help="Open blocker (repeatable)")
    parser.add_argument("--next-action", action="append", default=[], help="Next action on resume (repeatable)")
    parser.add_argument("--handoff", action="append", default=[], help="Critical handoff context link/file (repeatable)")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    active = args.active_task or ["TBD"]
    decisions = args.decision or ["TBD"]
    blockers = args.blocker or ["None"]
    next_actions = _ensure_three(args.next_action, "TBD")
    handoff = args.handoff or ["TBD"]

    lines: list[str] = [
        "# Context Compaction Checkpoint",
        "",
        f"Generated: {ts}",
        "",
        "1) Active tasks",
    ]
    lines.extend([f"- {x}" for x in active])

    lines.extend([
        "",
        "2) Decisions made",
    ])
    lines.extend([f"- {x}" for x in decisions])

    lines.extend([
        "",
        "3) Open blockers",
    ])
    lines.extend([f"- {x}" for x in blockers])

    lines.extend([
        "",
        "4) Next 3 actions on resume",
    ])
    lines.extend([f"{i+1}. {x}" for i, x in enumerate(next_actions)])

    lines.extend([
        "",
        "5) Handoff context (critical links/files)",
    ])
    lines.extend([f"- {x}" for x in handoff])
    lines.append("")

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
