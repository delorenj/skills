#!/usr/bin/env python3
"""Executable verifier for detect_plane_drift.py (CAF-119 / PLC-E2-S3).

Run with:

    python3 skills/project-lifecycle/scripts/test_detect_plane_drift.py

Stdlib-only (unittest). Covers: missing Plane issue, orphan Plane issue,
title mismatch, status-only drift, requirement/status categorization,
suggested update sources, and CLI exit codes 0/1/2 in offline mode.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "detect_plane_drift.py"

spec = importlib.util.spec_from_file_location("detect_plane_drift", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod  # required for dataclasses under Python 3.13+
spec.loader.exec_module(mod)


FIXTURE_MARKDOWN = """# Fixture Epics

## Epic 9: Drift fixtures

### PLC-E9-S1: Clean matching story

As a tester, I want a clean pair, so matched stories produce no findings.

Acceptance criteria:

- Matches its Plane issue exactly.

### PLC-E9-S2: Story missing its Plane issue

As a tester, I want a missing mirror, so the detector flags it.

Acceptance criteria:

- No Plane issue exists for this story.

### PLC-E9-S3: Story whose Plane title diverged

As a tester, I want a renamed Plane issue, so the detector flags the title.

Acceptance criteria:

- Plane title differs from this heading.

### PLC-E9-S4: Story with declared status

Status: in progress

As a tester, I want a declared BMAD status, so pure status drift is testable.

Acceptance criteria:

- BMAD says in progress while Plane says Done.

### PLC-E9-S5: Story closed only in Plane

As a tester, I want a Plane-only Done signal, so unknown BMAD status is graceful.

Acceptance criteria:

