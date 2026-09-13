from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_gitignore.py"


class AuditGitignoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        subprocess.run(["git", "init", "--quiet", str(self.repo)], check=True)

        self.global_ignore = self.repo.parent / f"{self.repo.name}-global-ignore"
        self.global_ignore.write_text("*.bak\nnode_modules/\n", encoding="utf-8")
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "config",
                "core.excludesFile",
                str(self.global_ignore),
            ],
            check=True,
        )

        (self.repo / ".gitignore").write_text("*.bak\n/build/\n", encoding="utf-8")
        (self.repo / "snapshot.bak").write_text("backup\n", encoding="utf-8")
        (self.repo / "build").mkdir()
        (self.repo / "build" / "artifact.bin").write_text("artifact\n", encoding="utf-8")
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "add",
                "--force",
                ".gitignore",
                "snapshot.bak",
                "build/artifact.bin",
            ],
            check=True,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        self.global_ignore.unlink(missing_ok=True)

    def audit(self) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_reports_tracked_ignored_paths_with_winning_rules(self) -> None:
        report = self.audit()
        ignored = {entry["path"]: entry for entry in report["tracked_ignored"]}

        self.assertEqual({"build/artifact.bin", "snapshot.bak"}, set(ignored))
        self.assertEqual("*.bak", ignored["snapshot.bak"]["pattern"])
        self.assertEqual("/build/", ignored["build/artifact.bin"]["pattern"])
        self.assertTrue(ignored["snapshot.bak"]["worktree_present"])

    def test_reports_exact_repo_global_overlap_as_candidate(self) -> None:
        report = self.audit()
        overlaps = report["exact_overlaps"]

        self.assertEqual(1, len(overlaps))
        self.assertEqual(".gitignore", overlaps[0]["file"])
        self.assertEqual("*.bak", overlaps[0]["pattern"])
        self.assertEqual([1], overlaps[0]["global_lines"])


if __name__ == "__main__":
    unittest.main()
