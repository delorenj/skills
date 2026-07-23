#!/usr/bin/env python3
"""Detect BMAD/Plane parity drift for lifecycle stories.

BMAD is requirements truth; Plane is status truth. This detector compares the
BMAD lifecycle epics artifact against the Plane project issues and reports:

- BMAD stories missing Plane issues (requirement drift -> update Plane);
- Plane lifecycle issues missing BMAD sources (requirement drift -> review,
  then backfill BMAD or cancel the Plane issue);
- title mismatches (requirement drift -> update Plane title);
- status mismatches (status drift -> update BMAD status);
- Plane-only status signals when BMAD carries no status marker for a story
  that Plane shows as started or closed (status drift -> record in BMAD).

The lifecycle BMAD artifact currently has no per-story status markers, so the
detector treats BMAD status as "unknown" unless a story body contains a line
such as `Status: in progress`. Unknown BMAD status is not drift by itself;
only Plane states beyond Backlog/Todo are surfaced as Plane-only signals.

Exit codes: 0 = no drift, 1 = drift found, 2 = error.

Read-only: live mode performs GET requests only and never prints the API key.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode


DEFAULT_ARTIFACT = "_bmad_output/planning-artifacts/project-lifecycle-workflow-stack-epics.md"
DEFAULT_PLANE_BASE = "https://plane.delo.sh"
DEFAULT_WORKSPACE = "automaticai"
DEFAULT_TITLE_PREFIX = "[Lifecycle] "
API_KEY_ENV_NAMES = ("PLANE_API_KEY", "PLANE_AUTOMATIAI_API_KEY")

STORY_RE = re.compile(r"^### (?P<id>PLC-E\d+-S\d+): (?P<title>.+)$", re.MULTILINE)
STORY_ID_RE = re.compile(r"PLC-E\d+-S\d+")
STATUS_LINE_RE = re.compile(r"^[-*]?\s*Status:\s*(?P<status>.+?)\s*$", re.IGNORECASE)
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

EXIT_NO_DRIFT = 0
EXIT_DRIFT = 1
EXIT_ERROR = 2

CATEGORY_REQUIREMENT = "requirement"
CATEGORY_STATUS = "status"

# Canonical status buckets shared by both sides.
PLANE_STATE_BUCKETS = {
    "backlog": "backlog",
    "todo": "todo",
    "in progress": "in_progress",
    "review": "review",
    "in review": "review",
    "done": "done",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}

BMAD_STATUS_BUCKETS = {
    "backlog": "backlog",
    "draft": "backlog",
    "planned": "backlog",
    "unvalidated": "backlog",
    "todo": "todo",
    "ready": "todo",
    "in progress": "in_progress",
    "in-progress": "in_progress",
    "doing": "in_progress",
    "started": "in_progress",
    "review": "review",
    "in review": "review",
    "code review": "review",
    "blocked": "blocked",
    "done": "done",
    "complete": "done",
    "completed": "done",
    "verified": "done",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "dropped": "cancelled",
}

# BMAD declared status bucket -> Plane buckets that count as aligned
# (from the parity reference "Status Alignment" section).
ACCEPTABLE_PLANE_BUCKETS = {
    "backlog": {"backlog", "todo"},
    "todo": {"todo"},
    "in_progress": {"in_progress"},
    "blocked": {"in_progress"},  # this Plane project has no Blocked state
    "review": {"review"},
    "done": {"done"},
    "cancelled": {"cancelled"},
}

# Plane buckets that are meaningful even when BMAD has no status marker.
# Backlog/Todo are consistent with "no status recorded yet" and are skipped.
PLANE_ONLY_SIGNAL_BUCKETS = {"in_progress", "review", "done", "cancelled"}


@dataclass(frozen=True)
class Story:
    story_id: str
    title: str
    status: str | None  # declared status text, None when absent (the norm today)


@dataclass(frozen=True)
class PlaneIssue:
    issue_id: str
    sequence_id: int | None
    name: str
    state_name: str | None

    @property
    def display_id(self) -> str:
        return f"CAF-{self.sequence_id}" if self.sequence_id is not None else (self.issue_id or self.name)


@dataclass(frozen=True)
class Finding:
    kind: str
    category: str  # requirement | status
    story_id: str | None
    plane_issue: str | None
    detail: str
    suggested_update: str


@dataclass
class DriftReport:
    mode: str
    artifact: str
    plane_scope: str
    stories_total: int = 0
    lifecycle_issues_total: int = 0
    matched: int = 0
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def requirement_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.category == CATEGORY_REQUIREMENT]

    @property
    def status_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.category == CATEGORY_STATUS]

    @property
    def has_drift(self) -> bool:
        return bool(self.findings)


# --------------------------------------------------------------------------
# BMAD parsing (same heading convention as sync_plane_from_bmad.py)
# --------------------------------------------------------------------------

def parse_stories(markdown: str) -> list[Story]:
    matches = list(STORY_RE.finditer(markdown))
    stories: list[Story] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[start:end]
        stories.append(
            Story(
                story_id=match.group("id"),
                title=match.group("title").strip(),
                status=parse_declared_status(body),
            )
        )
    return stories


def parse_declared_status(body: str) -> str | None:
    for line in body.splitlines():
        match = STATUS_LINE_RE.match(line.strip())
        if match:
            return match.group("status").strip()
    return None


# --------------------------------------------------------------------------
# Config and Plane API (live mode, read-only GETs, key never printed)
# --------------------------------------------------------------------------

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
        raise SystemExit("Missing Plane project_id in .plane.json")

    api_key = ""
    for name in API_KEY_ENV_NAMES:
        api_key = os.environ.get(name) or dotenv.get(name, "")
        if api_key:
            break
    if not api_key:
        raise SystemExit("Missing Plane API key. Set PLANE_API_KEY or PLANE_AUTOMATIAI_API_KEY.")

    return base, workspace, project_id, api_key


def plane_url(base: str, workspace: str, project_id: str, path: str, params: dict[str, str] | None = None) -> str:
    url = f"{base}/api/v1/workspaces/{workspace}/projects/{project_id}/{path.lstrip('/')}"
    if params:
        url += "?" + urlencode(params)
    return url


def http_get_json(url: str, api_key: str, timeout: int = 30) -> object:
    cmd = [
        "curl",
        "-fsS",
        "--max-time",
        str(timeout),
        "-H",
        f"X-API-Key: {api_key}",
        "-H",
        "Accept: application/json",
        url,
    ]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Plane GET failed for {url}: {exc}") from exc
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or f"curl exited {completed.returncode}").strip()
        raise RuntimeError(f"Plane GET failed for {url}: {message[:500]}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Plane GET returned invalid JSON for {url}: {exc}") from exc


def fetch_states(base: str, workspace: str, project_id: str, api_key: str) -> dict[str, str]:
    data = http_get_json(plane_url(base, workspace, project_id, "states/"), api_key)
    if isinstance(data, dict):
        items = data.get("results", [])
    elif isinstance(data, list):
        items = data
    else:
        raise RuntimeError("Unexpected Plane states response")
    return {str(item.get("id")): str(item.get("name", "")) for item in items if isinstance(item, dict)}


def fetch_issues(base: str, workspace: str, project_id: str, api_key: str) -> list[dict]:
    issues: list[dict] = []
    cursor: str | None = None
    while True:
        params = {"cursor": cursor} if cursor else None
        data = http_get_json(plane_url(base, workspace, project_id, "issues/", params), api_key)
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected Plane issue list response")
        issues.extend(item for item in data.get("results", []) if isinstance(item, dict))
        if not data.get("next_page_results"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return issues


# --------------------------------------------------------------------------
# Issue loading (shared by live and offline modes)
# --------------------------------------------------------------------------

def load_offline_payload(path: Path) -> tuple[list[dict], dict[str, str]]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data, {}
    if isinstance(data, dict):
        states = {
            str(item.get("id")): str(item.get("name", ""))
            for item in data.get("states", [])
            if isinstance(item, dict)
        }
        if isinstance(data.get("issues"), list):
            return data["issues"], states
        if isinstance(data.get("results"), list):
            return data["results"], states
    raise ValueError(f"Unrecognized issues JSON shape in {path}: expected a list, or a dict with 'issues' or 'results'.")


def build_issues(raw_issues: list[dict], state_names: dict[str, str]) -> list[PlaneIssue]:
    issues: list[PlaneIssue] = []
    for item in raw_issues:
        state_name: str | None = None
        if item.get("state_name"):
            state_name = str(item["state_name"])
        else:
            state_value = item.get("state")
            if state_value is not None:
                state_value = str(state_value)
                if state_value in state_names:
                    state_name = state_names[state_value]
                elif not UUID_RE.match(state_value):
                    state_name = state_value  # fixture used a plain name
        issues.append(
            PlaneIssue(
                issue_id=str(item.get("id", "")),
                sequence_id=item.get("sequence_id"),
                name=str(item.get("name", "")),
                state_name=state_name,
            )
        )
    return issues


# --------------------------------------------------------------------------
# Drift detection
# --------------------------------------------------------------------------

def normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def plane_bucket(state_name: str | None) -> str | None:
    if not state_name:
        return None
    return PLANE_STATE_BUCKETS.get(state_name.strip().casefold())


def bmad_bucket(status: str | None) -> str | None:
    if not status:
        return None
    return BMAD_STATUS_BUCKETS.get(status.strip().casefold())


def is_lifecycle_issue(issue: PlaneIssue, title_prefix: str) -> bool:
    return issue.name.startswith(title_prefix) or bool(STORY_ID_RE.search(issue.name))


def detect_drift(
    stories: list[Story],
    issues: list[PlaneIssue],
    title_prefix: str = DEFAULT_TITLE_PREFIX,
    include_plane_only_status: bool = True,
) -> tuple[list[Finding], list[str], int, int]:
    """Return (findings, notes, lifecycle_issue_count, matched_count)."""
    findings: list[Finding] = []
    notes: list[str] = []

    story_by_id = {story.story_id: story for story in stories}
    lifecycle_issues = [issue for issue in issues if is_lifecycle_issue(issue, title_prefix)]

    issues_by_story: dict[str, list[PlaneIssue]] = {}
    orphans: list[PlaneIssue] = []
    for issue in lifecycle_issues:
        match = STORY_ID_RE.search(issue.name)
        if match and match.group(0) in story_by_id:
            issues_by_story.setdefault(match.group(0), []).append(issue)
        else:
            orphans.append(issue)

    # 1. BMAD stories missing Plane issues (requirement drift; update Plane).
    for story in stories:
        if story.story_id not in issues_by_story:
            findings.append(
                Finding(
                    kind="missing_plane_issue",
                    category=CATEGORY_REQUIREMENT,
                    story_id=story.story_id,
                    plane_issue=None,
                    detail=f"BMAD story '{story.story_id}: {story.title}' has no Plane issue.",
                    suggested_update=(
                        "Update Plane: create the mirror issue "
                        "(sync_plane_from_bmad.py --create). BMAD is requirements truth."
                    ),
                )
            )

    # 2. Plane lifecycle issues missing BMAD sources (requirement drift).
    for issue in orphans:
        findings.append(
            Finding(
                kind="orphan_plane_issue",
                category=CATEGORY_REQUIREMENT,
                story_id=None,
                plane_issue=issue.display_id,
                detail=f"Plane issue {issue.display_id} '{issue.name}' has no BMAD source story.",
                suggested_update=(
                    "Review intent, then update the stale side: backfill the BMAD story if the "
                    "work is real, otherwise cancel the Plane issue. BMAD is requirements truth."
                ),
            )
        )

    matched = 0
    for story in stories:
        story_issues = issues_by_story.get(story.story_id, [])
        if not story_issues:
            continue
        matched += 1

        # Duplicate mirrors are requirement drift: Plane no longer mirrors 1:1.
        ordered = sorted(story_issues, key=lambda i: (i.sequence_id is None, i.sequence_id or 0))
        primary = ordered[0]
        for duplicate in ordered[1:]:
            findings.append(
                Finding(
                    kind="duplicate_plane_issue",
                    category=CATEGORY_REQUIREMENT,
                    story_id=story.story_id,
                    plane_issue=duplicate.display_id,
                    detail=(
                        f"Story {story.story_id} has multiple Plane issues "
                        f"({', '.join(i.display_id for i in ordered)}); expected exactly one."
                    ),
                    suggested_update="Update Plane: cancel the duplicate issue. BMAD is requirements truth.",
                )
            )

        # 3. Title mismatch (requirement drift; update Plane).
        expected_name = f"{title_prefix}{story.story_id}: {story.title}"
        if normalize_title(primary.name) != normalize_title(expected_name):
            findings.append(
                Finding(
                    kind="title_mismatch",
                    category=CATEGORY_REQUIREMENT,
                    story_id=story.story_id,
                    plane_issue=primary.display_id,
                    detail=(
                        f"Plane issue {primary.display_id} title '{primary.name}' "
                        f"!= expected '{expected_name}'."
                    ),
                    suggested_update="Update Plane: rename the issue to match BMAD. BMAD is requirements truth.",
                )
            )

        # 4. Status checks (status drift; update BMAD -- Plane is status truth).
        p_bucket = plane_bucket(primary.state_name)
        b_bucket = bmad_bucket(story.status)

        if primary.state_name is None:
            notes.append(f"{story.story_id}: Plane state unknown for {primary.display_id}; status check skipped.")
            continue
        if p_bucket is None:
            notes.append(
                f"{story.story_id}: unrecognized Plane state '{primary.state_name}' on {primary.display_id}; "
                "status check skipped."
            )
            continue

        if story.status is None:
            # BMAD carries no status marker (the norm today): status drift is a
            # Plane-only signal, raised only for states beyond Backlog/Todo.
            if include_plane_only_status and p_bucket in PLANE_ONLY_SIGNAL_BUCKETS:
                findings.append(
                    Finding(
                        kind="status_unknown_in_bmad",
                        category=CATEGORY_STATUS,
                        story_id=story.story_id,
                        plane_issue=primary.display_id,
                        detail=(
                            f"Plane shows {primary.display_id} as '{primary.state_name}' but the BMAD story "
                            "carries no status marker."
                        ),
                        suggested_update=(
                            "Update BMAD: record the story status (e.g. add 'Status: "
                            f"{primary.state_name.lower()}' to the story). Plane is status truth."
                        ),
                    )
                )
            continue

        if b_bucket is None:
            notes.append(
                f"{story.story_id}: unrecognized BMAD status '{story.status}'; status check skipped."
            )
            continue

        if p_bucket not in ACCEPTABLE_PLANE_BUCKETS.get(b_bucket, set()):
            findings.append(
                Finding(
                    kind="status_mismatch",
                    category=CATEGORY_STATUS,
                    story_id=story.story_id,
                    plane_issue=primary.display_id,
                    detail=(
                        f"BMAD declares status '{story.status}' but Plane issue {primary.display_id} "
                        f"is in state '{primary.state_name}'."
                    ),
                    suggested_update=(
                        "Update BMAD: align the story status with Plane. Plane is status truth. "
                        "If the Plane state itself is wrong, fix Plane and note why."
                    ),
                )
            )

    return findings, notes, len(lifecycle_issues), matched


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_text(report: DriftReport) -> str:
    lines = [
        "# BMAD/Plane Parity Drift Report",
        "",
        f"- Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- Mode: `{report.mode}`",
        f"- BMAD source: `{report.artifact}` (requirements truth)",
        f"- Plane scope: {report.plane_scope} (status truth)",
        f"- BMAD stories: {report.stories_total}",
        f"- Lifecycle Plane issues: {report.lifecycle_issues_total}",
        f"- Matched pairs: {report.matched}",
        f"- Requirement drift findings: {len(report.requirement_findings)}",
        f"- Status drift findings: {len(report.status_findings)}",
        "",
    ]

    if report.requirement_findings:
        lines += ["## Requirement Drift (BMAD is requirements truth)", ""]
        for f in report.requirement_findings:
            ref = f.story_id or f.plane_issue or "?"
            lines.append(f"- [{f.kind}] {ref}: {f.detail}")
            lines.append(f"  - Suggested update: {f.suggested_update}")
        lines.append("")

    if report.status_findings:
        lines += ["## Status Drift (Plane is status truth)", ""]
        for f in report.status_findings:
            ref = f.story_id or f.plane_issue or "?"
            lines.append(f"- [{f.kind}] {ref}: {f.detail}")
            lines.append(f"  - Suggested update: {f.suggested_update}")
        lines.append("")

    if report.notes:
        lines += ["## Notes (informational, not drift)", ""]
        lines += [f"- {note}" for note in report.notes]
        lines.append("")

    verdict = f"DRIFT ({len(report.findings)} finding(s))" if report.has_drift else "NO DRIFT"
    lines.append(f"RESULT: {verdict}")
    return "\n".join(lines)


def render_json(report: DriftReport) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": report.mode,
        "bmad_source": report.artifact,
        "plane_scope": report.plane_scope,
        "truth": {"requirements": "bmad", "status": "plane"},
        "counts": {
            "stories": report.stories_total,
            "lifecycle_issues": report.lifecycle_issues_total,
            "matched": report.matched,
            "requirement_drift": len(report.requirement_findings),
            "status_drift": len(report.status_findings),
        },
        "findings": [
            {
                "kind": f.kind,
                "category": f.category,
                "story_id": f.story_id,
                "plane_issue": f.plane_issue,
                "detail": f.detail,
                "suggested_update": f.suggested_update,
            }
            for f in report.findings
        ],
        "notes": report.notes,
        "drift": report.has_drift,
    }
    return json.dumps(payload, indent=2)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    artifact_path = Path(args.artifact)
    if not artifact_path.exists():
        print(f"error: BMAD artifact not found: {artifact_path}", file=sys.stderr)
        return EXIT_ERROR

    stories = parse_stories(artifact_path.read_text())
    if not stories:
        print(f"error: no PLC stories found in {artifact_path}", file=sys.stderr)
        return EXIT_ERROR

    if args.issues_json:
        issues_path = Path(args.issues_json)
        if not issues_path.exists():
            print(f"error: issues JSON not found: {issues_path}", file=sys.stderr)
            return EXIT_ERROR
        try:
            raw_issues, state_names = load_offline_payload(issues_path)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_ERROR
        issues = build_issues(raw_issues, state_names)
        mode = "offline"
        plane_scope = f"`{issues_path}`"
    else:
        try:
            base, workspace, project_id, api_key = resolve_config(Path.cwd())
            state_names = fetch_states(base, workspace, project_id, api_key)
            raw_issues = fetch_issues(base, workspace, project_id, api_key)
        except (SystemExit, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_ERROR
        issues = build_issues(raw_issues, state_names)
        mode = "live"
        plane_scope = f"workspace `{workspace}`, project `{project_id}`"

    findings, notes, lifecycle_total, matched = detect_drift(
        stories,
        issues,
        title_prefix=args.title_prefix,
        include_plane_only_status=not args.ignore_plane_only_status,
    )

    report = DriftReport(
        mode=mode,
        artifact=str(artifact_path),
        plane_scope=plane_scope,
        stories_total=len(stories),
        lifecycle_issues_total=lifecycle_total,
        matched=matched,
        findings=findings,
        notes=notes,
    )

    print(render_json(report) if args.format == "json" else render_text(report))
    return EXIT_DRIFT if report.has_drift else EXIT_NO_DRIFT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--artifact", default=DEFAULT_ARTIFACT, help="BMAD epics artifact path.")
    parser.add_argument(
        "--issues-json",
        default=None,
        help="Offline mode: path to saved Plane issues JSON (a list, or a dict with 'issues'/'results' and optional 'states').",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--title-prefix", default=DEFAULT_TITLE_PREFIX)
    parser.add_argument(
        "--ignore-plane-only-status",
        action="store_true",
        help="Suppress status findings for stories whose BMAD body has no status marker.",
    )
    args = parser.parse_args(argv)

    try:
        return run(args)
    except Exception as exc:  # noqa: BLE001 - top-level guard maps errors to exit 2
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
