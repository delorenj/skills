#!/usr/bin/env python3
"""Verifier for validate_workflow_artifacts.py (PLC-E3-S2 / CAF-123)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "validate_workflow_artifacts.py"
EXAMPLE = SCRIPTS_DIR.parents[2] / "workflow-artifacts" / "workflow-examples" / "messages-workflow.v1.json"

spec = importlib.util.spec_from_file_location("validate_workflow_artifacts", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class WorkflowArtifactValidationTests(unittest.TestCase):
    def test_messages_workflow_example_is_valid(self) -> None:
        payload = json.loads(EXAMPLE.read_text())
        result = mod.validate_workflow(payload)
        self.assertEqual(result.errors, [])

    def test_missing_top_level_keys_rejected(self) -> None:
        result = mod.validate_workflow({"workflow_id": "x"})
        self.assertTrue(any("missing top-level keys" in error for error in result.errors))

    def test_step_field_must_exist(self) -> None:
        payload = json.loads(EXAMPLE.read_text())
        payload["steps"][0]["field_id"] = "not_declared"
        result = mod.validate_workflow(payload)
        self.assertTrue(any("must reference a declared field" in error for error in result.errors))

    def test_transition_target_must_exist(self) -> None:
        payload = json.loads(EXAMPLE.read_text())
        payload["steps"][0]["transitions"][0]["target"] = "missing_step"
        result = mod.validate_workflow(payload)
        self.assertTrue(any("unknown step" in error for error in result.errors))

    def test_rating_requires_bounds_and_gate(self) -> None:
        payload = json.loads(EXAMPLE.read_text())
        payload["steps"][0]["answer"].pop("rating_max")
        payload["steps"][0]["completion_gate"]["rating_required"] = False
        result = mod.validate_workflow(payload)
        self.assertTrue(any("rating_min 0 and rating_max 10" in error for error in result.errors))
        self.assertTrue(any("rating_required must be true" in error for error in result.errors))

    def test_cli_validates_default_examples(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(MODULE_PATH)],
            cwd=SCRIPTS_DIR.parents[2],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("validated", proc.stdout)

    def test_cli_rejects_invalid_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write(json.dumps({"workflow_id": "bad"}))
            path = handle.name
        proc = subprocess.run(
            [sys.executable, str(MODULE_PATH), path],
            cwd=SCRIPTS_DIR.parents[2],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("missing top-level keys", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
