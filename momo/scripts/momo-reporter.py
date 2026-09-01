#!/usr/bin/env python3
"""momo-reporter — CLI wrapper for the canonical deduplicated board reporter."""
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(_LIB))

from momo_reporter import main  # type: ignore[import]  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
