#!/usr/bin/env python3
"""momo-worker-handback — CLI for the canonical worker hand-back bundle.

Thin wrapper around momo/skill/scripts/lib/momo_handback.py so the script lives
in the skill tree and can be invoked from either Momo or the Hermes PM role.
"""
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(_LIB))

from momo_handback import main  # type: ignore[import]  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
