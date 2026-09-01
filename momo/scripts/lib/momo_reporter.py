"""momo_reporter — disciplined, deduplicated board reporting (33GPM-5).

Posts one comment per event, each containing delta + current state + asks only.
Post-mortems/decisions go to the Bloodbank decision trail (record-decision.py) with
a link; the reporter only posts the delta summary. Deduplication is enforced by a
local store keyed on a content hash so repeated identical states do not spam the board.

Design pattern: Command — ReportCommand encapsulates one board comment and its execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORTS_DIR = Path("_bmad-output/implementation-artifacts/reports")

_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB))

from momo_handback import repo_root  # type: ignore[import]  # noqa: E402


class ReporterError(Exception):
    pass


@dataclass
class ReportCommand:
    issue: str
    event: str  # e.g. "status", "decision", "review", "handback"
    delta: str
    state: str
    asks: str = ""
    actor: str = "momo"
    link: str = ""  # link to decision trail or evidence
    posted_at: str = field(default_factory=lambda: _now_iso())

    def body(self) -> str:
        parts = [
            f"**{self.actor}** · `{self.event}` · {self.posted_at}",
            "",
            f"**State:** {self.state}",
            "",
            "**Delta:**",
            self.delta,
        ]
        if self.asks:
            parts += ["", "**Asks:**", self.asks]
        if self.link:
            parts += ["", f"**Trail:** {self.link}"]
        return "\n".join(parts)

    def content_hash(self) -> str:
        return hashlib.sha256(self.body().encode("utf-8")).hexdigest()[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root(start: Path | None = None) -> Path:
    return repo_root(start or os.getcwd())


def reports_path(issue: str, root: Path | None = None) -> Path:
    return _repo_root(root) / REPORTS_DIR / f"{issue}.comments.json"


def load_log(issue: str, root: Path | None = None) -> dict[str, Any]:
    p = reports_path(issue, root)
    if not p.is_file():
        return {"schema_version": "1.0", "issue": issue, "comments": []}
    return json.loads(p.read_text())


def save_log(log: dict[str, Any], issue: str, root: Path | None = None) -> Path:
    p = reports_path(issue, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".comments-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(log, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    return p


def already_posted(cmd: ReportCommand, root: Path | None = None) -> bool:
    log = load_log(cmd.issue, root)
    h = cmd.content_hash()
    return any(c.get("hash") == h for c in log.get("comments", []))


def post(cmd: ReportCommand, *, board: str = "momo-board.sh", dry_run: bool = False, root: Path | None = None) -> dict[str, Any]:
    """Post a comment through momo-board.sh if not already posted."""
    r = _repo_root(root)
    log = load_log(cmd.issue, r)
    h = cmd.content_hash()
    if any(c.get("hash") == h for c in log.get("comments", [])):
        return {"skipped": True, "hash": h, "reason": "already posted"}

    body = cmd.body()
    if dry_run:
        return {"skipped": True, "hash": h, "body": body, "reason": "dry_run"}

    script = r / "momo" / "skill" / "scripts" / board
    if not script.is_file():
        script = r / "agents" / "hermes" / "pm" / ".scripts" / board
    if not script.is_file():
        raise ReporterError(f"board adapter not found: {board}")

    try:
        result = subprocess.run(
            [str(script), "comment", cmd.issue, body],
            cwd=r, capture_output=True, text=True, timeout=60,
        )
    except Exception as exc:
        raise ReporterError(f"board adapter failed: {exc}") from exc

    if result.returncode != 0:
        raise ReporterError(f"board adapter exit {result.returncode}: {result.stderr}")

    comment_id = result.stdout.strip().splitlines()[-1].strip() if result.stdout.strip() else ""
    entry = {
        "hash": h,
        "event": cmd.event,
        "posted_at": cmd.posted_at,
        "comment_id": comment_id,
        "state": cmd.state,
    }
    log["comments"].append(entry)
    save_log(log, cmd.issue, r)
    return {"posted": True, "hash": h, "comment_id": comment_id}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Momo deduplicated board reporter")
    ap.add_argument("--issue", required=True)
    ap.add_argument("--event", required=True)
    ap.add_argument("--delta", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--asks", default="")
    ap.add_argument("--link", default="")
    ap.add_argument("--actor", default="momo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--board", default="momo-board.sh")
    args = ap.parse_args(argv)

    cmd = ReportCommand(
        issue=args.issue,
        event=args.event,
        delta=args.delta,
        state=args.state,
        asks=args.asks,
        actor=args.actor,
        link=args.link,
    )
    try:
        result = post(cmd, board=args.board, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        return 0
    except ReporterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
