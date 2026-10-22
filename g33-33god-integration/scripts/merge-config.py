#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Merge module configuration into shared _bmad/config.yaml + config.user.yaml.

g33 variant of the canonical standalone-module merge script. The full-safe
install path is `g33_install.py` (conflict preflight, dry-run, operator-edit
preservation); this thin wrapper exists to satisfy the canonical standalone
module structure expected by the BMad module validator and performs the same
surgical YAML-section merge for simple pipelines.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g33_install  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge g33 module config into shared _bmad/config.yaml."
    )
    parser.add_argument("--project-root", required=True,
                        help="Project root containing _bmad/")
    args = parser.parse_args()
    plan = g33_install.plan_install(Path(args.project_root).resolve(), force=False)
    if plan.get("status") == "error":
        sys.stderr.write(json.dumps(plan) + "\n")
        return 1
    performed = g33_install.execute_plan(plan, dry_run=False)
    sys.stdout.write(json.dumps({
        "status": "success",
        "performed": performed,
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
