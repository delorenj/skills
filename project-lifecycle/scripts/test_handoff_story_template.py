#!/usr/bin/env python3
"""Verifier for handoff-ready BMAD story template (PLC-E6-S1 / CAF-136)."""

from __future__ import annotations

import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parents[2]
TEMPLATE_PATH = (
    PROJECT_ROOT
    / "skills"
    / "project-lifecycle"
    / "references"
    / "handoff-story-template.md"
)
SKILL_PATH = PROJECT_ROOT / "skills" / "project-lifecycle" / "SKILL.md"


class HandoffStoryTemplateTests(unittest.TestCase):
    def test_template_contains_required_handoff_sections(self) -> None:
        text = TEMPLATE_PATH.read_text()

        required_sections = [
            "## Story Header",
            "## Source Intent",
            "## User Story",
            "## Acceptance Criteria",
            "## Dependencies",
            "## Implementation Notes",
            "## Validation Plan",
            "## Blocker Handling",
            "## Plane Mirror",
            "## Completion Evidence",
        ]
        for section in required_sections:
            self.assertIn(section, text)

    def test_template_supports_blocked_and_promoted_history_states(self) -> None:
        text = TEMPLATE_PATH.read_text()

        self.assertIn("Status: `backlog | todo | in-progress | blocked | review | done`", text)
        self.assertIn("Promoted from component history: `yes | no`", text)
        self.assertIn("Component source path:", text)
        self.assertIn("Next useful unblocked work:", text)

    def test_project_lifecycle_skill_references_template(self) -> None:
        text = SKILL_PATH.read_text()

        self.assertIn("references/handoff-story-template.md", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
