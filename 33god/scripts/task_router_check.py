#!/usr/bin/env python3
"""Validate that router targets referenced in 33god/SKILL.md and references/index.md exist."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
INDEX = ROOT / "references" / "index.md"

# Pattern for SKILL.md: matches paths like references/foo.md, workflows/bar.md, scripts/baz.py
SKILL_PATTERN = re.compile(r"(?:references|workflows|scripts)/[A-Za-z0-9._/-]+\.(?:md|py)")

# Pattern for index.md: matches relative .md references like `filename.md`
INDEX_PATTERN = re.compile(r"`([A-Za-z0-9._/-]+\.md)`")


def check_skill_md() -> tuple[list[str], list[str]]:
    """Check references from SKILL.md. Returns (ok_list, missing_list)."""
    text = SKILL.read_text(encoding="utf-8")
    refs = sorted(set(SKILL_PATTERN.findall(text)))
    ok: list[str] = []
    missing: list[str] = []

    print(f"Checking {len(refs)} router target(s) from {SKILL}")
    for rel in refs:
        p = ROOT / rel
        if p.exists():
            print(f"  OK   {rel}")
            ok.append(rel)
        else:
            print(f"  MISS {rel}")
            missing.append(rel)

    return ok, missing


def check_index_md() -> tuple[list[str], list[str]]:
    """Check references from references/index.md. Returns (ok_list, missing_list)."""
    text = INDEX.read_text(encoding="utf-8")
    # Find relative .md references and prefix with references/
    matches = sorted(set(INDEX_PATTERN.findall(text)))
    refs = [f"references/{m}" for m in matches]
    ok: list[str] = []
    missing: list[str] = []

    print(f"\nChecking {len(refs)} router target(s) from {INDEX}")
    for rel in refs:
        p = ROOT / rel
        if p.exists():
            print(f"  OK   {rel}")
            ok.append(rel)
        else:
            print(f"  MISS {rel}")
            missing.append(rel)

    return ok, missing


def main() -> int:
    skill_ok, skill_missing = check_skill_md()
    index_ok, index_missing = check_index_md()

    all_missing = skill_missing + index_missing

    if all_missing:
        print(f"\nRouter check failed. {len(all_missing)} missing target(s):")
        for m in all_missing:
            print(f"- {m}")
        return 1

    total_ok = len(skill_ok) + len(index_ok)
    print(f"\nRouter check passed. {total_ok} target(s) verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
