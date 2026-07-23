#!/usr/bin/env python3
"""CI checks for Project Lifecycle artifacts (PLC-E6-S4 / CAF-139)."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL = PROJECT_ROOT / "skills" / "project-lifecycle" / "SKILL.md"
EPICS = PROJECT_ROOT / "_bmad_output" / "planning-artifacts" / "project-lifecycle-workflow-stack-epics.md"
MIRROR_REPORT = PROJECT_ROOT / "_bmad_output" / "planning-artifacts" / "project-lifecycle-plane-mirror-report.md"
LEDGER = PROJECT_ROOT / "_bmad_output" / "planning-artifacts" / "lifecycle-status-ledger.json"
WORKFLOW_SCHEMA_PATH = PROJECT_ROOT / "workflow-artifacts" / "workflow-schema.json"
WORKFLOW_EXAMPLES_DIR = PROJECT_ROOT / "workflow-artifacts" / "workflow-examples"

STORY_RE = re.compile(r"^### (?P<story_id>PLC-E\d+-S\d+): (?P<title>.+)$", re.MULTILINE)
CAF_RE = re.compile(r"CAF-(\d+)")
REFERENCE_RE = re.compile(r"`(references/[^`]+\.md)`")
VALID_LEDGER_STATUSES = {"backlog", "todo", "in-progress", "blocked", "review", "done"}


@dataclass
class CheckResult:
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def parse_skill_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    _, frontmatter, _body = text.split("---", 2)
    parsed: dict[str, str] = {}
    for raw_line in frontmatter.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def lifecycle_stories() -> list[str]:
    return [match.group("story_id") for match in STORY_RE.finditer(EPICS.read_text())]


def check_skill(result: CheckResult) -> None:
    try:
        text = SKILL.read_text()
        frontmatter = parse_skill_frontmatter(text)
    except Exception as exc:
        result.error(f"skill frontmatter invalid: {exc}")
        return
    if frontmatter.get("name") != "project-lifecycle":
        result.error("skill frontmatter name must be project-lifecycle")
    if not frontmatter.get("description"):
        result.error("skill frontmatter description is required")

    for reference in sorted(set(REFERENCE_RE.findall(text))):
        if not (SKILL.parent / reference).exists():
            result.error(f"skill references missing file: {reference}")


def check_mirror_report(result: CheckResult, stories: list[str]) -> None:
    if not MIRROR_REPORT.exists():
        result.error(f"missing mirror report: {MIRROR_REPORT.relative_to(PROJECT_ROOT)}")
        return
    text = MIRROR_REPORT.read_text()
    source_line = f"BMAD source: `{EPICS.relative_to(PROJECT_ROOT)}`"
    if source_line not in text:
        result.error("mirror report is missing BMAD source link")
    missing = [story_id for story_id in stories if story_id not in text]
    if missing:
        result.error(f"mirror report missing story links: {', '.join(missing)}")
    caf_ids = {f"CAF-{n}" for n in range(114, 140)}
    missing_caf = sorted(caf_id for caf_id in caf_ids if caf_id not in text)
    if missing_caf:
        result.error(f"mirror report missing CAF IDs: {', '.join(missing_caf)}")


def check_ledger(result: CheckResult, stories: list[str]) -> None:
    try:
        entries = json.loads(LEDGER.read_text())
    except Exception as exc:
        result.error(f"status ledger invalid JSON: {exc}")
        return
    if not isinstance(entries, list):
        result.error("status ledger root must be a list")
        return

    by_story: dict[str, dict[str, object]] = {}
    caf_ids: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            result.error(f"ledger entry[{index}] must be an object")
            continue
        story_id = entry.get("story_id")
        caf_id = entry.get("caf_id")
        status = entry.get("status")
        if not isinstance(story_id, str):
            result.error(f"ledger entry[{index}] missing story_id")
            continue
        if story_id in by_story:
            result.error(f"duplicate ledger story_id: {story_id}")
        by_story[story_id] = entry
        if not isinstance(caf_id, str) or not CAF_RE.fullmatch(caf_id):
            result.error(f"{story_id}: invalid caf_id {caf_id!r}")
        elif caf_id in caf_ids:
            result.error(f"duplicate ledger caf_id: {caf_id}")
        else:
            caf_ids.add(caf_id)
        if status not in VALID_LEDGER_STATUSES:
            result.error(f"{story_id}: invalid status {status!r}")
        if status == "done":
            ac_verified = entry.get("ac_verified")
            if not (
                isinstance(ac_verified, dict)
                and ac_verified.get("verified") is True
                and isinstance(ac_verified.get("evidence"), str)
                and ac_verified["evidence"].strip()
            ):
                result.error(f"{story_id}: done status requires verified acceptance evidence")

    missing = [story_id for story_id in stories if story_id not in by_story]
    if missing:
        result.error(f"status ledger missing stories: {', '.join(missing)}")


def check_workflow_schema_examples(result: CheckResult) -> None:
    if not WORKFLOW_SCHEMA_PATH.exists() and not WORKFLOW_EXAMPLES_DIR.exists():
        result.note("workflow artifact schema examples not present yet; CAF-123 owns the first schema")
        return
    if not WORKFLOW_SCHEMA_PATH.exists():
        result.error("workflow artifact examples exist without workflow-schema.json")
        return
    try:
        schema_payload = json.loads(WORKFLOW_SCHEMA_PATH.read_text())
    except Exception as exc:
        result.error(f"workflow-schema.json is invalid JSON: {exc}")
        return
    required = schema_payload.get("required", [])
    if not isinstance(required, list):
        result.error("workflow-schema.json required must be a list when present")
        return
    examples = sorted(WORKFLOW_EXAMPLES_DIR.glob("*.json")) if WORKFLOW_EXAMPLES_DIR.exists() else []
    if not examples:
        result.error("workflow-schema.json exists but no JSON examples were found")
        return
    for example in examples:
        try:
            payload = json.loads(example.read_text())
        except Exception as exc:
            result.error(f"{example.relative_to(PROJECT_ROOT)} invalid JSON: {exc}")
            continue
        if not isinstance(payload, dict):
            result.error(f"{example.relative_to(PROJECT_ROOT)} must be an object")
            continue
        missing = [key for key in required if key not in payload]
        if missing:
            result.error(f"{example.relative_to(PROJECT_ROOT)} missing required keys: {', '.join(missing)}")


def main() -> int:
    result = CheckResult()
    if not EPICS.exists():
        result.error(f"missing lifecycle epics artifact: {EPICS.relative_to(PROJECT_ROOT)}")
        stories: list[str] = []
    else:
        stories = lifecycle_stories()
        if len(stories) != 26:
            result.error(f"expected 26 lifecycle stories, found {len(stories)}")

    check_skill(result)
    check_mirror_report(result, stories)
    check_ledger(result, stories)
    check_workflow_schema_examples(result)

    for note in result.notes:
        print(f"note: {note}")
    if result.errors:
        for message in result.errors:
            print(f"error: {message}", file=sys.stderr)
        return 1
    print("lifecycle CI checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
