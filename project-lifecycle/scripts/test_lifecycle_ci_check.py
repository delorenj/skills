#!/usr/bin/env python3
"""Verifier for lifecycle_ci_check.py (PLC-E6-S4 / CAF-139)."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "lifecycle_ci_check.py"

spec = importlib.util.spec_from_file_location("lifecycle_ci_check", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class LifecycleCiCheckTests(unittest.TestCase):
    def test_skill_frontmatter_is_valid(self) -> None:
        parsed = mod.parse_skill_frontmatter(mod.SKILL.read_text())
        self.assertEqual(parsed["name"], "project-lifecycle")
        self.assertTrue(parsed["description"])

    def test_lifecycle_story_count_and_caf_range(self) -> None:
        stories = mod.lifecycle_stories()
        self.assertEqual(len(stories), 26)
        entries = json.loads(mod.LEDGER.read_text())
        self.assertEqual({entry["caf_id"] for entry in entries}, {f"CAF-{n}" for n in range(114, 140)})

    def test_main_passes_current_artifacts(self) -> None:
        self.assertEqual(mod.main(), 0)

    def test_done_ledger_entries_have_acceptance_evidence(self) -> None:
        result = mod.CheckResult()
        stories = mod.lifecycle_stories()
        mod.check_ledger(result, stories)
        self.assertEqual(result.errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
