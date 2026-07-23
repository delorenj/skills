#!/usr/bin/env python3
"""Reconcile the lifecycle status ledger with Plane issue states.

BMAD remains the source of truth for requirements. Execution status lives in
`_bmad_output/planning-artifacts/lifecycle-status-ledger.json`; this helper
validates that ledger and mirrors it into Plane. Default mode is a dry run
that prints intended changes. `--apply` PATCHes Plane issue states and posts
blocker / PR-link comments. See
`skills/project-lifecycle/references/status-reconciliation.md`.

Exit codes: 0 valid/clean, 1 validation errors, 2 runtime errors.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

DEFAULT_LEDGER = "_bmad_output/planning-artifacts/lifecycle-status-ledger.json"
DEFAULT_PLANE_BASE = "https://plane.delo.sh"
DEFAULT_WORKSPACE = "automaticai"
API_KEY_ENV_NAMES = ("PLANE_API_KEY", "PLANE_AUTOMATIAI_API_KEY")

STORY_ID_RE = re.compile(r"^PLC-E\d+-S\d+$")
CAF_ID_RE = re.compile(r"^CAF-(\d+)$")

# Ledger status -> Plane state name. Plane has no native Blocked state, so
# blocked maps to In Progress plus a blocker comment (the ledger entry is the
# authoritative blocked record).
STATUS_TO_PLANE_STATE = {
    "backlog": "Backlog",
    "todo": "Todo",
    "in-progress": "In Progress",
    "blocked": "In Progress",
    "review": "Review",
    "done": "Done",
}
KNOWN_ENTRY_KEYS = {
    "story_id",
    "caf_id",
    "status",
    "blocker",
    "pr_links",
    "ac_verified",
    "updated",
    "title",  # optional, readability only
}
BLOCKED_COMMENT_TAG = "[blocked]"
PR_LINKS_COMMENT_TAG = "[pr-links]"


@dataclass(frozen=True)
class PlannedChange:
    story_id: str
    caf_id: str
    ledger_status: str
    plane_state: str
    comments: tuple[str, ...] = ()


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_nonempty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_iso_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_iso_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    for parser in (date.fromisoformat, datetime.fromisoformat):
        try:
            parser(value)
        except ValueError:
            continue
        return True
    return False


def validate_entry(entry: object, index: int) -> ValidationResult:
    result = ValidationResult()
    label = f"entry[{index}]"
    if not isinstance(entry, dict):
        result.errors.append(f"{label}: must be an object")
        return result

    story_id = entry.get("story_id")
    if _is_nonempty_str(story_id):
        label = str(story_id)
        if not STORY_ID_RE.match(str(story_id)):
            result.errors.append(f"{label}: story_id must match PLC-E<n>-S<n>")
    else:
        result.errors.append(f"{label}: missing story_id")

    caf_id = entry.get("caf_id")
    if not (_is_nonempty_str(caf_id) and CAF_ID_RE.match(str(caf_id))):
        result.errors.append(f"{label}: caf_id must match CAF-<number>")

    status = entry.get("status")
    if status not in STATUS_TO_PLANE_STATE:
        allowed = ", ".join(sorted(STATUS_TO_PLANE_STATE))
        result.errors.append(f"{label}: status {status!r} not one of: {allowed}")

    blocker = entry.get("blocker")
    if status == "blocked":
        if not isinstance(blocker, dict):
            result.errors.append(f"{label}: blocked status requires a blocker object with reason, owner, date")
        else:
            for key in ("reason", "owner"):
                if not _is_nonempty_str(blocker.get(key)):
                    result.errors.append(f"{label}: blocker.{key} is required and must be non-empty")
            if not _is_iso_date(blocker.get("date")):
                result.errors.append(f"{label}: blocker.date is required and must be an ISO date (YYYY-MM-DD)")
    elif blocker is not None:
        if isinstance(blocker, dict):
            result.warnings.append(f"{label}: blocker set but status is {status!r}; clear it once unblocked")
        else:
            result.errors.append(f"{label}: blocker must be an object or null")

    pr_links = entry.get("pr_links")
    if not isinstance(pr_links, list) or not all(_is_nonempty_str(link) for link in pr_links):
        result.errors.append(f"{label}: pr_links must be a list of non-empty strings")

    ac_verified = entry.get("ac_verified")
    if status == "done":
        if not isinstance(ac_verified, dict):
            result.errors.append(f"{label}: done status requires ac_verified with verified=true and evidence")
        else:
            if ac_verified.get("verified") is not True:
                result.errors.append(f"{label}: done status requires ac_verified.verified to be true")
            if not _is_nonempty_str(ac_verified.get("evidence")):
                result.errors.append(f"{label}: done status requires non-empty ac_verified.evidence")
    elif ac_verified is not None:
        if not isinstance(ac_verified, dict):
            result.errors.append(f"{label}: ac_verified must be an object or null")
        elif ac_verified.get("verified") is True and not _is_nonempty_str(ac_verified.get("evidence")):
            result.errors.append(f"{label}: ac_verified.verified=true requires non-empty evidence")

    if not _is_iso_timestamp(entry.get("updated")):
        result.errors.append(f"{label}: updated must be an ISO date or datetime string")

    unknown = sorted(set(entry) - KNOWN_ENTRY_KEYS)
    if unknown:
        result.warnings.append(f"{label}: unknown keys ignored: {', '.join(unknown)}")
    return result


def validate_ledger(entries: object) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(entries, list):
        result.errors.append("ledger root must be a JSON array of story entries")
        return result

    seen: dict[str, set[str]] = {"story_id": set(), "caf_id": set()}
    for index, entry in enumerate(entries):
        entry_result = validate_entry(entry, index)
        result.errors.extend(entry_result.errors)
        result.warnings.extend(entry_result.warnings)
        if isinstance(entry, dict):
            for key, values in seen.items():
                value = entry.get(key)
                if _is_nonempty_str(value):
                    if value in values:
                        result.errors.append(f"duplicate {key}: {value}")
                    values.add(str(value))
    return result


def blocker_comment(blocker: dict[str, object]) -> str:
    return (
        f"{BLOCKED_COMMENT_TAG} {blocker.get('reason')} | "
        f"owner: {blocker.get('owner')} | since: {blocker.get('date')}"
    )


def pr_links_comment(pr_links: list[str]) -> str:
    return f"{PR_LINKS_COMMENT_TAG} " + " ".join(pr_links)


def plan_changes(entries: list[dict[str, object]]) -> list[PlannedChange]:
    planned: list[PlannedChange] = []
    for entry in entries:
        status = str(entry["status"])
        comments: list[str] = []
        if status == "blocked":
            comments.append(blocker_comment(entry["blocker"]))  # type: ignore[arg-type]
        pr_links = [str(link) for link in entry.get("pr_links", [])]
        if pr_links:
            comments.append(pr_links_comment(pr_links))
        planned.append(
            PlannedChange(
                story_id=str(entry["story_id"]),
                caf_id=str(entry["caf_id"]),
                ledger_status=status,
                plane_state=STATUS_TO_PLANE_STATE[status],
                comments=tuple(comments),
            )
        )
    return planned


def print_plan(planned: list[PlannedChange]) -> None:
    for change in planned:
        print(f"{change.caf_id} ({change.story_id}): {change.ledger_status} -> Plane state '{change.plane_state}'")
        for comment in change.comments:
            print(f"  comment: {comment}")


# --- Plane API (apply mode only) -------------------------------------------


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_config(project_root: Path) -> tuple[str, str, str, str]:
    dotenv = load_dotenv(project_root / ".env")
    plane_config_path = project_root / ".plane.json"
    plane_config = json.loads(plane_config_path.read_text()) if plane_config_path.exists() else {}

    base = (dotenv.get("PLANE_BASE") or DEFAULT_PLANE_BASE).rstrip("/")
    workspace = plane_config.get("workspace") or DEFAULT_WORKSPACE
    project_id = plane_config.get("project_id")
    if not project_id:
        raise RuntimeError("Missing Plane project_id in .plane.json")

    api_key = ""
    for name in API_KEY_ENV_NAMES:
        api_key = os.environ.get(name) or dotenv.get(name, "")
        if api_key:
            break
    if not api_key:
        raise RuntimeError("Missing Plane API key. Set PLANE_API_KEY or PLANE_AUTOMATIAI_API_KEY.")
    return base, workspace, project_id, api_key


def plane_request(method: str, url: str, api_key: str, payload: dict[str, object] | None = None) -> object:
    cmd = [
        "curl",
        "-fsS",
        "--max-time",
        "30",
        "-X",
        method,
        "-H",
        f"X-API-Key: {api_key}",
        "-H",
        "Accept: application/json",
    ]
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "--data", json.dumps(payload)])
    cmd.append(url)
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=35, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Plane API {method} {url} failed: {exc}") from None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or f"curl exited {completed.returncode}").strip()[:500]
        raise RuntimeError(f"Plane API {method} {url} failed: {detail}") from None
    body = completed.stdout
    if not body.strip():
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Plane API {method} {url} returned invalid JSON: {exc}") from None


def plane_url(base: str, workspace: str, project_id: str, path: str) -> str:
    return f"{base}/api/v1/workspaces/{workspace}/projects/{project_id}/{path.lstrip('/')}"


def fetch_paginated(base: str, workspace: str, project_id: str, api_key: str, path: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    cursor: str | None = None
    while True:
        url = plane_url(base, workspace, project_id, path)
        if cursor:
            url += f"?cursor={cursor}"
        data = plane_request("GET", url, api_key)
        if isinstance(data, list):
            items.extend(item for item in data if isinstance(item, dict))
            return items
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected Plane response for {path}")
        items.extend(item for item in data.get("results", []) if isinstance(item, dict))
        if not data.get("next_page_results"):
            return items
        cursor = data.get("next_cursor")
        if not cursor:
            return items


def apply_changes(planned: list[PlannedChange], project_root: Path) -> None:
    base, workspace, project_id, api_key = resolve_config(project_root)

    states = fetch_paginated(base, workspace, project_id, api_key, "states/")
    state_ids = {str(state.get("name", "")): str(state.get("id", "")) for state in states}

    issues = fetch_paginated(base, workspace, project_id, api_key, "issues/")
    by_sequence: dict[int, dict[str, object]] = {}
    for issue in issues:
        sequence_id = issue.get("sequence_id")
        if isinstance(sequence_id, int):
            by_sequence[sequence_id] = issue

    for change in planned:
        sequence_id = int(CAF_ID_RE.match(change.caf_id).group(1))  # validated earlier
        issue = by_sequence.get(sequence_id)
        if issue is None:
            raise RuntimeError(f"No Plane issue found for {change.caf_id}")
        issue_id = str(issue.get("id", ""))
        target_state_id = state_ids.get(change.plane_state)
        if not target_state_id:
            raise RuntimeError(f"Plane state '{change.plane_state}' not found in project")

        if str(issue.get("state", "")) == target_state_id:
            print(f"{change.caf_id}: already in '{change.plane_state}', skipping PATCH")
        else:
            plane_request(
                "PATCH",
                plane_url(base, workspace, project_id, f"issues/{issue_id}/"),
                api_key,
                {"state": target_state_id},
            )
            print(f"{change.caf_id}: state set to '{change.plane_state}'")

        if change.comments:
            existing = fetch_paginated(base, workspace, project_id, api_key, f"issues/{issue_id}/comments/")
            existing_html = " ".join(str(item.get("comment_html", "")) for item in existing)
            for comment in change.comments:
                escaped = html.escape(comment)
                if escaped in existing_html or comment in existing_html:
                    print(f"{change.caf_id}: comment already present, skipping: {comment}")
                    continue
                plane_request(
                    "POST",
                    plane_url(base, workspace, project_id, f"issues/{issue_id}/comments/"),
                    api_key,
                    {"comment_html": f"<p>{escaped}</p>"},
                )
                print(f"{change.caf_id}: comment posted: {comment}")


# --- Entry point ------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ledger", default=DEFAULT_LEDGER, help="Path to the status ledger JSON file.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="PATCH Plane issue states and post blocker/PR-link comments. Default is dry-run.",
    )
    args = parser.parse_args(argv)

    ledger_path = Path(args.ledger)
    try:
        entries = json.loads(ledger_path.read_text())
    except OSError as exc:
        print(f"runtime error: cannot read ledger {ledger_path}: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"runtime error: ledger {ledger_path} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    result = validate_ledger(entries)
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if result.errors:
        for error_message in result.errors:
            print(f"validation error: {error_message}", file=sys.stderr)
        print(f"ledger invalid: {len(result.errors)} error(s)", file=sys.stderr)
        return 1

    planned = plan_changes(entries)
    if args.apply:
        try:
            apply_changes(planned, Path.cwd())
        except RuntimeError as exc:
            print(f"runtime error: {exc}", file=sys.stderr)
            return 2
        print(f"applied: {len(planned)} entries reconciled")
        return 0

    print(f"dry-run: {len(planned)} entries valid; intended Plane changes:")
    print_plan(planned)
    print("dry-run complete; re-run with --apply to write to Plane")
    return 0


if __name__ == "__main__":
    sys.exit(main())
