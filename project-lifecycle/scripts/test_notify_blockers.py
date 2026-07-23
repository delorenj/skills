#!/usr/bin/env python3
"""Verifier for blocker notification hook (PLC-E6-S3 / CAF-138)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "notify_blockers.py"

spec = importlib.util.spec_from_file_location("notify_blockers", MODULE_PATH)
notify_blockers = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = notify_blockers
spec.loader.exec_module(notify_blockers)


def entry(
    *,
    status: str = "blocked",
    blocker_date: str = "2026-06-09",
    reason: str = "Waiting on review",
    owner: str = "Jarad",
    requested_action: str = "Review the PR and approve or request changes.",
) -> dict:
    blocker = None
    if status == "blocked":
        blocker = {
            "reason": reason,
            "owner": owner,
            "date": blocker_date,
            "missing_input": reason,
            "requested_action": requested_action,
        }
    return {
        "story_id": "PLC-E9-S1",
        "caf_id": "CAF-999",
        "title": "Example blocked story",
        "status": status,
        "blocker": blocker,
        "pr_links": [],
        "ac_verified": None,
        "updated": "2026-06-11",
    }


class NotifyBlockersTests(unittest.TestCase):
    def test_only_alerts_after_threshold(self) -> None:
        alerts = notify_blockers.plan_alerts(
            [entry(blocker_date="2026-06-10")],
            threshold_days=2,
            today=date(2026, 6, 11),
        )

        self.assertEqual(alerts, [])

    def test_alert_includes_ticket_story_missing_input_and_action(self) -> None:
        alerts = notify_blockers.plan_alerts(
            [entry(blocker_date="2026-06-09")],
            threshold_days=2,
            today=date(2026, 6, 11),
        )

        self.assertEqual(len(alerts), 1)
        message = alerts[0].message()
        self.assertIn("CAF-999 / PLC-E9-S1", message)
        self.assertIn("Missing input: Waiting on review", message)
        self.assertIn("Requested action for Jarad", message)
        self.assertIn("Review the PR and approve or request changes.", message)

    def test_non_blocked_entries_do_not_alert(self) -> None:
        alerts = notify_blockers.plan_alerts(
            [entry(status="in-progress")],
            threshold_days=0,
            today=date(2026, 6, 11),
        )

        self.assertEqual(alerts, [])

    def test_secret_like_content_is_redacted(self) -> None:
        alerts = notify_blockers.plan_alerts(
            [
                entry(
                    reason="Need token=abc123 from Damian",
                    requested_action="Set API_KEY=secret-value in env",
                )
            ],
            threshold_days=0,
            today=date(2026, 6, 11),
        )

        message = alerts[0].message()
        self.assertNotIn("abc123", message)
        self.assertNotIn("secret-value", message)
        self.assertIn("<redacted>", message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
