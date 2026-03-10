#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

START = "<!-- 33GOD:ROLE_CHARTER:START -->"
END = "<!-- 33GOD:ROLE_CHARTER:END -->"

DEFAULT_PRIME_DIRECTIVES = """# 33GOD Prime Directives (Global)

These directives are **always on** for every agent unless Jarad explicitly overrides them.

1. **Build the 33GOD platform first.**
2. **Maximize autonomy and reduce downtime.**
3. **Monetization over busywork.**
4. **Truth over comfort.**
5. **Template discipline.**
6. **Ticket-first execution (no-ticket, no-work).**
7. **Finish the turn: commit and push.**
"""


def load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ensure_governance_files(governance_dir: Path) -> tuple[Path, Path]:
    governance_dir.mkdir(parents=True, exist_ok=True)
    prime_path = governance_dir / "PRIME_DIRECTIVES.md"
    matrix_path = governance_dir / "AGENT_ROLE_MATRIX.json"

    if not prime_path.exists():
        prime_path.write_text(DEFAULT_PRIME_DIRECTIVES, encoding="utf-8")

    if not matrix_path.exists():
        save_json(
            matrix_path,
            {
                "generatedAtPolicy": "Update this map first, then apply role charters.",
                "agents": [],
            },
        )

    return prime_path, matrix_path


def load_prime_bullets(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    bullets: list[str] = []
    for line in lines:
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            bullets.append(f"- {m.group(1).strip()}")
    return "\n".join(bullets)


def local_directives_section(local_directives: list[str]) -> str:
    clean = [d.strip() for d in local_directives if d and d.strip()]
    if not clean:
        return ""
    lines = "\n".join(f"- {d}" for d in clean)
    return f"\n### Agent-Specific Directives\n{lines}\n"


def build_block(row: dict, prime_bullets: str) -> str:
    local_section = local_directives_section(row.get("localDirectives", []))
    return (
        f"{START}\n"
        f"## 33GOD Role Charter (Template Managed)\n\n"
        f"- **Agent:** {row['agent']}\n"
        f"- **Role:** {row['role']}\n"
        f"- **Reports to:** {row['reportsTo']}\n"
        f"- **Mission:** {row['mission']}\n\n"
        f"### Prime Objectives (Inherited Global)\n"
        f"{prime_bullets}\n"
        f"{local_section}\n"
        f"### Local Operating Rule\n"
        f"- Treat these role + prime objective constraints as active context for every request unless Jarad overrides them explicitly.\n\n"
        f"{END}"
    )


def inject_or_replace(content: str, block: str) -> str:
    if START in content and END in content:
        pattern = re.compile(rf"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
        return pattern.sub(block, content)

    lines = content.splitlines()
    if lines and lines[0].startswith("#"):
        insert_at = 1
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        return "\n".join(lines[:insert_at] + ["", block, ""] + lines[insert_at:]).rstrip() + "\n"

    return block + "\n\n" + content


def upsert_agent(
    matrix_path: Path,
    workspace: str,
    agent: str,
    role: str,
    reports_to: str,
    mission: str,
    directives: list[str] | None,
) -> dict:
    matrix = load_json(
        matrix_path,
        {"generatedAtPolicy": "Update this map first, then apply role charters.", "agents": []},
    )
    agents = matrix.setdefault("agents", [])

    existing = None
    for row in agents:
        if row.get("workspace") == workspace:
            existing = row
            break

    if existing is None:
        existing = {
            "workspace": workspace,
            "agent": agent,
            "role": role,
            "reportsTo": reports_to,
            "mission": mission,
            "localDirectives": directives or [],
        }
        agents.append(existing)
        action = "created"
    else:
        existing["agent"] = agent
        existing["role"] = role
        existing["reportsTo"] = reports_to
        existing["mission"] = mission
        if directives is not None:
            existing["localDirectives"] = directives
        else:
            existing.setdefault("localDirectives", [])
        action = "updated"

    save_json(matrix_path, matrix)
    return {"action": action, "workspace": workspace, "agent": agent}


def apply_charters(prime_path: Path, matrix_path: Path) -> dict:
    matrix = load_json(matrix_path, {"agents": []})
    prime_bullets = load_prime_bullets(prime_path)

    updated = 0
    skipped = 0

    for row in matrix.get("agents", []):
        agents_md = Path(row["workspace"]) / "AGENTS.md"
        if not agents_md.exists():
            skipped += 1
            continue

        original = agents_md.read_text(encoding="utf-8")
        rendered = inject_or_replace(original, build_block(row, prime_bullets))
        if rendered != original:
            agents_md.write_text(rendered, encoding="utf-8")
            updated += 1

    return {"updated": updated, "skipped": skipped, "total": len(matrix.get("agents", []))}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Manage template-driven 33GOD role charters.")
    p.add_argument(
        "--governance-dir",
        default=str(Path.home() / ".openclaw/workspace/frameworks/agent-governance"),
        help="Directory containing PRIME_DIRECTIVES.md and AGENT_ROLE_MATRIX.json",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    upsert = sub.add_parser("upsert", help="Create/update an agent role matrix row")
    for sp in (upsert,):
        sp.add_argument("--workspace", required=True)
        sp.add_argument("--agent", required=True)
        sp.add_argument("--role", required=True)
        sp.add_argument("--reports-to", required=True)
        sp.add_argument("--mission", required=True)
        sp.add_argument("--directive", action="append", default=None, help="Repeatable per-agent directive")

    upsert_apply = sub.add_parser("upsert-and-apply", help="Upsert one row then apply to all AGENTS.md files")
    upsert_apply.add_argument("--workspace", required=True)
    upsert_apply.add_argument("--agent", required=True)
    upsert_apply.add_argument("--role", required=True)
    upsert_apply.add_argument("--reports-to", required=True)
    upsert_apply.add_argument("--mission", required=True)
    upsert_apply.add_argument("--directive", action="append", default=None, help="Repeatable per-agent directive")

    sub.add_parser("apply", help="Apply current matrix + prime directives to all AGENTS.md files")

    return p.parse_args()


def main() -> None:
    args = parse_args()
    governance_dir = Path(args.governance_dir).expanduser().resolve()
    prime_path, matrix_path = ensure_governance_files(governance_dir)

    result: dict = {}

    if args.cmd == "upsert":
        result["upsert"] = upsert_agent(
            matrix_path=matrix_path,
            workspace=args.workspace,
            agent=args.agent,
            role=args.role,
            reports_to=args.reports_to,
            mission=args.mission,
            directives=args.directive,
        )
    elif args.cmd == "apply":
        result["apply"] = apply_charters(prime_path=prime_path, matrix_path=matrix_path)
    elif args.cmd == "upsert-and-apply":
        result["upsert"] = upsert_agent(
            matrix_path=matrix_path,
            workspace=args.workspace,
            agent=args.agent,
            role=args.role,
            reports_to=args.reports_to,
            mission=args.mission,
            directives=args.directive,
        )
        result["apply"] = apply_charters(prime_path=prime_path, matrix_path=matrix_path)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
