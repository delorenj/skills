#!/usr/bin/env python3
"""Audit consolidated 33god skill structure for required files."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md",
    "references/index.md",
    "references/project-creation.md",
    "references/task-execution.md",
    "references/coding-workflow.md",
    "references/service-development.md",
    "references/workflow-generation.md",
    "references/event-command-lifecycle.md",
    "references/platform-lifecycle.md",
    "references/god-doc-policy.md",
    "workflows/project-bootstrap.md",
    "workflows/task-intake.md",
    "workflows/coding-delivery.md",
    "workflows/event-contract-rollout.md",
    "scripts/task_router_check.py",
]


def main() -> int:
    missing = []
    for rel in REQUIRED:
        p = ROOT / rel
        if p.exists():
            print(f"OK   {rel}")
        else:
            print(f"MISS {rel}")
            missing.append(rel)

    if missing:
        print("\nAudit failed. Missing required files:")
        for m in missing:
            print(f"- {m}")
        return 1

    print("\nAudit passed. Consolidated structure is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
