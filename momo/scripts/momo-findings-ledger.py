#!/usr/bin/env python3
"""momo-findings-ledger — CLI wrapper for the canonical findings-ledger library."""
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(_LIB))

from momo_findings import main  # type: ignore[import]  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
