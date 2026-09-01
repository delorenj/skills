"""momo_findings — stable findings ledger per issue (33GPM-6).

Replaces prose findings with a stable checklist/table. Each finding has an ID,
severity, category, state, and evidence pointer. The ledger is persisted per
issue and can be rendered as Markdown for evidence files.

Design pattern: Repository — Ledger owns the collection and enforces ID uniqueness.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
FINDINGS_DIR = Path("_bmad-output/implementation-artifacts/findings")


class FindingsError(Exception):
    pass


@dataclass
class Finding:
    id: str
    severity: str  # critical | high | medium | low | note
    category: str
    description: str
    state: str = "open"  # open | resolved | wontfix
    evidence: str = ""
    created_at: str = field(default_factory=lambda: _now_iso())
    resolved_at: str = ""
    resolver: str = ""

    def resolve(self, resolver: str = "") -> None:
        self.state = "resolved"
        self.resolved_at = _now_iso()
        self.resolver = resolver

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FindingsLedger:
    schema_version: str = SCHEMA_VERSION
    issue: str = ""
    findings: list[Finding] = field(default_factory=list)

    def ids(self) -> set[str]:
        return {f.id for f in self.findings}

    def next_id(self) -> str:
        nums = []
        for f in self.findings:
            m = re.match(r"F(\d+)", f.id)
            if m:
                nums.append(int(m.group(1)))
        n = max(nums, default=0) + 1
        return f"F{n:03d}"

    def add(self, finding: Finding) -> Finding:
        if finding.id in self.ids():
            raise FindingsError(f"finding {finding.id} already exists")
        if not finding.id:
            finding.id = self.next_id()
        self.findings.append(finding)
        return finding

    def get(self, fid: str) -> Finding:
        for f in self.findings:
            if f.id == fid:
                return f
        raise FindingsError(f"finding {fid} not found")

    def resolve(self, fid: str, resolver: str = "") -> Finding:
        f = self.get(fid)
        f.resolve(resolver)
        return f

    def open_count(self) -> int:
        return sum(1 for f in self.findings if f.state == "open")

    def resolved_count(self) -> int:
        return sum(1 for f in self.findings if f.state == "resolved")

    def by_severity(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = {}
        for f in self.findings:
            out.setdefault(f.severity, []).append(f)
        return out

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise FindingsError(f"unsupported schema_version {self.schema_version}")
        for f in self.findings:
            if f.severity not in {"critical", "high", "medium", "low", "note"}:
                raise FindingsError(f"invalid severity {f.severity}")
            if f.state not in {"open", "resolved", "wontfix"}:
                raise FindingsError(f"invalid state {f.state}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "issue": self.issue,
            "findings": [f.to_dict() for f in self.findings],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FindingsLedger:
        if d.get("schema_version") != SCHEMA_VERSION:
            raise FindingsError("schema_version mismatch")
        return cls(
            schema_version=d["schema_version"],
            issue=d.get("issue", ""),
            findings=[Finding(**f) for f in d.get("findings", [])],
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_finding_id(raw: str) -> str:
    """Accept F-001, F001, f-001, f001 and normalize to F001."""
    m = re.match(r"[Ff]-?(\d+)", raw.strip())
    if m:
        return f"F{int(m.group(1)):03d}"
    return raw.strip()


def _repo_root(start: Path | None = None) -> Path:
    d = Path(start or os.getcwd()).resolve()
    while d != d.parent:
        if (d / ".project.json").is_file():
            return d
        d = d.parent
    raise FindingsError("no .project.json found")


def ledger_path(issue: str, root: Path | None = None) -> Path:
    return _repo_root(root) / FINDINGS_DIR / f"{issue}.findings.json"


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".findings-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def load(issue: str, root: Path | None = None) -> FindingsLedger:
    p = ledger_path(issue, root)
    if not p.is_file():
        return FindingsLedger(issue=issue)
    return FindingsLedger.from_dict(json.loads(p.read_text()))


def save(ledger: FindingsLedger, root: Path | None = None) -> Path:
    ledger.validate()
    p = ledger_path(ledger.issue or "unknown", root)
    _write_atomic(p, ledger.to_dict())
    return p


def render_markdown(ledger: FindingsLedger) -> str:
    lines = [f"## Findings ledger for {ledger.issue}\n"]
    lines.append(f"Open: {ledger.open_count()} | Resolved: {ledger.resolved_count()} | Total: {len(ledger.findings)}\n")
    if not ledger.findings:
        lines.append("No findings recorded.\n")
        return "\n".join(lines)
    lines.append("| ID | Severity | Category | State | Description | Evidence |")
    lines.append("|---|---|---|---|---|---|")
    for f in ledger.findings:
        evidence = f.evidence or ""
        desc = f.description.replace("|", "\\|")
        lines.append(f"| {f.id} | {f.severity} | {f.category} | {f.state} | {desc} | {evidence} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stable findings ledger")
    ap.add_argument("--issue", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="add a finding")
    add.add_argument("--id", default="", help="finding ID (auto-generated if empty)")
    add.add_argument("--severity", required=True, choices=["critical", "high", "medium", "low", "note"])
    add.add_argument("--category", required=True)
    add.add_argument("--description", required=True)
    add.add_argument("--evidence", default="")
    add.set_defaults(func=lambda args, ledger: ledger.add(Finding(
        id=args.id,
        severity=args.severity,
        category=args.category,
        description=args.description,
        evidence=args.evidence,
    )))

    resolve = sub.add_parser("resolve", help="resolve a finding")
    resolve.add_argument("--id", required=True)
    resolve.add_argument("--resolver", default="")
    resolve.set_defaults(func=lambda args, ledger: ledger.resolve(_normalize_finding_id(args.id), args.resolver))

    show = sub.add_parser("show", help="show ledger JSON")
    show.set_defaults(func=lambda args, ledger: print(json.dumps(ledger.to_dict(), indent=2)))

    md = sub.add_parser("markdown", help="render ledger as Markdown")
    md.set_defaults(func=lambda args, ledger: print(render_markdown(ledger)))

    args = ap.parse_args(argv)
    ledger = load(args.issue)
    result = args.func(args, ledger)
    if isinstance(result, Finding):
        save(ledger)
        print(result.id)
    elif isinstance(result, FindingsLedger):
        save(result)
    else:
        save(ledger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