- Plane shows Done; BMAD has no status marker.
"""

FIXTURE_ISSUES = {
    "states": [
        {"id": "11111111-1111-1111-1111-111111111111", "name": "Backlog"},
        {"id": "22222222-2222-2222-2222-222222222222", "name": "Todo"},
        {"id": "33333333-3333-3333-3333-333333333333", "name": "In Progress"},
        {"id": "44444444-4444-4444-4444-444444444444", "name": "Done"},
    ],
    "issues": [
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000001",
            "sequence_id": 901,
            "name": "[Lifecycle] PLC-E9-S1: Clean matching story",
            "state": "11111111-1111-1111-1111-111111111111",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000003",
            "sequence_id": 903,
            "name": "[Lifecycle] PLC-E9-S3: Some old divergent title",
            "state": "11111111-1111-1111-1111-111111111111",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000004",
            "sequence_id": 904,
            "name": "[Lifecycle] PLC-E9-S4: Story with declared status",
            "state": "44444444-4444-4444-4444-444444444444",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000005",
            "sequence_id": 905,
            "name": "[Lifecycle] PLC-E9-S5: Story closed only in Plane",
            "state": "44444444-4444-4444-4444-444444444444",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000009",
            "sequence_id": 909,
            "name": "[Lifecycle] PLC-E9-S9: Orphan issue with no BMAD source",
            "state": "22222222-2222-2222-2222-222222222222",
        },
        {
            "id": "bbbbbbbb-0000-0000-0000-000000000001",
            "sequence_id": 999,
            "name": "Unrelated non-lifecycle ticket",
            "state": "11111111-1111-1111-1111-111111111111",
        },
    ],
}

CLEAN_ISSUES = {
    "states": FIXTURE_ISSUES["states"],
    "issues": [
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000001",
            "sequence_id": 901,
            "name": "[Lifecycle] PLC-E9-S1: Clean matching story",
            "state": "11111111-1111-1111-1111-111111111111",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000002",
            "sequence_id": 902,
            "name": "[Lifecycle] PLC-E9-S2: Story missing its Plane issue",
            "state": "22222222-2222-2222-2222-222222222222",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000003",
            "sequence_id": 903,
            "name": "[Lifecycle] PLC-E9-S3: Story whose Plane title diverged",
            "state": "11111111-1111-1111-1111-111111111111",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000004",
            "sequence_id": 904,
            "name": "[Lifecycle] PLC-E9-S4: Story with declared status",
            "state": "33333333-3333-3333-3333-333333333333",
        },
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000005",
            "sequence_id": 905,
            "name": "[Lifecycle] PLC-E9-S5: Story closed only in Plane",
            "state": "22222222-2222-2222-2222-222222222222",
        },
    ],
}


def run_detection(issues_payload: dict, markdown: str = FIXTURE_MARKDOWN):
    stories = mod.parse_stories(markdown)
    raw_issues, state_names = issues_payload["issues"], {
        s["id"]: s["name"] for s in issues_payload.get("states", [])
    }
    issues = mod.build_issues(raw_issues, state_names)
    return mod.detect_drift(stories, issues)


class DetectDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.findings, self.notes, self.lifecycle_total, self.matched = run_detection(FIXTURE_ISSUES)
        self.by_kind = {}
        for finding in self.findings:
            self.by_kind.setdefault(finding.kind, []).append(finding)

    def test_missing_plane_issue_detected(self) -> None:
        kinds = self.by_kind.get("missing_plane_issue", [])
        self.assertEqual([f.story_id for f in kinds], ["PLC-E9-S2"])
        self.assertEqual(kinds[0].category, "requirement")
        self.assertIn("Update Plane", kinds[0].suggested_update)

    def test_orphan_plane_issue_detected(self) -> None:
        kinds = self.by_kind.get("orphan_plane_issue", [])
        self.assertEqual(len(kinds), 1)
        self.assertEqual(kinds[0].plane_issue, "CAF-909")
        self.assertEqual(kinds[0].category, "requirement")
        self.assertIn("BMAD is requirements truth", kinds[0].suggested_update)

    def test_non_lifecycle_issue_not_flagged_as_orphan(self) -> None:
        orphan_refs = [f.plane_issue for f in self.by_kind.get("orphan_plane_issue", [])]
        self.assertNotIn("CAF-999", orphan_refs)
        self.assertEqual(self.lifecycle_total, 5)

    def test_title_mismatch_detected(self) -> None:
        kinds = self.by_kind.get("title_mismatch", [])
        self.assertEqual([f.story_id for f in kinds], ["PLC-E9-S3"])
        self.assertEqual(kinds[0].category, "requirement")
        self.assertIn("rename", kinds[0].suggested_update.lower())

    def test_status_only_drift_detected(self) -> None:
        kinds = self.by_kind.get("status_mismatch", [])
        self.assertEqual([f.story_id for f in kinds], ["PLC-E9-S4"])
        self.assertEqual(kinds[0].category, "status")
        self.assertIn("Plane is status truth", kinds[0].suggested_update)
        # Pure status drift: S4 must not also appear as requirement drift.
        s4_requirement = [
            f for f in self.findings if f.story_id == "PLC-E9-S4" and f.category == "requirement"
        ]
        self.assertEqual(s4_requirement, [])

    def test_plane_only_status_signal_when_bmad_status_unknown(self) -> None:
        kinds = self.by_kind.get("status_unknown_in_bmad", [])
        self.assertEqual([f.story_id for f in kinds], ["PLC-E9-S5"])
        self.assertEqual(kinds[0].category, "status")
        self.assertIn("Update BMAD", kinds[0].suggested_update)

    def test_requirement_and_status_drift_distinguished(self) -> None:
        categories = {f.category for f in self.findings}
        self.assertEqual(categories, {"requirement", "status"})
        requirement_kinds = {f.kind for f in self.findings if f.category == "requirement"}
        status_kinds = {f.kind for f in self.findings if f.category == "status"}
        self.assertEqual(requirement_kinds, {"missing_plane_issue", "orphan_plane_issue", "title_mismatch"})
        self.assertEqual(status_kinds, {"status_mismatch", "status_unknown_in_bmad"})

    def test_every_finding_suggests_a_source_to_update(self) -> None:
        for finding in self.findings:
            self.assertTrue(
                "Update Plane" in finding.suggested_update
                or "Update BMAD" in finding.suggested_update
                or "update the stale side" in finding.suggested_update,
                msg=f"finding {finding.kind} lacks an update suggestion",
            )

    def test_clean_fixture_has_no_findings(self) -> None:
        findings, notes, lifecycle_total, matched = run_detection(CLEAN_ISSUES)
        self.assertEqual(findings, [])
        self.assertEqual(matched, 5)

    def test_backlog_todo_not_flagged_without_bmad_status(self) -> None:
        # S1 is Backlog with no BMAD status: must not produce a status finding.
        s1 = [f for f in self.findings if f.story_id == "PLC-E9-S1"]
        self.assertEqual(s1, [])


class PlaneHttpTests(unittest.TestCase):
    def test_http_get_json_uses_curl_and_parses_json(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["curl"],
            returncode=0,
            stdout='{"results": []}',
            stderr="",
        )
        with patch.object(mod.subprocess, "run", return_value=completed) as run:
            payload = mod.http_get_json("https://plane.example/issues/", "secret-token")

        self.assertEqual(payload, {"results": []})
        command = run.call_args.args[0]
        self.assertEqual(command[0], "curl")
        self.assertIn("X-API-Key: secret-token", command)

    def test_http_get_json_reports_curl_failure_without_api_key(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["curl"],
            returncode=22,
            stdout="",
            stderr="curl: (22) The requested URL returned error: 403",
        )
        with patch.object(mod.subprocess, "run", return_value=completed):
            with self.assertRaises(RuntimeError) as context:
                mod.http_get_json("https://plane.example/issues/", "secret-token")

        message = str(context.exception)
        self.assertIn("Plane GET failed", message)
        self.assertNotIn("secret-token", message)


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.artifact = self.root / "epics.md"
        self.artifact.write_text(FIXTURE_MARKDOWN)
        self.drift_json = self.root / "issues-drift.json"
        self.drift_json.write_text(json.dumps(FIXTURE_ISSUES))
        self.clean_json = self.root / "issues-clean.json"
        self.clean_json.write_text(json.dumps(CLEAN_ISSUES))

    def run_cli(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MODULE_PATH), "--artifact", str(self.artifact), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_exit_zero_when_no_drift(self) -> None:
        result = self.run_cli("--issues-json", str(self.clean_json))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("RESULT: NO DRIFT", result.stdout)

    def test_exit_one_when_drift_found(self) -> None:
        result = self.run_cli("--issues-json", str(self.drift_json))
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        self.assertIn("RESULT: DRIFT", result.stdout)
        self.assertIn("Requirement Drift", result.stdout)
        self.assertIn("Status Drift", result.stdout)

    def test_json_format_output(self) -> None:
        result = self.run_cli("--issues-json", str(self.drift_json), "--format", "json")
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["drift"])
        self.assertEqual(payload["truth"], {"requirements": "bmad", "status": "plane"})
        kinds = {f["kind"] for f in payload["findings"]}
        self.assertEqual(
            kinds,
            {
                "missing_plane_issue",
                "orphan_plane_issue",
                "title_mismatch",
                "status_mismatch",
                "status_unknown_in_bmad",
            },
        )

    def test_exit_two_on_missing_issues_file(self) -> None:
        result = self.run_cli("--issues-json", str(self.root / "nope.json"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_exit_two_on_malformed_issues_json(self) -> None:
        bad = self.root / "bad.json"
        bad.write_text("{\"unexpected\": true}")
        result = self.run_cli("--issues-json", str(bad))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_ignore_plane_only_status_flag(self) -> None:
        result = self.run_cli(
            "--issues-json", str(self.drift_json), "--format", "json", "--ignore-plane-only-status"
        )
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        payload = json.loads(result.stdout)
        kinds = {f["kind"] for f in payload["findings"]}
        self.assertNotIn("status_unknown_in_bmad", kinds)
        self.assertIn("status_mismatch", kinds)


if __name__ == "__main__":
    unittest.main(verbosity=2)
