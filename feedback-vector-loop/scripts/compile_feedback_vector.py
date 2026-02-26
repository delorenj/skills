#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]{1,}")


def tok(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def compile_vector(rows: list[dict]) -> dict:
    weights: defaultdict[str, float] = defaultdict(float)
    replace_map: dict[str, str] = {}

    for row in rows:
        verdict = str(row.get("verdict", "revise")).lower()
        direction = row.get("direction", {}) or {}
        candidate = row.get("candidate", {}) or {}

        for t in direction.get("more", []):
            weights[str(t).lower()] += 1.3
        for t in direction.get("less", []):
            weights[str(t).lower()] -= 1.0
        for t in direction.get("avoid", []):
            weights[str(t).lower()] -= 2.2

        for old, new in (direction.get("replace", {}) or {}).items():
            old = str(old).lower()
            new = str(new).lower()
            replace_map[old] = new
            weights[old] -= 1.2
            weights[new] += 1.2

        text = f"{candidate.get('title','')} {candidate.get('slogan','')} {candidate.get('rationale','')}"
        for t in tok(text):
            if verdict == "up":
                weights[t] += 0.2
            elif verdict == "down":
                weights[t] -= 0.25

    return {
        "version": "1.0",
        "token_adjustments": sorted(weights.items(), key=lambda kv: abs(kv[1]), reverse=True),
        "replace_map": replace_map,
        "stats": {
            "rows": len(rows),
            "nonzero_tokens": len(weights),
            "replace_rules": len(replace_map),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compile directional feedback into vector profile")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    rows = load_jsonl(Path(args.input).expanduser().resolve())
    vector = compile_vector(rows)

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(vector, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
