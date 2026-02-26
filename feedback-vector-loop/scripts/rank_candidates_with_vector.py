#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]{1,}")


def tok(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def main() -> int:
    ap = argparse.ArgumentParser(description="Rank candidates using directional feedback vector")
    ap.add_argument("--candidates", required=True, help="JSON object with {candidates:[...]}")
    ap.add_argument("--vector", required=True, help="feedback_vector.json")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    candidates = json.loads(Path(args.candidates).expanduser().resolve().read_text(encoding="utf-8"))
    vector = json.loads(Path(args.vector).expanduser().resolve().read_text(encoding="utf-8"))

    weights = {k: float(v) for k, v in vector.get("token_adjustments", [])}
    replace_map = {str(k).lower(): str(v).lower() for k, v in vector.get("replace_map", {}).items()}

    ranked = []
    for c in candidates.get("candidates", []):
        text = f"{c.get('title','')} {c.get('slogan','')} {c.get('rationale','')}"
        tks = tok(text)

        vector_score = sum(weights.get(t, 0.0) for t in tks)

        replace_bonus = 0.0
        replace_penalty = 0.0
        lower = text.lower()
        for old, new in replace_map.items():
            if old in lower:
                replace_penalty += 0.8
            if new in lower:
                replace_bonus += 0.8

        total = vector_score + replace_bonus - replace_penalty
        ranked.append(
            {
                "candidate": c,
                "score": round(total, 3),
                "breakdown": {
                    "vector_score": round(vector_score, 3),
                    "replace_bonus": round(replace_bonus, 3),
                    "replace_penalty": round(replace_penalty, 3),
                },
            }
        )

    ranked.sort(key=lambda r: r["score"], reverse=True)

    out = {
        "ranked": ranked,
        "winner": ranked[0]["candidate"] if ranked else None,
        "stats": {
            "candidate_count": len(ranked),
            "vector_tokens": len(weights),
            "replace_rules": len(replace_map),
        },
    }

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
