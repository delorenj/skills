#!/usr/bin/env python3
"""Choose the next lifecycle ticket from BMAD stories, status, and dependencies.

BMAD is the requirements source. The lifecycle status ledger is execution state.
This helper builds a dependency graph for CAF-114..CAF-139, reports the optimal
implementation order, and selects the next unblocked ticket.

Default mode is read-only. It writes a markdown report only when `--write-report`
is supplied.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ARTIFACT = "_bmad_output/planning-artifacts/project-lifecycle-workflow-stack-epics.md"
DEFAULT_LEDGER = "_bmad_output/planning-artifacts/lifecycle-status-ledger.json"
DEFAULT_REPORT = "_bmad_output/planning-artifacts/lifecycle-next-ticket-triage-report.md"
STORY_RE = re.compile(r"^### (?P<id>PLC-E\d+-S\d+): (?P<title>.+)$", re.MULTILINE)
CAF_RE = re.compile(r"CAF-(\d+)")

ACTIVE_STATUSES = {"todo", "in-progress", "review"}
DONE_STATUSES = {"done"}
BLOCKED_STATUSES = {"blocked"}
AVAILABLE_STATUSES = {"backlog", "todo", "in-progress"}

# Domain dependency graph. Keep this explicit; this is the project rail that
# prevents agent/router/runtime work from outrunning the workflow/MCP foundation.
DEPENDENCIES: dict[str, set[str]] = {
    "PLC-E1-S1": set(),
    "PLC-E1-S2": {"PLC-E1-S1"},
    "PLC-E1-S3": {"PLC-E1-S1", "PLC-E1-S2"},
    "PLC-E2-S1": {"PLC-E1-S2", "PLC-E1-S3"},
    "PLC-E2-S2": {"PLC-E2-S1"},
    "PLC-E2-S3": {"PLC-E2-S2"},
    "PLC-E2-S4": {"PLC-E2-S3"},
    "PLC-E2-S5": {"PLC-E2-S3", "PLC-E2-S4"},
    "PLC-E3-S1": {"PLC-E2-S5"},
    "PLC-E3-S2": {"PLC-E3-S1"},
    "PLC-E3-S3": {"PLC-E3-S1", "PLC-E3-S2"},
    "PLC-E3-S4": {"PLC-E3-S2", "PLC-E3-S3"},
    "PLC-E3-S5": {"PLC-E3-S2", "PLC-E5-S2", "PLC-E5-S3"},
    "PLC-E4-S1": {"PLC-E3-S2"},
    "PLC-E4-S2": {"PLC-E4-S1", "PLC-E5-S1", "PLC-E5-S2"},
    "PLC-E4-S3": {"PLC-E4-S1", "PLC-E4-S2", "PLC-E5-S2", "PLC-E5-S3"},
    "PLC-E4-S4": {"PLC-E4-S1"},
    "PLC-E5-S1": {"PLC-E3-S2"},
    "PLC-E5-S2": {"PLC-E3-S2", "PLC-E5-S1"},
    "PLC-E5-S3": {"PLC-E3-S2"},
    "PLC-E5-S4": {"PLC-E5-S2", "PLC-E5-S3"},
    "PLC-E5-S5": {"PLC-E4-S1", "PLC-E5-S2"},
    "PLC-E6-S1": {"PLC-E2-S5"},
    "PLC-E6-S2": {"PLC-E2-S2", "PLC-E2-S4"},
    "PLC-E6-S3": {"PLC-E2-S5"},
    "PLC-E6-S4": {"PLC-E2-S3", "PLC-E2-S4", "PLC-E2-S5"},
}

# Prefer operating rails before runtime features when several tickets are ready.
PRIORITY: dict[str, int] = {
    "PLC-E2-S3": 10,
    "PLC-E2-S4": 20,
    "PLC-E2-S5": 30,
    "PLC-E6-S2": 40,
    "PLC-E6-S4": 50,
    "PLC-E3-S1": 60,
    "PLC-E3-S2": 70,
    "PLC-E5-S3": 80,
    "PLC-E5-S1": 90,
    "PLC-E5-S2": 100,
    "PLC-E5-S4": 110,
    "PLC-E4-S1": 120,
    "PLC-E4-S2": 130,
    "PLC-E4-S4": 140,
    "PLC-E4-S3": 150,
    "PLC-E3-S3": 160,
    "PLC-E3-S4": 170,
    "PLC-E3-S5": 180,
    "PLC-E5-S5": 190,
    "PLC-E6-S1": 200,
    "PLC-E6-S3": 210,
}


@dataclass(frozen=True)
class Story:
    story_id: str
    title: str
    caf_id: str
    status: str = "backlog"
    blocker: str | None = None
    pr_links: tuple[str, ...] = ()
    deps: tuple[str, ...] = ()

    @property
    def sort_key(self) -> tuple[int, int]:
        match = re.match(r"PLC-E(\d+)-S(\d+)", self.story_id)
        if not match:
            return (999, 999)
        return (int(match.group(1)), int(match.group(2)))


@dataclass
class TriageResult:
    stories: list[Story]
    order: list[Story]
    ready: list[Story]
    next_story: Story | None
    blocked: list[Story] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)


def parse_stories(markdown: str) -> list[tuple[str, str]]:
    return [(m.group("id"), m.group("title").strip()) for m in STORY_RE.finditer(markdown)]


def load_ledger(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"ledger root must be a list: {path}")
    ledger: dict[str, dict[str, object]] = {}
    for entry in data:
        if not isinstance(entry, dict) or not isinstance(entry.get("story_id"), str):
            continue
        ledger[entry["story_id"]] = entry
    return ledger


def caf_id_for(index: int, story_id: str, ledger_entry: dict[str, object] | None) -> str:
    if ledger_entry and isinstance(ledger_entry.get("caf_id"), str):
        return str(ledger_entry["caf_id"])
    return f"CAF-{114 + index}"


def build_stories(markdown: str, ledger: dict[str, dict[str, object]]) -> list[Story]:
    parsed = parse_stories(markdown)
    stories: list[Story] = []
    for index, (story_id, title) in enumerate(parsed):
        entry = ledger.get(story_id)
        status = str(entry.get("status", "backlog")) if entry else "backlog"
        blocker = None
        if entry and isinstance(entry.get("blocker"), dict):
            blocker_dict = entry["blocker"]
            blocker = str(blocker_dict.get("reason", "")).strip() or None
        pr_links: tuple[str, ...] = ()
        if entry and isinstance(entry.get("pr_links"), list):
            pr_links = tuple(str(link) for link in entry["pr_links"] if str(link).strip())
        stories.append(
            Story(
                story_id=story_id,
                title=title,
                caf_id=caf_id_for(index, story_id, entry),
                status=status,
                blocker=blocker,
                pr_links=pr_links,
                deps=tuple(sorted(DEPENDENCIES.get(story_id, set()))),
            )
        )
    return stories


def dependency_order(stories: list[Story]) -> list[Story]:
    by_id = {story.story_id: story for story in stories}
    ordered: list[Story] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(story_id: str) -> None:
        if story_id in visited:
            return
        if story_id in visiting:
            raise ValueError(f"dependency cycle detected at {story_id}")
        visiting.add(story_id)
        for dep in sorted(DEPENDENCIES.get(story_id, set())):
            if dep in by_id:
                visit(dep)
        visiting.remove(story_id)
        visited.add(story_id)
        ordered.append(by_id[story_id])

    for story in sorted(stories, key=lambda item: (PRIORITY.get(item.story_id, 500), item.sort_key)):
        visit(story.story_id)
    return ordered


def unmet_dependencies(story: Story, by_id: dict[str, Story]) -> list[str]:
    unmet: list[str] = []
    for dep in story.deps:
        dep_story = by_id.get(dep)
        if dep_story is None:
            unmet.append(dep)
        elif dep_story.status not in DONE_STATUSES:
            unmet.append(f"{dep_story.caf_id}/{dep_story.story_id} ({dep_story.status})")
    return unmet


def triage(stories: list[Story]) -> TriageResult:
    by_id = {story.story_id: story for story in stories}
    ordered = dependency_order(stories)
    ready: list[Story] = []
    blocked: list[Story] = []
    skipped: dict[str, str] = {}

    for story in ordered:
        if story.status in DONE_STATUSES:
            skipped[story.story_id] = "already done"
            continue
        if story.status in BLOCKED_STATUSES:
            blocked.append(story)
            skipped[story.story_id] = story.blocker or "blocked"
            continue
        if story.status == "review":
            skipped[story.story_id] = "in review"
            continue
        unmet = unmet_dependencies(story, by_id)
        if unmet:
            skipped[story.story_id] = "waiting on " + ", ".join(unmet)
            continue
        if story.status in AVAILABLE_STATUSES:
            ready.append(story)

    next_story = ready[0] if ready else None
    return TriageResult(stories=stories, order=ordered, ready=ready, next_story=next_story, blocked=blocked, skipped=skipped)


def git_branch_evidence(project_root: Path, caf_id: str) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "branch", "-a", "--list", f"*{caf_id}*"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip().lstrip("* ").strip() for line in proc.stdout.splitlines() if line.strip()]


def render_report(result: TriageResult, project_root: Path) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Lifecycle Next-Ticket Triage Report",
        "",
        f"- Generated at: {generated}",
        "- BMAD source: `_bmad_output/planning-artifacts/project-lifecycle-workflow-stack-epics.md`",
        "- Status source: `_bmad_output/planning-artifacts/lifecycle-status-ledger.json`",
        "- Dependency graph: `skills/project-lifecycle/scripts/triage_next_ticket.py`",
        "",
    ]
    if result.next_story:
        lines.extend(
            [
                "## Selected Next Ticket",
                "",
                f"- {result.next_story.caf_id} / {result.next_story.story_id}: {result.next_story.title}",
                f"- Status: `{result.next_story.status}`",
                "- Reason: first unblocked story in dependency order with all dependencies done.",
                "",
            ]
        )
    else:
        lines.extend(["## Selected Next Ticket", "", "- None: no unblocked ticket is ready.", ""])

    lines.extend(["## Optimal Implementation Order", ""])
    for index, story in enumerate(result.order, start=1):
        deps = ", ".join(story.deps) if story.deps else "none"
        skip = result.skipped.get(story.story_id, "ready")
        branches = git_branch_evidence(project_root, story.caf_id)
        branch_text = f"; branches: {', '.join(branches)}" if branches else ""
        lines.append(
            f"{index}. {story.caf_id} / {story.story_id}: {story.title} "
            f"`{story.status}` deps: {deps}; triage: {skip}{branch_text}"
        )

    if result.ready:
        lines.extend(["", "## Ready Queue", ""])
        for story in result.ready:
            lines.append(f"- {story.caf_id} / {story.story_id}: {story.title}")

    if result.blocked:
        lines.extend(["", "## Blocked", ""])
        for story in result.blocked:
            lines.append(f"- {story.caf_id} / {story.story_id}: {story.blocker or 'blocked'}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    parser.add_argument("--ledger", default=DEFAULT_LEDGER)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    project_root = Path.cwd()
    artifact_path = project_root / args.artifact
    ledger_path = project_root / args.ledger
    stories = build_stories(artifact_path.read_text(), load_ledger(ledger_path))
    result = triage(stories)

    if args.format == "json":
        payload = {
            "next": result.next_story.__dict__ if result.next_story else None,
            "ready": [story.__dict__ for story in result.ready],
            "order": [story.__dict__ for story in result.order],
            "skipped": result.skipped,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        report = render_report(result, project_root)
        print(report)

    if args.write_report:
        report_path = project_root / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(result, project_root))
        print(f"wrote {args.report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
