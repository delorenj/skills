#!/usr/bin/env python3
"""momo-worker-monitor — CLI wrapper for the canonical worker monitor library."""
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(_LIB))

from momo_worker_monitor import main  # type: ignore[import]  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
