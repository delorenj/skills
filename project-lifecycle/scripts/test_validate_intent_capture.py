#!/usr/bin/env python3
"""Verifier for validate_intent_capture.py (PLC-E3-S1 / CAF-122)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "validate_intent_capture.py"
EXAMPLE = SCRIPTS_DIR.parents[2] / "workflow-artifacts" / "examples" / "messages-intent-capture.json"

spec = importlib.util.spec_from_file_location("validate_intent_capture", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class IntentCaptureValidationTests(unittest.TestCase):
    def test_messages_example_is_valid(self) -> None:
        payload = json.loads(EXAMPLE.read_text())
        result = mod.validate_capture(payload)
        self.assertEqual(result.errors, [])

    def test_missing_top_level_keys_rejected(self) -> None:
        result = mod.validate_capture({"intent_id": "x"})
        self.assertTrue(any("missing top-level keys" in error for error in result.errors))

    def test_step_requires_mapping_or_note_target(self) -> None:
        payload = json.loads(EXAMPLE.read_text())
        payload["steps"][0]["answer"].pop("field_id", None)
        payload["steps"][0]["answer"].pop("mapped_field", None)
        result = mod.validate_capture(payload)
        self.assertTrue(any("must declare field_id" in error for error in result.errors))

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
            handle.write(json.dumps({"intent_id": "bad"}))
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
