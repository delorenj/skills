"""The project's identity comes from pjangler's canonical `project_id`.

`pj migrate` (PJAN-137) replaced `project_slug` with `project_id` in migrated
manifests; reading only the legacy field stopped James Brennan's nightly report
on 2026-10-07 with "project_slug None is not a lowercase slug".
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import config  # noqa: E402
from ar.common import ConfigError  # noqa: E402


def write_manifest(root: str, **fields) -> str:
    manifest = {"project_name": "Example", "repo_path": root, **fields}
    with open(os.path.join(root, ".project.json"), "w") as fh:
        json.dump(manifest, fh)
    return root


class IdentityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_a_migrated_manifest_resolves_by_project_id(self):
        root = write_manifest(self.tmp.name, project_id="james-brennan")
        project = config.load_project(cwd=root)
        self.assertEqual(project.slug, "james-brennan")

    def test_the_slug_passed_on_the_command_line_matches_project_id(self):
        root = write_manifest(self.tmp.name, project_id="james-brennan")
        self.assertEqual(config.load_project("james-brennan", cwd=root).slug, "james-brennan")

    def test_a_legacy_manifest_still_resolves_by_project_slug(self):
        root = write_manifest(self.tmp.name, project_slug="old-project")
        self.assertEqual(config.load_project(cwd=root).slug, "old-project")

    def test_project_id_wins_when_both_are_present(self):
        root = write_manifest(self.tmp.name, project_id="new-name", project_slug="old-name")
        self.assertEqual(config.load_project(cwd=root).slug, "new-name")

    def test_a_manifest_with_no_identity_is_still_refused(self):
        root = write_manifest(self.tmp.name)
        with mock.patch.object(config, "_pjangler_repo_path", return_value=root):
            with self.assertRaises(ConfigError):
                config.load_project(cwd=root)


if __name__ == "__main__":
    unittest.main()
