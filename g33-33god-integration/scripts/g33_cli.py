#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""g33 consumable CLI: preflight, route, evidence, setup.

Safe surface for PJangler and humans: --json mode exits 0 on findings
(nonzero only for usage/IO errors). All printed output is secret-scrubbed
(values whose key names look secret-y are replaced with [REDACTED]).

preflight and route CONSUME --project-root: the module's installed answers
in _bmad/custom/config.toml (the layer the real upstream resolver merges)
feed runtime routing, doctrine pointer and preflight reporting.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g33lib as G  # noqa: E402

MODULE_ROOT = Path(__file__).resolve().parent.parent


def cmd_preflight(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    result = G.run_preflight(project_root, MODULE_ROOT)
    G.emit_json(result)
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    result = G.ecosystem_route(MODULE_ROOT, args.request,
                               project_root=project_root)
    G.emit_json(result)
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    bundle_path = Path(args.bundle).resolve()
    if not bundle_path.is_file():
        G.emit_json({"status": "error",
                     "error": f"bundle not found: {bundle_path}"})
        return 1
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        G.emit_json({"status": "error", "error": f"cannot read bundle: {err}"})
        return 1
    if not isinstance(bundle, dict):
        G.emit_json({"status": "error", "error": "bundle must be a JSON object"})
        return 1
    errors = G.validate_bundle(bundle)
    if errors:
        G.emit_json({"status": "error", "errors": errors})
        return 1
    handoff = G.generate_handoff(MODULE_ROOT, bundle)
    out_path = Path(args.out).resolve() if args.out else None
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(handoff, encoding="utf-8")
    G.emit_json({
        "status": "ok",
        "bundle": str(bundle_path),
        "out": str(out_path) if out_path else None,
        "handoff_bytes": len(handoff.encode("utf-8")),
    })
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    install_script = MODULE_ROOT / "scripts" / "g33_install.py"
    cmd = [sys.executable, "-B", str(install_script),
           "--project-root", str(Path(args.project_root).resolve())]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.force:
        cmd.append("--force")
    if args.answers:
        cmd += ["--answers", args.answers]
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="g33",
        description="33GOD Integration (g33): preflight, ecosystem routing, "
                    "and evidence-to-handoff for BMAD projects.",
    )
    parser.add_argument("--version", action="version",
                        version=f"g33 {G.MODULE_VERSION} ({G.MODULE_NAME})")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("preflight", help="Validate project bindings, tools, enrollment")
    p.add_argument("--project-root", required=True)
    p.add_argument("--json", action="store_true", default=True)
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("route", help="Route a work request to owner components")
    p.add_argument("--project-root", required=True)
    p.add_argument("--request", required=True)
    p.add_argument("--json", action="store_true", default=True)
    p.set_defaults(func=cmd_route)

    p = sub.add_parser("evidence", help="Turn an evidence bundle into a handoff")
    p.add_argument("--project-root", required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--json", action="store_true", default=True)
    p.set_defaults(func=cmd_evidence)

    p = sub.add_parser("setup", help="Install/reconfigure the g33 module")
    p.add_argument("--project-root", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--answers", default=None,
                   help="JSON answers file validated against module.yaml variables")
    p.add_argument("--json", action="store_true", default=True)
    p.set_defaults(func=cmd_setup)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
