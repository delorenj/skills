#!/usr/bin/env python3
"""Mirror BMAD story headings into Plane issues.

BMAD remains the source of truth. This helper creates concise Plane issues
that point back to the authoritative BMAD artifact and writes a mirror report.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode


DEFAULT_ARTIFACT = "_bmad_output/planning-artifacts/project-lifecycle-workflow-stack-epics.md"
DEFAULT_REPORT = "_bmad_output/planning-artifacts/project-lifecycle-plane-mirror-report.md"
DEFAULT_PLANE_BASE = "https://plane.delo.sh"
DEFAULT_WORKSPACE = "automaticai"
API_KEY_ENV_NAMES = ("PLANE_API_KEY", "PLANE_AUTOMATIAI_API_KEY")
STORY_RE = re.compile(r"^### (?P<id>PLC-E\d+-S\d+): (?P<title>.+)$", re.MULTILINE)


@dataclass(frozen=True)
class Story:
    story_id: str
    title: str
    summary: str
    acceptance_criteria: list[str]


@dataclass(frozen=True)
class PlaneIssue:
    issue_id: str
    sequence_id: int | None
    name: str

    @property
    def display_id(self) -> str:
        return f"CAF-{self.sequence_id}" if self.sequence_id is not None else self.issue_id


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


def parse_stories(markdown: str) -> list[Story]:
    matches = list(STORY_RE.finditer(markdown))
    stories: list[Story] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        story_id = match.group("id")
        title = match.group("title").strip()
        stories.append(
            Story(
                story_id=story_id,
                title=title,
                summary=parse_summary(body),
                acceptance_criteria=parse_acceptance_criteria(body),
            )
        )
    return stories


def parse_summary(body: str) -> str:
    for line in body.splitlines():
        text = line.strip()
        if not text or text == "Acceptance criteria:":
            continue
        if text.startswith("- "):
            continue
        return text
    return "See BMAD story for execution context."


def parse_acceptance_criteria(body: str) -> list[str]:
    lines = body.splitlines()
    criteria: list[str] = []
    in_ac = False
    for line in lines:
        text = line.strip()
        if text == "Acceptance criteria:":
            in_ac = True
            continue
        if in_ac and text.startswith("##"):
            break
        if in_ac and text.startswith("- "):
            criteria.append(text[2:].strip())
    return criteria


def plane_url(base: str, workspace: str, project_id: str, path: str, params: dict[str, str] | None = None) -> str:
    url = f"{base}/api/v1/workspaces/{workspace}/projects/{project_id}/{path.lstrip('/')}"
    if params:
        url += "?" + urlencode(params)
    return url


def run_curl(method: str, url: str, api_key: str, payload: dict[str, object] | None = None) -> object:
    args = [
        "curl",
        "-sS",
        "-L",
        "--fail-with-body",
        "-X",
        method,
        "-H",
        f"X-API-Key: {api_key}",
        "-H",
        "Accept: application/json",
    ]
    input_text = None
    if payload is not None:
        args += ["-H", "Content-Type: application/json", "-d", "@-"]
        input_text = json.dumps(payload)
    args.append(url)

    result = subprocess.run(args, input=input_text, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        body = result.stdout.strip()
        error = result.stderr.strip()
        message = body or error or f"curl exited {result.returncode}"
        raise RuntimeError(message[:1200])
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def list_issues(base: str, workspace: str, project_id: str, api_key: str) -> list[PlaneIssue]:
    issues: list[PlaneIssue] = []
    cursor: str | None = None
    while True:
        params = {"cursor": cursor} if cursor else None
        data = run_curl("GET", plane_url(base, workspace, project_id, "issues/", params), api_key)
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected Plane issue list response")
        for item in data.get("results", []):
            issues.append(
                PlaneIssue(
                    issue_id=str(item.get("id", "")),
                    sequence_id=item.get("sequence_id"),
                    name=str(item.get("name", "")),
                )
            )
        if not data.get("next_page_results"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return issues


def issue_description(story: Story, artifact_path: Path) -> str:
    criteria = story.acceptance_criteria[:5] or ["See BMAD story for authoritative acceptance criteria."]
    items = "".join(f"<li>{html.escape(item)}</li>" for item in criteria)
    source = html.escape(str(artifact_path))
    story_id = html.escape(story.story_id)
    summary = html.escape(story.summary)
    return (
        "<div>"
        f"<p><strong>BMAD source:</strong> <code>{source}</code></p>"
        f"<p><strong>BMAD story:</strong> <code>{story_id}</code></p>"
        f"<p><strong>Summary:</strong> {summary}</p>"
        "<h3>Acceptance criteria highlights</h3>"
        f"<ul>{items}</ul>"
        "<h3>Dependencies</h3>"
        "<p>See the BMAD story and nearby epic order before implementation.</p>"
        "<h3>Validation</h3>"
        "<p>Verify the story acceptance criteria, then update BMAD and Plane status together.</p>"
        "</div>"
    )


def create_issue(
    base: str,
    workspace: str,
    project_id: str,
    api_key: str,
    story: Story,
    title_prefix: str,
    priority: str,
    artifact_path: Path,
) -> PlaneIssue:
    payload = {
        "name": f"{title_prefix}{story.story_id}: {story.title}",
        "description_html": issue_description(story, artifact_path),
        "priority": priority,
    }
    data = run_curl("POST", plane_url(base, workspace, project_id, "issues/"), api_key, payload)
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected Plane issue create response")
    return PlaneIssue(
        issue_id=str(data.get("id", "")),
        sequence_id=data.get("sequence_id"),
        name=str(data.get("name", payload["name"])),
    )


def write_report(
    report_path: Path,
    artifact_path: Path,
    workspace: str,
    project_id: str,
    created: list[tuple[Story, PlaneIssue]],
    existing: list[tuple[Story, PlaneIssue]],
    would_create: list[Story],
    mode: str,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Project Lifecycle Plane Mirror Report",
        "",
        f"- Generated at: {now}",
        f"- Mode: `{mode}`",
        f"- BMAD source: `{artifact_path}`",
        f"- Plane workspace: `{workspace}`",
        f"- Plane project id: `{project_id}`",
        f"- Created: {len(created)}",
        f"- Existing/skipped: {len(existing)}",
        f"- Would create: {len(would_create)}",
        "",
    ]

    if created:
        lines += ["## Created", ""]
        for story, issue in created:
            issue_url = f"https://plane.delo.sh/{workspace}/projects/{project_id}/issues/{issue.issue_id}"
            lines.append(f"- {story.story_id}: {story.title} -> [{issue.display_id}]({issue_url})")
        lines.append("")

    if would_create:
        lines += ["## Dry-Run Would Create", ""]
        for story in would_create:
            lines.append(f"- {story.story_id}: {story.title}")
        lines.append("")

    if existing:
        lines += ["## Existing Or Skipped", ""]
        for story, issue in existing:
            issue_url = f"https://plane.delo.sh/{workspace}/projects/{project_id}/issues/{issue.issue_id}"
            lines.append(f"- {story.story_id}: {story.title} -> [{issue.display_id}]({issue_url})")
        lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument("--create", action="store_true", help="Create missing Plane issues. Default is dry-run.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of stories processed.")
    parser.add_argument("--title-prefix", default="[Lifecycle] ")
    parser.add_argument("--priority", default="medium")
    args = parser.parse_args()

    project_root = Path.cwd()
    artifact_path = Path(args.artifact)
    report_path = Path(args.report)
    markdown = artifact_path.read_text()
    stories = parse_stories(markdown)
    if args.limit:
        stories = stories[: args.limit]
    if not stories:
        raise SystemExit(f"No PLC stories found in {artifact_path}")

    base, workspace, project_id, api_key = resolve_config(project_root)
    existing_issues = list_issues(base, workspace, project_id, api_key)
    existing_by_story: dict[str, PlaneIssue] = {}
    for issue in existing_issues:
        for story in stories:
            if story.story_id in issue.name:
                existing_by_story[story.story_id] = issue

    created: list[tuple[Story, PlaneIssue]] = []
    existing: list[tuple[Story, PlaneIssue]] = []
    would_create: list[Story] = []

    for story in stories:
        if story.story_id in existing_by_story:
            existing.append((story, existing_by_story[story.story_id]))
            continue
        if not args.create:
            would_create.append(story)
            continue
        issue = create_issue(base, workspace, project_id, api_key, story, args.title_prefix, args.priority, artifact_path)
        created.append((story, issue))

    mode = "create" if args.create else "dry-run"
    write_report(report_path, artifact_path, workspace, project_id, created, existing, would_create, mode)
    print(f"stories={len(stories)} existing={len(existing)} created={len(created)} would_create={len(would_create)}")
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
