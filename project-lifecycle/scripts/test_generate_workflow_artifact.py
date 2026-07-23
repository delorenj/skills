#!/usr/bin/env python3
"""Verifier for generate_workflow_artifact.py (PLC-E3-S3 / CAF-124)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parents[2]
MODULE_PATH = SCRIPTS_DIR / "generate_workflow_artifact.py"
VALIDATOR_PATH = SCRIPTS_DIR / "validate_workflow_artifacts.py"
INTENT_EXAMPLE = PROJECT_ROOT / "workflow-artifacts" / "examples" / "messages-intent-capture.json"
RUNTIME_EXAMPLE_DIR = PROJECT_ROOT / "workflow-artifacts" / "workflow-examples"

spec = importlib.util.spec_from_file_location("generate_workflow_artifact", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

validator_spec = importlib.util.spec_from_file_location(
    "validate_workflow_artifacts",
    VALIDATOR_PATH,
)
validator = importlib.util.module_from_spec(validator_spec)
sys.modules[validator_spec.name] = validator
validator_spec.loader.exec_module(validator)


class GenerateWorkflowArtifactTests(unittest.TestCase):
    def test_intent_capture_generates_valid_review_required_draft(self) -> None:
        result = mod.generate_artifact(INTENT_EXAMPLE, generated_at="2026-06-11T00:00:00Z")

        workflow = result.workflow
        self.assertEqual(workflow["status"], "draft")
        self.assertTrue(workflow["generation"]["review_required"])
        self.assertEqual(workflow["generation"]["source_reference"], str(INTENT_EXAMPLE))
        self.assertEqual(workflow["workflow_id"], "damian-method.messages")
        self.assertEqual(
            workflow["steps"][0]["transitions"][0]["target"],
            "starting_wellbeing_level",
        )
        validation = validator.validate_workflow(workflow)
        self.assertEqual(validation.errors, [])

    def test_intent_ambiguities_become_uncertain_mappings(self) -> None:
        result = mod.generate_artifact(INTENT_EXAMPLE, generated_at="2026-06-11T00:00:00Z")

        uncertain = result.workflow["generation"]["uncertain_mappings"]
        self.assertTrue(any(item["source"] == "intent.ambiguities" for item in uncertain))

    def test_plain_text_generates_review_only_shell(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write("Breakthrough Sequence\nAsk for negative thoughts and lessons.")
            source = Path(handle.name)

        result = mod.generate_artifact(source, generated_at="2026-06-11T00:00:00Z")

        self.assertEqual(result.workflow["status"], "draft")
        self.assertTrue(result.workflow["generation"]["review_required"])
        self.assertEqual(result.workflow["phase_or_protocol"]["name"], "Breakthrough Sequence")
        self.assertEqual(result.workflow["steps"][0]["step_id"], "review_source_notes")
        self.assertTrue(result.workflow["generation"]["uncertain_mappings"])
        validation = validator.validate_workflow(result.workflow)
        self.assertEqual(validation.errors, [])

    def test_toml_output_parses(self) -> None:
        result = mod.generate_artifact(INTENT_EXAMPLE, generated_at="2026-06-11T00:00:00Z")
        payload = tomllib.loads(mod.render_artifact(result.workflow, output_format="toml"))

        self.assertEqual(payload["status"], "draft")
        self.assertTrue(payload["generation"]["review_required"])
        self.assertEqual(payload["steps"][0]["step_id"], "starting_migraine_level")

    def test_cli_writes_json_and_refuses_runtime_directory_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "messages.generated.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    str(INTENT_EXAMPLE),
                    "--output",
                    str(output),
                    "--format",
                    "json",
                    "--generated-at",
                    "2026-06-11T00:00:00Z",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(output.read_text())["status"], "draft")

        blocked_output = RUNTIME_EXAMPLE_DIR / "_generated-should-not-write.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                str(INTENT_EXAMPLE),
                "--output",
                str(blocked_output),
                "--format",
                "json",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("refusing to write", proc.stderr)
        self.assertFalse(blocked_output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
