#!/usr/bin/env python3
"""Validate that router targets referenced in 33god/SKILL.md exist."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
PATTERN = re.compile(r"(?:references|workflows|scripts)/[A-Za-z0-9._/-]+\.(?:md|py)")


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    refs = sorted(set(PATTERN.findall(text)))
    missing: list[str] = []

    print(f"Checking {len(refs)} router target(s) from {SKILL}")
    for rel in refs:
        p = ROOT / rel
        if p.exists():
            print(f"  OK   {rel}")
        else:
            print(f"  MISS {rel}")
            missing.append(rel)

    if missing:
        print("\nRouter check failed. Missing targets:")
        for m in missing:
            print(f"- {m}")
        return 1

    print("\nRouter check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
