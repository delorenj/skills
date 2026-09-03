"""Publish one event data object through Bloodbank's own emitter.

Two passes, both through `bb-emit` so the skill never re-implements the
envelope: `--check` (validate, publish nothing), then, unless dry-run, the
same command with `--strict` so a bus failure is exit 1 rather than a warning.
Both outputs are recorded next to the event as `<label>-<audience>.emit.json`
whether or not they succeeded; a non-zero exit is an AcceptanceError after
the record is written.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

from .common import EVENT_TYPE, EXIT_OK, SKILL_NAME, AcceptanceError, ConfigError, read_json, write_json
from .contract import validate_event

SOURCE = "urn:33god:skill:activity-report"
ACTOR_ID = "bloodbank.skill.activity-report"
DEFAULT_BLOODBANK = os.path.join(os.path.expanduser("~"), "code", "33GOD", "bloodbank")
STEP_TIMEOUT = 120


def find_emitter() -> list[str]:
    """`$BLOODBANK_ROOT/bin/bb-emit`, then `~/code/33GOD/bloodbank/bin/bb-emit`, then `bb emit` on PATH."""
    candidates = []
    root = os.environ.get("BLOODBANK_ROOT")
    if root:
        candidates.append(os.path.join(root, "bin", "bb-emit"))
    candidates.append(os.path.join(DEFAULT_BLOODBANK, "bin", "bb-emit"))
    for path in candidates:
        if os.path.isfile(path):
            return [sys.executable or "python3", path]
    bb = shutil.which("bb")
    if bb:
        return [bb, "emit"]
    raise ConfigError("no Bloodbank emitter found: set BLOODBANK_ROOT, clone ~/code/33GOD/bloodbank, "
                      "or put `bb` on PATH")


def emit_args(event_data: dict, check: bool) -> list[str]:
    run_id = event_data["generator"]["run_id"]
    slug = event_data["project"]["slug"]
    args = [
        "--type", EVENT_TYPE,
        "--source", SOURCE,
        "--producer", SKILL_NAME,
        "--service", SKILL_NAME,
        "--actor-type", "service",
        "--actor-id", ACTOR_ID,
        "--correlation", run_id,
        "--ordering-key", f"project:{slug}",
    ]
    return (["--check"] + args) if check else (args + ["--strict"])


def _run(cmd: list[str], payload: str) -> dict:
    try:
        proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=STEP_TIMEOUT)
    except OSError as exc:
        return {"rc": 127, "stdout": "", "stderr": f"could not run {cmd[0]}: {exc}"}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "stdout": "", "stderr": f"{cmd[0]} timed out after {STEP_TIMEOUT}s"}
    return {"rc": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def _tail(step: dict) -> str:
    text = (step.get("stderr") or "").strip() or (step.get("stdout") or "").strip()
    return text[-600:]


def emit(event_data: dict, dry_run: bool) -> dict:
    """Run `--check`, then publish unless dry_run. Returns the record; raises
    AcceptanceError (with `.record` attached) when either step is non-zero."""
    validate_event(event_data)
    emitter = find_emitter()
    payload = json.dumps(event_data, ensure_ascii=False)
    record = {
        "emitter": " ".join(emitter),
        "type": EVENT_TYPE,
        "run_id": event_data["generator"]["run_id"],
        "audience": event_data["audience"],
        "ordering_key": f"project:{event_data['project']['slug']}",
        "dry_run": bool(dry_run),
        "check": None,
        "publish": None,
    }
    record["check"] = _run(emitter + emit_args(event_data, check=True), payload)
    if record["check"]["rc"] != 0:
        exc = AcceptanceError(f"bb-emit --check refused the event (rc {record['check']['rc']}): {_tail(record['check'])}")
        exc.record = record
        raise exc
    if dry_run:
        return record
    record["publish"] = _run(emitter + emit_args(event_data, check=False), payload)
    if record["publish"]["rc"] != 0:
        exc = AcceptanceError(f"bb-emit did not publish (rc {record['publish']['rc']}): {_tail(record['publish'])}")
        exc.record = record
        raise exc
    return record


def _default_out(event_path: str) -> str:
    if event_path.endswith(".event.json"):
        return event_path[:-len(".event.json")] + ".emit.json"
    return event_path + ".emit.json"


def emit_cmd(args) -> int:
    event_data = read_json(args.event)
    out = args.out or _default_out(args.event)
    try:
        record = emit(event_data, bool(args.dry_run))
    except AcceptanceError as exc:
        record = getattr(exc, "record", None)
        if record is not None:
            write_json(out, record)
        raise
    write_json(out, record)
    if getattr(args, "json", False):
        print(json.dumps(record, indent=2))
        return EXIT_OK
    check_line = (record["check"]["stdout"].strip().splitlines() or ["(no output)"])[0]
    print(f"check:   rc {record['check']['rc']}  {check_line}")
    if record["publish"] is None:
        print("publish: skipped (dry run; nothing left the machine)")
    else:
        pub_line = (record["publish"]["stderr"].strip().splitlines() or record["publish"]["stdout"].strip().splitlines()
                    or ["(no output)"])[-1]
        print(f"publish: rc {record['publish']['rc']}  {pub_line}")
    print(f"record:  {out}")
    return EXIT_OK
