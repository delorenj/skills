#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Merge module help entries into shared _bmad/module-help.csv.

g33 variant of the canonical standalone-module merge script: same anti-zombie
contract (remove this module's rows, append fresh ones, preserve other modules'
rows and the target header), implemented against g33lib so the installer and
this wrapper share one implementation. Kept as `merge-help-csv.py` because the
BMad module validator expects the canonical script names.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g33lib as G  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge g33 module help entries into shared _bmad/module-help.csv."
    )
    parser.add_argument("--target", required=True,
                        help="Path to the target _bmad/module-help.csv file")
    parser.add_argument("--source", required=False,
                        help="Optional source CSV (defaults to this module's "
                             "assets/module-help.csv)")
    args = parser.parse_args()

    target = Path(args.target)
    source = Path(args.source) if args.source else (
        Path(__file__).resolve().parent.parent / "assets" / "module-help.csv")

    target_text = target.read_text(encoding="utf-8") if target.exists() else ""
    merged, appended = G.merge_help_csv(target_text, source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(merged, encoding="utf-8")
    print(json.dumps({
        "status": "success",
        "target": str(target.resolve()),
        "rows_appended": len(appended),
        "module": G.MODULE_NAME,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
