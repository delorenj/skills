#!/usr/bin/env python3
"""Verifier for Plane sync runbook coverage (PLC-E6-S2 / CAF-137)."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = PROJECT_ROOT / "skills" / "project-lifecycle" / "references" / "plane-sync-runbook.md"
SKILL = PROJECT_ROOT / "skills" / "project-lifecycle" / "SKILL.md"


class PlaneSyncRunbookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = RUNBOOK.read_text()

    def test_documents_plane_config_and_env(self) -> None:
        for required in (".plane.json", "workspace", "project_id", "PLANE_BASE", "PLANE_API_KEY"):
            self.assertIn(required, self.text)

    def test_documents_dry_run_create_update_and_drift_check(self) -> None:
        for required in (
            "sync_plane_from_bmad.py",
            "sync_plane_from_bmad.py --create",
            "detect_plane_drift.py --ignore-plane-only-status",
            "reconcile_status.py",
            "reconcile_status.py --apply",
        ):
            self.assertIn(required, self.text)

    def test_documents_secret_and_failed_write_handling(self) -> None:
        lowered = self.text.lower()
        for required in ("never print", "api key", "failed plane writes", "partially changed"):
            self.assertIn(required, lowered)

    def test_skill_links_to_runbook(self) -> None:
        self.assertIn("references/plane-sync-runbook.md", SKILL.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
