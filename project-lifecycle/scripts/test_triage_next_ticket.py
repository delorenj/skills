#!/usr/bin/env python3
"""Verifier for triage_next_ticket.py (PLC-E2-S5 / CAF-121)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "triage_next_ticket.py"

spec = importlib.util.spec_from_file_location("triage_next_ticket", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


FIXTURE_MARKDOWN = """# Lifecycle fixture

### PLC-E1-S1: Verify root BMAD install and module set

Acceptance criteria:

- fixture

### PLC-E1-S2: Author Project Lifecycle skill

Acceptance criteria:

- fixture

### PLC-E1-S3: Add lifecycle snapshot helper

Acceptance criteria:

- fixture

### PLC-E2-S1: Define BMAD-to-Plane mapping contract

Acceptance criteria:

- fixture

### PLC-E2-S2: Build Plane mirror creation script

Acceptance criteria:

- fixture

### PLC-E2-S3: Build parity drift detector

Acceptance criteria:

- fixture

### PLC-E2-S4: Add status reconciliation workflow

Acceptance criteria:

- fixture

### PLC-E2-S5: Add next-ticket triage workflow

Acceptance criteria:

- fixture

### PLC-E3-S1: Define intent capture format

Acceptance criteria:

- fixture
"""


def ledger_entry(story_id: str, caf_id: str, status: str = "backlog") -> dict[str, object]:
    return {
        "story_id": story_id,
        "caf_id": caf_id,
        "status": status,
        "blocker": None,
        "pr_links": [],
        "ac_verified": None,
        "updated": "2026-06-11",
    }


class TriageTests(unittest.TestCase):
    def test_dependency_order_keeps_triage_after_parity_and_status(self) -> None:
        ledger = {
            "PLC-E1-S1": ledger_entry("PLC-E1-S1", "CAF-114", "done"),
            "PLC-E1-S2": ledger_entry("PLC-E1-S2", "CAF-115", "done"),
            "PLC-E1-S3": ledger_entry("PLC-E1-S3", "CAF-116", "done"),
            "PLC-E2-S1": ledger_entry("PLC-E2-S1", "CAF-117", "done"),
            "PLC-E2-S2": ledger_entry("PLC-E2-S2", "CAF-118", "done"),
            "PLC-E2-S3": ledger_entry("PLC-E2-S3", "CAF-119", "done"),
            "PLC-E2-S4": ledger_entry("PLC-E2-S4", "CAF-120", "done"),
        }
        stories = mod.build_stories(FIXTURE_MARKDOWN, ledger)
        result = mod.triage(stories)

        self.assertIsNotNone(result.next_story)
        self.assertEqual(result.next_story.story_id, "PLC-E2-S5")

    def test_unmet_dependency_skips_later_story(self) -> None:
        ledger = {
            "PLC-E1-S1": ledger_entry("PLC-E1-S1", "CAF-114", "done"),
            "PLC-E1-S2": ledger_entry("PLC-E1-S2", "CAF-115", "done"),
            "PLC-E1-S3": ledger_entry("PLC-E1-S3", "CAF-116", "done"),
            "PLC-E2-S1": ledger_entry("PLC-E2-S1", "CAF-117", "done"),
            "PLC-E2-S2": ledger_entry("PLC-E2-S2", "CAF-118", "done"),
        }
        stories = mod.build_stories(FIXTURE_MARKDOWN, ledger)
        result = mod.triage(stories)

        self.assertEqual(result.next_story.story_id, "PLC-E2-S3")
        self.assertIn("PLC-E2-S5", result.skipped)
        self.assertIn("PLC-E2-S3", result.skipped["PLC-E2-S5"])

    def test_review_status_is_not_selected_as_next_work(self) -> None:
        ledger = {
            "PLC-E1-S1": ledger_entry("PLC-E1-S1", "CAF-114", "done"),
            "PLC-E1-S2": ledger_entry("PLC-E1-S2", "CAF-115", "done"),
            "PLC-E1-S3": ledger_entry("PLC-E1-S3", "CAF-116", "done"),
            "PLC-E2-S1": ledger_entry("PLC-E2-S1", "CAF-117", "done"),
            "PLC-E2-S2": ledger_entry("PLC-E2-S2", "CAF-118", "done"),
            "PLC-E2-S3": ledger_entry("PLC-E2-S3", "CAF-119", "review"),
        }
        stories = mod.build_stories(FIXTURE_MARKDOWN, ledger)
        result = mod.triage(stories)

        self.assertIsNone(result.next_story)
        self.assertEqual(result.skipped["PLC-E2-S3"], "in review")


class CliTests(unittest.TestCase):
    def test_cli_writes_report_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "epics.md"
            ledger = root / "ledger.json"
            report = root / "report.md"
            artifact.write_text(FIXTURE_MARKDOWN)
            ledger.write_text(json.dumps([ledger_entry("PLC-E1-S1", "CAF-114", "done")]))

            proc = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--artifact",
                    str(artifact),
                    "--ledger",
                    str(ledger),
                    "--report",
                    str(report),
                    "--write-report",
                    "--format",
                    "json",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(report.exists())
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["next"]["story_id"], "PLC-E1-S2")
            self.assertIn("Lifecycle Next-Ticket Triage Report", report.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
