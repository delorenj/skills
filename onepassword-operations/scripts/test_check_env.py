"""Synthetic, credential-free checks for the name-only environment checker."""

import os
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).with_name("check-env.py")
SENTINEL = "synthetic-secret-never-print"


class CheckEnvironmentTests(unittest.TestCase):
    def invoke(self, *names, env=None):
        child = dict(os.environ)
        child.update(env or {})
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *names],
            capture_output=True, text=True, env=child, check=False,
        )
        self.assertNotIn(SENTINEL, result.stdout + result.stderr)
        return result

    def test_present_names_only(self):
        result = self.invoke("APP_SECRET", "ANOTHER", env={"APP_SECRET": SENTINEL, "ANOTHER": "1"})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "environment check passed: 2 required names present\n")
        self.assertEqual(result.stderr, "")

    def test_missing_and_blank_are_aggregated(self):
        result = self.invoke("APP_SECRET", "MISSING", "BLANK", env={"APP_SECRET": SENTINEL, "BLANK": "  "})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "environment check failed: 2 of 3 required names absent or empty\n")

    def test_duplicate_names_do_not_change_count(self):
        result = self.invoke("APP_SECRET", "APP_SECRET", env={"APP_SECRET": SENTINEL})
        self.assertEqual(result.returncode, 0)
        self.assertIn("1 required names", result.stdout)

    def test_bad_names_and_no_arguments_do_not_leak(self):
        for names in ((), ("APP_SECRET", "bad=name"), (SENTINEL,)):
            with self.subTest(names=names):
                result = self.invoke(*names, env={"APP_SECRET": SENTINEL})
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("usage:", result.stderr)

    def test_unresolved_reference_is_rejected(self):
        for value in ("op://example/item/field", "postgres://u:op://example/item/password@db/app"):
            result = self.invoke("APP_SECRET", env={"APP_SECRET": value})
            self.assertEqual(result.returncode, 1)
            self.assertIn("unresolved references", result.stderr)
            self.assertNotIn(value, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
