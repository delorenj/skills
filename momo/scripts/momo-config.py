#!/usr/bin/env python3
"""momo-config — per-repo Momo board config (.momo/config.json) + lane detection.

Momo's normalized stages are
`backlog | unstarted | started | in_review | completed | cancelled`,
but a repo's kanban columns rarely match 1:1. This tool lets Momo learn a repo's real
lanes ONCE and codify the mapping locally, so the shared board adapter stays generic
and the per-repo lanes are just data.

Ops:
    detect  --root R    Fetch the live board lanes (via the bundled provider) and report
                        which are unmapped and which mapped targets are missing. Momo runs
                        this on first use; if the board is non-standard it asks the operator
                        to map the odd lanes, then calls `set`.
    show    --root R     Print the current .momo/config.json (or the standard defaults).
    set     --root R --lanes '<json>' [--write-targets '<json>'] [--notes '<json>']
                        Write .momo/config.json (validated shape).

`detect` shells out to ../providers/trello.py `resolve`, so it uses the same creds/board
resolution as the adapter (no duplicated transport).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROVIDERS = os.path.join(HERE, "providers")
sys.path.insert(0, PROVIDERS)

from trello import (  # type: ignore[import]  # noqa: E402
    ConfigError,
    NORMALIZED_STATES,
    state_for_lane,
    validate_lane_config,
)

STATES = list(NORMALIZED_STATES)


def provider_resolve(root: str) -> dict:
    out = subprocess.run(
        [sys.executable, os.path.join(HERE, "providers", "trello.py"), "resolve", "--root", root],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.stderr.write(out.stderr)
        raise SystemExit(out.returncode or 2)
    return json.loads(out.stdout)


def config_path(root: str) -> str:
    return os.path.join(root, ".momo", "config.json")


def cmd_detect(root: str) -> int:
    info = provider_resolve(root)
    lm = info["list_map"]
    board_lists = info["board_lists"]
    live_lane_names = {
        lane.casefold()
        for lane in board_lists
        if isinstance(lane, str)
    }
    unmapped = [l for l in board_lists if state_for_lane(l, lm) == "other"]
    missing = {
        state: lm[state]
        for state in STATES
        if not any(
            lane.casefold() in live_lane_names
            for lane in lm.get(state, [])
        )
    }
    report = {
        "board_name": info.get("board_name", ""),
        "board_id": info.get("board_id", ""),
        "config_present": info.get("config_present", False),
        "board_lists": board_lists,
        "current_lane_map": lm,
        "unmapped_lanes": unmapped,          # board columns no stage claims -> classified "other"
        "states_with_missing_lane": missing,  # stages whose mapped lane(s) aren't on the board
        "is_standard": not unmapped and not missing,
    }
    print(json.dumps(report, indent=2))
    return 0


def cmd_show(root: str) -> int:
    path = config_path(root)
    if os.path.isfile(path):
        print(open(path, encoding="utf-8").read())
    else:
        print(json.dumps({"note": "no .momo/config.json — adapter uses standard defaults"}, indent=2))
    return 0


def cmd_set(root: str, lanes: str, write_targets: str | None, notes: str | None) -> int:
    try:
        lanes_obj = json.loads(lanes)
        cfg = {
            "provider": "trello",
            "lanes": lanes_obj,
        }
        if write_targets is not None:
            cfg["write_targets"] = json.loads(write_targets)
        if notes is not None:
            notes_obj = json.loads(notes)
            if not isinstance(notes_obj, dict):
                raise ConfigError("lane_notes must be an object of lane -> note")
            for lane, note in notes_obj.items():
                if (
                    not isinstance(lane, str)
                    or not lane
                    or lane != lane.strip()
                ):
                    raise ConfigError("lane_notes keys must be non-blank exact strings")
                if not isinstance(note, str):
                    raise ConfigError(f"lane_notes[{lane!r}] must be a string")
            cfg["lane_notes"] = notes_obj
        validate_lane_config(cfg)
    except (ValueError, TypeError) as exc:
        sys.stderr.write(f"momo-config: invalid configuration: {exc}\n")
        return 2

    path = config_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(cfg, indent=2) + "\n")
    print(f"wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="op", required=True)
    for name in ("detect", "show"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=os.getcwd())
    ps = sub.add_parser("set")
    ps.add_argument("--root", default=os.getcwd())
    ps.add_argument("--lanes", required=True, help="JSON: {state: [lane, ...]}")
    ps.add_argument("--write-targets", default=None, help="JSON: {state: lane} canonical write lane")
    ps.add_argument("--notes", default=None, help="JSON: {lane: 'meaning'} human semantics")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if args.op == "detect":
        return cmd_detect(root)
    if args.op == "show":
        return cmd_show(root)
    if args.op == "set":
        return cmd_set(root, args.lanes, args.write_targets, args.notes)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
