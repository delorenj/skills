#!/usr/bin/env python3
"""Verifier for reconcile_status.py (PLC-E2-S4 / CAF-120).

Stdlib-only unittest suite. Covers: valid status mapping, done-without-
verification rejection, blocked-missing-fields rejection, PR-link acceptance,
the seeded real ledger, and CLI exit codes. Never touches the network.

Run: python3 skills/project-lifecycle/scripts/test_reconcile_status.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent.parent.parent
REAL_LEDGER = PROJECT_ROOT / "_bmad_output" / "planning-artifacts" / "lifecycle-status-ledger.json"

sys.path.insert(0, str(SCRIPTS_DIR))

import reconcile_status  # noqa: E402


def entry(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "story_id": "PLC-E2-S4",
        "caf_id": "CAF-120",
        "status": "backlog",
        "blocker": None,
        "pr_links": [],
        "ac_verified": None,
        "updated": "2026-06-11",
    }
    base.update(overrides)
    return base


class ValidMappingTests(unittest.TestCase):
    def test_every_ledger_status_maps_to_a_plane_state(self) -> None:
        expected = {
            "backlog": "Backlog",
            "todo": "Todo",
            "in-progress": "In Progress",
            "blocked": "In Progress",
            "review": "Review",
            "done": "Done",
        }
        self.assertEqual(reconcile_status.STATUS_TO_PLANE_STATE, expected)

    def test_valid_ledger_passes_and_plans_states(self) -> None:
        entries = [
            entry(),
            entry(story_id="PLC-E2-S5", caf_id="CAF-121", status="todo"),
            entry(story_id="PLC-E3-S1", caf_id="CAF-122", status="in-progress"),
            entry(
                story_id="PLC-E3-S2",
                caf_id="CAF-123",
                status="blocked",
                blocker={"reason": "Waiting on Plane credentials", "owner": "Jarad", "date": "2026-06-11"},
            ),
            entry(story_id="PLC-E3-S3", caf_id="CAF-124", status="review"),
            entry(
                story_id="PLC-E3-S4",
                caf_id="CAF-125",
                status="done",
                ac_verified={"verified": True, "evidence": "python3 scripts/test_reconcile_status.py passed"},
            ),
        ]
        result = reconcile_status.validate_ledger(entries)
        self.assertEqual(result.errors, [])

        planned = reconcile_status.plan_changes(entries)
        self.assertEqual(
            [change.plane_state for change in planned],
            ["Backlog", "Todo", "In Progress", "In Progress", "Review", "Done"],
        )

    def test_blocked_entry_plans_blocker_comment_with_reason_owner_date(self) -> None:
        blocked = entry(
            status="blocked",
            blocker={"reason": "API key missing", "owner": "Jarad", "date": "2026-06-11"},
        )
        planned = reconcile_status.plan_changes([blocked])
        self.assertEqual(len(planned[0].comments), 1)
        comment = planned[0].comments[0]
        self.assertIn("[blocked]", comment)
        self.assertIn("API key missing", comment)
        self.assertIn("owner: Jarad", comment)
        self.assertIn("since: 2026-06-11", comment)


class DoneGateTests(unittest.TestCase):
    def test_done_without_ac_verified_rejected(self) -> None:
        result = reconcile_status.validate_ledger([entry(status="done", ac_verified=None)])
        self.assertTrue(any("ac_verified" in message for message in result.errors))

    def test_done_with_verified_false_rejected(self) -> None:
        result = reconcile_status.validate_ledger(
            [entry(status="done", ac_verified={"verified": False, "evidence": "tests passed"})]
        )
        self.assertTrue(any("verified" in message for message in result.errors))

    def test_done_with_empty_evidence_rejected(self) -> None:
        result = reconcile_status.validate_ledger(
            [entry(status="done", ac_verified={"verified": True, "evidence": "   "})]
        )
        self.assertTrue(any("evidence" in message for message in result.errors))

    def test_done_with_verification_accepted(self) -> None:
        result = reconcile_status.validate_ledger(
            [entry(status="done", ac_verified={"verified": True, "evidence": "verifier run output attached"})]
        )
        self.assertEqual(result.errors, [])


class BlockedFieldTests(unittest.TestCase):
    def test_blocked_without_blocker_rejected(self) -> None:
        result = reconcile_status.validate_ledger([entry(status="blocked", blocker=None)])
        self.assertTrue(any("blocker" in message for message in result.errors))

    def test_blocked_missing_owner_rejected(self) -> None:
        result = reconcile_status.validate_ledger(
            [entry(status="blocked", blocker={"reason": "Waiting on review", "date": "2026-06-11"})]
        )
        self.assertTrue(any("blocker.owner" in message for message in result.errors))

    def test_blocked_missing_reason_rejected(self) -> None:
        result = reconcile_status.validate_ledger(
            [entry(status="blocked", blocker={"owner": "Jarad", "date": "2026-06-11"})]
        )
        self.assertTrue(any("blocker.reason" in message for message in result.errors))

    def test_blocked_bad_date_rejected(self) -> None:
        result = reconcile_status.validate_ledger(
            [entry(status="blocked", blocker={"reason": "Waiting", "owner": "Jarad", "date": "next week"})]
        )
        self.assertTrue(any("blocker.date" in message for message in result.errors))


class PrLinkTests(unittest.TestCase):
    def test_pr_links_accepted_in_any_status_and_planned_as_comment(self) -> None:
        links = ["https://github.com/AutomaticAI-io/CoachingAgentFramework/pull/34"]
        for status in ("in-progress", "review"):
            with self.subTest(status=status):
                item = entry(status=status, pr_links=links)
                result = reconcile_status.validate_ledger([item])
                self.assertEqual(result.errors, [])
                planned = reconcile_status.plan_changes([item])
                self.assertTrue(any("[pr-links]" in comment and links[0] in comment for comment in planned[0].comments))

    def test_pr_links_must_be_list_of_strings(self) -> None:
        result = reconcile_status.validate_ledger([entry(pr_links="not-a-list")])
        self.assertTrue(any("pr_links" in message for message in result.errors))


class LedgerShapeTests(unittest.TestCase):
    def test_duplicate_story_ids_rejected(self) -> None:
        result = reconcile_status.validate_ledger([entry(), entry(caf_id="CAF-121")])
        self.assertTrue(any("duplicate story_id" in message for message in result.errors))

    def test_invalid_status_rejected(self) -> None:
        result = reconcile_status.validate_ledger([entry(status="doing")])
        self.assertTrue(any("status" in message for message in result.errors))

    def test_real_seeded_ledger_is_valid_and_complete(self) -> None:
        entries = json.loads(REAL_LEDGER.read_text())
        result = reconcile_status.validate_ledger(entries)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(entries), 26)
        story_ids = {item["story_id"] for item in entries}
        caf_ids = {item["caf_id"] for item in entries}
        self.assertIn("PLC-E1-S1", story_ids)
        self.assertIn("PLC-E6-S4", story_ids)
        self.assertEqual(caf_ids, {f"CAF-{n}" for n in range(114, 140)})


class PlaneRequestTests(unittest.TestCase):
    def test_plane_request_uses_curl_and_parses_json(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["curl"],
            returncode=0,
            stdout='{"results": []}',
            stderr="",
        )
        with patch.object(reconcile_status.subprocess, "run", return_value=completed) as run:
            payload = reconcile_status.plane_request("GET", "https://plane.example/issues/", "secret-token")

        self.assertEqual(payload, {"results": []})
        command = run.call_args.args[0]
        self.assertEqual(command[0], "curl")
        self.assertIn("X-API-Key: secret-token", command)

    def test_plane_request_failure_does_not_echo_api_key(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["curl"],
            returncode=22,
            stdout="",
            stderr="curl: (22) The requested URL returned error: 403",
        )
        with patch.object(reconcile_status.subprocess, "run", return_value=completed):
            with self.assertRaises(RuntimeError) as context:
                reconcile_status.plane_request("GET", "https://plane.example/issues/", "secret-token")

        message = str(context.exception)
        self.assertIn("Plane API GET", message)
        self.assertNotIn("secret-token", message)


class CliExitCodeTests(unittest.TestCase):
    def run_cli(self, ledger_content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write(ledger_content)
            ledger_path = handle.name
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "reconcile_status.py"), "--ledger", ledger_path],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_ledger_dry_run_exits_zero(self) -> None:
        proc = self.run_cli(json.dumps([entry()]))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("dry-run", proc.stdout)
        self.assertIn("Backlog", proc.stdout)

    def test_validation_failure_exits_one(self) -> None:
        proc = self.run_cli(json.dumps([entry(status="done", ac_verified=None)]))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("validation error", proc.stderr)

    def test_unreadable_ledger_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "reconcile_status.py"), "--ledger", "/nonexistent/ledger.json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)

    def test_malformed_json_exits_two(self) -> None:
        proc = self.run_cli("{not json")
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
