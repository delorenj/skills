#!/usr/bin/env python3
"""Generate a deterministic promotion-review report from recent daily memory files.

Scans memory/YYYY-MM-DD.md files and extracts lines likely worth promoting
into MEMORY.md based on durable-signal keywords.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

KEYWORDS = [
    "decision",
    "lesson",
    "rule",
    "preference",
    "always",
    "never",
    "important",
    "policy",
    "workflow",
    "standard",
]

DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


def _latest_daily_files(memory_dir: Path, days: int) -> list[Path]:
    files = [p for p in memory_dir.glob("*.md") if DATE_FILE_RE.match(p.name)]
    files.sort(key=lambda p: p.name, reverse=True)
    return files[: max(1, days)]


def _extract_candidates(path: Path, keywords: list[str]) -> list[tuple[int, str]]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[tuple[int, str]] = []
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if any(k in lower for k in keywords):
            out.append((i, line))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate memory promotion review report")
    parser.add_argument("--memory-dir", default="memory", help="Directory containing daily memory markdown files")
    parser.add_argument("--days", type=int, default=2, help="How many latest daily files to scan")
    parser.add_argument("--output", default=None, help="Output markdown path")
    parser.add_argument("--keyword", action="append", default=[], help="Additional durable-signal keyword (repeatable)")
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir).expanduser().resolve()
    files = _latest_daily_files(memory_dir, args.days)
    if not files:
        raise SystemExit(f"No daily memory files found in {memory_dir}")

    keywords = sorted(set(KEYWORDS + [k.lower() for k in args.keyword]))

    today = datetime.now().strftime("%Y-%m-%d")
    output = Path(args.output).expanduser().resolve() if args.output else memory_dir / f"promotion-review-{today}.md"

    lines: list[str] = [
        f"# Promotion Review — {today}",
        "",
        "## Files scanned",
    ]
    for f in files:
        lines.append(f"- {f}")

    lines.extend([
        "",
        "## Durable candidates",
    ])

    total = 0
    for f in files:
        candidates = _extract_candidates(f, keywords)
        if not candidates:
            continue
        lines.append("")
        lines.append(f"### {f.name}")
        for ln, text in candidates:
            lines.append(f"- [ ] {text} (Source: {f.name}#{ln})")
            total += 1

    if total == 0:
        lines.append("- No keyword-matched durable candidates found. Manual review required.")

    lines.extend([
        "",
        "## Proposed MEMORY.md update block",
        "",
        "Copy only checked items and rewrite them into concise long-term bullets:",
        "",
        "```markdown",
        "## <topic>",
        "- <durable rule/decision/preference>",
        "- <durable workflow or lesson>",
        "```",
        "",
        "## Notes",
        "- Daily notes are raw logs.",
        "- MEMORY.md should contain only durable, reusable context.",
        "",
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
