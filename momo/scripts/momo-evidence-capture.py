#!/usr/bin/env python3
"""momo-evidence-capture — CLI wrapper for the canonical evidence-capture library."""
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(_LIB))

from momo_evidence import main  # type: ignore[import]  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
