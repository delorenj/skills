#!/usr/bin/env python3
"""plane_lane — Momo's normalized state -> the Plane lane `px move` writes to (MOMO-8).

`momo-board.sh transition <id> <target>` on a Plane board goes through px, and px
takes exact lane names. The target is resolved the way the Trello adapter does:

1. `<root>/.momo/config.json` `write_targets[<state>]`, else `lanes[<state>][0]`;
2. else the 33GOD canon lane for the state (the Krebs LANES every standard board
   carries, and what the fleet's role.yaml state maps already say);
3. else the target itself, as a literal lane name.

No guess happens here: px move resolves the name strictly and fails loudly,
listing the board's lanes, when it is not on the board.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Normalized state -> canon lane. Matches krebs contract.py LANES and the
# state_map of every deployed hermes PM role.yaml.
CANON = {
    "backlog": "Backlog",
    "unstarted": "Todo",
    "started": "In Progress",
    "in_review": "E2E Testing & QA",
    "completed": "Done",
    "cancelled": "Cancelled",
    "awaiting_decision": "Needs Attention",
    "e2e_testing": "E2E Testing & QA",
    "ready_for_documentation": "Ready for Documentation",
    "needs_re_evaluation": "Needs Re-evaluation",
}

# The tp adapter's aliases for the same states.
ALIASES = {"needs_attention": "awaiting_decision", "waiting_reply": "awaiting_decision"}


def lane_for(root: Path, target: str) -> str:
    state = ALIASES.get(target, target)
    config_path = root / ".momo" / "config.json"
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise SystemExit(f"momo-board: invalid {config_path}: {exc}")
        written = (config.get("write_targets") or {}).get(state)
        if written:
            return str(written)
        lanes = (config.get("lanes") or {}).get(state) or []
        if lanes:
            return str(lanes[0])
    return CANON.get(state, target)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: plane_lane.py <root> <normalized-state|lane>", file=sys.stderr)
        return 2
    print(lane_for(Path(argv[1]), argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
