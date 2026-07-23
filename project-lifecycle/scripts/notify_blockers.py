#!/usr/bin/env python3
"""Notify configured surfaces when BMAD blockers age past a threshold.

Default mode is dry-run. Apply mode currently supports a Plane comment alert,
which is enough for the lifecycle loop because Plane is the shared execution
surface. The script intentionally summarizes blockers and redacts secret-like
content before printing or posting.
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER = (
    PROJECT_ROOT
    / "_bmad_output"
    / "planning-artifacts"
    / "lifecycle-status-ledger.json"
)
ALERT_TAG = "[blocker-alert]"
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|pat|bearer)\s*[:=]\s*\S+"
)


@dataclass(frozen=True)
class BlockerAlert:
    story_id: str
    caf_id: str
    title: str
    owner: str
    blocked_since: date
    age_days: int
    missing_input: str
    requested_action: str

    def message(self) -> str:
        return (
            f"{ALERT_TAG} {self.caf_id} / {self.story_id}: {self.title} "
            f"has been blocked for {self.age_days} day(s). "
            f"Missing input: {self.missing_input}. "
            f"Requested action for {self.owner}: {self.requested_action}"
        )


def _load_reconcile_status() -> Any:
    path = Path(__file__).resolve().parent / "reconcile_status.py"
    spec = importlib.util.spec_from_file_location("reconcile_status", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def redact(text: object) -> str:
    value = str(text or "").strip()
    return SECRET_RE.sub(
        lambda match: (
            match.group(0).split(match.group(1), 1)[0]
            + match.group(1)
            + "=<redacted>"
        ),
        value,
    )


def plan_alerts(
    entries: list[dict[str, Any]],
    *,
    threshold_days: int,
    today: date | None = None,
) -> list[BlockerAlert]:
    today = today or date.today()
    alerts: list[BlockerAlert] = []
    for entry in entries:
        if entry.get("status") != "blocked":
            continue
        blocker = entry.get("blocker")
        if not isinstance(blocker, dict):
            continue
        try:
            blocked_since = date.fromisoformat(str(blocker.get("date", "")))
        except ValueError:
            continue
        age_days = (today - blocked_since).days
        if age_days < threshold_days:
            continue
        reason = blocker.get("reason", "")
        alerts.append(
            BlockerAlert(
                story_id=redact(entry.get("story_id")),
                caf_id=redact(entry.get("caf_id")),
                title=redact(entry.get("title")),
                owner=redact(blocker.get("owner")),
                blocked_since=blocked_since,
                age_days=age_days,
                missing_input=redact(blocker.get("missing_input") or reason),
                requested_action=redact(
                    blocker.get("requested_action")
                    or "Unblock this ticket or name the next owner/action."
                ),
            )
        )
    return alerts


def _plane_issue_by_sequence(module: Any, caf_id: str) -> tuple[Any, str, str, str, str, str]:
    base, workspace, project_id, api_key = module.resolve_config(PROJECT_ROOT)
    sequence_id = int(caf_id.removeprefix("CAF-"))
    issues = module.fetch_paginated(base, workspace, project_id, api_key, "issues/")
    for issue in issues:
        if issue.get("sequence_id") == sequence_id:
            return module, base, workspace, project_id, api_key, str(issue.get("id", ""))
    raise RuntimeError(f"No Plane issue found for {caf_id}")


def post_plane_alert(alert: BlockerAlert) -> str:
    module = _load_reconcile_status()
    module, base, workspace, project_id, api_key, issue_id = _plane_issue_by_sequence(
        module,
        alert.caf_id,
    )
    existing = module.fetch_paginated(
        base,
        workspace,
        project_id,
        api_key,
        f"issues/{issue_id}/comments/",
    )
    message = alert.message()
    existing_html = " ".join(str(item.get("comment_html", "")) for item in existing)
    if message in existing_html or html.escape(message) in existing_html:
        return "already-present"
    module.plane_request(
        "POST",
        module.plane_url(base, workspace, project_id, f"issues/{issue_id}/comments/"),
        api_key,
        {"comment_html": f"<p>{html.escape(message)}</p>"},
    )
    return "posted"


def _load_entries(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise RuntimeError("ledger root must be a list")
    return [item for item in payload if isinstance(item, dict)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--threshold-days", type=int, default=1)
    parser.add_argument(
        "--channel",
        choices=("dry-run", "plane-comment"),
        default="dry-run",
        help="Alert channel. dry-run prints sanitized messages only.",
    )
    parser.add_argument("--apply", action="store_true", help="Send the configured alert.")
    args = parser.parse_args(argv)

    if args.threshold_days < 0:
        print("error: --threshold-days must be >= 0", file=sys.stderr)
        return 1
    entries = _load_entries(args.ledger)
    alerts = plan_alerts(entries, threshold_days=args.threshold_days)
    if not alerts:
        print("no blocker alerts due")
        return 0

    for alert in alerts:
        message = alert.message()
        if not args.apply or args.channel == "dry-run":
            print(f"dry-run: {message}")
            continue
        if args.channel == "plane-comment":
            status = post_plane_alert(alert)
            print(f"{alert.caf_id}: Plane comment {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
