#!/usr/bin/env python3
"""Verifier for review_workflow_artifact.py (PLC-E3-S4 / CAF-125)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parents[2]
REVIEWER_PATH = SCRIPTS_DIR / "review_workflow_artifact.py"
GENERATOR_PATH = SCRIPTS_DIR / "generate_workflow_artifact.py"
INTENT_EXAMPLE = PROJECT_ROOT / "workflow-artifacts" / "examples" / "messages-intent-capture.json"

review_spec = importlib.util.spec_from_file_location("review_workflow_artifact", REVIEWER_PATH)
reviewer = importlib.util.module_from_spec(review_spec)
sys.modules[review_spec.name] = reviewer
review_spec.loader.exec_module(reviewer)

generator_spec = importlib.util.spec_from_file_location(
    "generate_workflow_artifact",
    GENERATOR_PATH,
)
generator = importlib.util.module_from_spec(generator_spec)
sys.modules[generator_spec.name] = generator
generator_spec.loader.exec_module(generator)


def _write_json(payload: dict, directory: Path, name: str = "artifact.json") -> Path:
    path = directory / name
    path.write_text(json.dumps(payload, indent=2))
    return path


class ReviewWorkflowArtifactTests(unittest.TestCase):
    def test_review_highlights_steps_gates_transitions_and_mappings(self) -> None:
        generated = generator.generate_artifact(
            INTENT_EXAMPLE,
            generated_at="2026-06-11T00:00:00Z",
        ).workflow
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(generated, Path(tmp))

            result = reviewer.review_artifact(
                path,
                decision="request_changes",
                reviewer="Jarad",
                reviewed_at="2026-06-11T00:00:00Z",
            )

        self.assertEqual(result.report["summary"]["step_count"], 8)
        first_step = result.report["highlights"]["steps"][0]
        self.assertEqual(
            first_step["prompt"],
            "What is your migraine level right now from 0 to 10?",
        )
        self.assertEqual(first_step["repeat_policy"], "until_valid_rating")
        self.assertEqual(first_step["duplicate_policy"], "merge_with_existing")
        self.assertEqual(first_step["transitions"][0]["target"], "starting_wellbeing_level")
        first_mapping = result.report["highlights"]["database_mappings"][0]
        self.assertEqual(
            first_mapping["storage_target"],
            "protocol_session.starting_migraine_level",
        )

    def test_approve_is_blocked_when_uncertain_mappings_are_not_acknowledged(self) -> None:
        generated = generator.generate_artifact(
            INTENT_EXAMPLE,
            generated_at="2026-06-11T00:00:00Z",
        ).workflow
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(generated, Path(tmp))

            result = reviewer.review_artifact(
                path,
                decision="approve",
                reviewer="Damian",
                reviewed_at="2026-06-11T00:00:00Z",
            )

        self.assertFalse(result.report["decision_allowed"])
        self.assertIn("ack", result.report["decision_reason"])
        self.assertTrue(any(finding.kind == "uncertain_mapping" for finding in result.findings))

    def test_approve_with_ack_uncertain_is_allowed_without_blockers(self) -> None:
        generated = generator.generate_artifact(
            INTENT_EXAMPLE,
            generated_at="2026-06-11T00:00:00Z",
        ).workflow
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(generated, Path(tmp))

            result = reviewer.review_artifact(
                path,
                decision="approve",
                reviewer="Damian",
                reviewed_at="2026-06-11T00:00:00Z",
                ack_uncertain=True,
            )

        self.assertTrue(result.report["decision_allowed"])
        self.assertEqual(result.report["recommended_workflow_status"], "approved")

    def test_missing_rating_requirement_and_duplicate_policy_are_identified(self) -> None:
        generated = generator.generate_artifact(
            INTENT_EXAMPLE,
            generated_at="2026-06-11T00:00:00Z",
        ).workflow
        generated["steps"][0]["completion_gate"]["rating_required"] = False
        generated["steps"][0].pop("duplicate_policy")
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(generated, Path(tmp))

            result = reviewer.review_artifact(
                path,
                decision="request_changes",
                reviewer="Jarad",
                reviewed_at="2026-06-11T00:00:00Z",
            )

        kinds = {finding.kind for finding in result.findings}
        self.assertIn("rating_requirement", kinds)
        self.assertIn("duplicate_policy", kinds)
        self.assertTrue(result.blocking_findings)

    def test_boundary_risk_is_identified(self) -> None:
        generated = generator.generate_artifact(
            INTENT_EXAMPLE,
            generated_at="2026-06-11T00:00:00Z",
        ).workflow
        generated["steps"][0]["prompt"]["coach_context"] = "Private coach-only note"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(generated, Path(tmp))

            result = reviewer.review_artifact(
                path,
                decision="request_changes",
                reviewer="Jarad",
                reviewed_at="2026-06-11T00:00:00Z",
            )

        self.assertTrue(
            any(finding.kind == "client_private_boundary" for finding in result.findings)
        )

    def test_cli_writes_markdown_report_and_blocks_bad_approval(self) -> None:
        generated = generator.generate_artifact(
            INTENT_EXAMPLE,
            generated_at="2026-06-11T00:00:00Z",
        ).workflow
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = _write_json(generated, root)
            report = root / "review.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REVIEWER_PATH),
                    str(artifact),
                    "--decision",
                    "request_changes",
                    "--reviewer",
                    "Jarad",
                    "--output",
                    str(report),
                    "--format",
                    "md",
                    "--reviewed-at",
                    "2026-06-11T00:00:00Z",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("# Workflow Artifact Review", report.read_text())

            proc = subprocess.run(
                [
                    sys.executable,
                    str(REVIEWER_PATH),
                    str(artifact),
                    "--decision",
                    "approve",
                    "--reviewer",
                    "Jarad",
                    "--reviewed-at",
                    "2026-06-11T00:00:00Z",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("approval requires", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
