"""Regression tests for reportctl_config: schema v1 -> v2 migration and the two
anti-false-green config rules.

Every test here exists because a real defect was observed:

* the live operator config at ~/.config/delonet-daily-report/report.json was
  still schema v1, `reportctl validate` answered only "unknown keys: daily,
  inference, topics", and no v1 -> v2 converter existed anywhere in scripts/
  (adversarial finding 12);
* a config may not declare a section required while disabled, and at least one
  enabled section must be required -- without both, "every required section
  completed" is vacuously true and an empty run reports complete.
"""

from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_fixtures import config as v2_config

reportctl_config = importlib.import_module("reportctl_config")
ConfigError = importlib.import_module("reportctl_contracts").ConfigError

MODULE_PATH = Path(reportctl_config.__file__).resolve()

# The shape of the real July v1 file, verbatim in structure.
LIVE_V1 = {
    "version": 1,
    "timezone": "America/New_York",
    "inference": {"provider": "openai-codex", "model": "gpt-5.4"},
    "artifact_dir": "/home/delorenj/.local/state/delonet-daily-report/artifacts",
    "archive_dir": "/home/delorenj/.local/state/delonet-daily-report/archive",
    "max_age_hours": 24,
    "core_sections": [
        {"id": "executive-brief", "title": "Executive Brief", "required": True},
        {"id": "key-changes", "title": "Key Changes", "required": True},
        {"id": "risks-watchlist", "title": "Risks and Watchlist", "required": True},
        {"id": "coverage-freshness", "title": "Coverage and Freshness", "required": True},
    ],
    "daily": {
        "enabled": False,
        "schedule": "0 7 * * *",
        "deliver": "local",
        "workdir": "/home/delorenj/code/agent-hm-delonet-company-reporter",
        "script": "ddr-daily-input.py",
    },
    "topics": [
        {
            "id": "nightly-pr-maintenance",
            "title": "Nightly PR Maintenance",
            "prompt": "...",
            "schedule": "30 5 * * *",
            "enabled": False,
            "sources": ["https://github.com/delorenj/pr-crusher"],
            "secret_env": [],
            "script": "ddr-journal-nightly-pr-maintenance.py",
        },
        {
            "id": "hermes-fleet-health",
            "title": "Hermes Fleet Health",
            "prompt": "...",
            "schedule": "50 5 * * *",
            "enabled": False,
            "sources": ["https://github.com/NousResearch/hermes-agent"],
            "secret_env": [],
            "script": "ddr-journal-hermes-fleet-health.py",
        },
        {
            "id": "report-delivery-health",
            "title": "Daily Report and Delivery Health",
            "prompt": "...",
            "schedule": "10 6 * * *",
            "enabled": False,
            "sources": ["https://github.com/delorenj/skillex"],
            "secret_env": [],
            "script": "ddr-journal-report-delivery-health.py",
        },
    ],
}
ROOTS = ["/home/delorenj/code/33GOD", "/home/delorenj/code/intelliforia"]


class MigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.v1 = copy.deepcopy(LIVE_V1)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def migrate(self, **kwargs):
        kwargs.setdefault("project_roots", ROOTS)
        return reportctl_config.migrate_v1_to_v2(self.v1, **kwargs)

    def test_v1_config_is_rejected_with_the_migration_command(self) -> None:
        """The old message ('unknown keys: daily, inference, topics') was true and useless."""
        with self.assertRaises(ConfigError) as caught:
            reportctl_config.validate_config(copy.deepcopy(self.v1))
        message = str(caught.exception)
        self.assertIn("schema v1", message)
        self.assertIn("version must be 2", message)
        self.assertIn("migrate --config", message)
        self.assertIn("--project-root", message)
        self.assertIn(str(MODULE_PATH), message)

    def test_a_v2_config_is_never_mistaken_for_v1(self) -> None:
        value = v2_config(self.root)
        self.assertFalse(reportctl_config.is_v1(value))
        self.assertIsNone(reportctl_config.v1_diagnosis(value))
        self.assertEqual(2, reportctl_config.validate_config(value)["version"])

    def test_migration_output_validates_as_v2(self) -> None:
        migrated, notes = self.migrate(enable_all=True)
        self.assertEqual(2, reportctl_config.validate_config(copy.deepcopy(migrated))["version"])
        self.assertEqual(
            ["dev-activity", "fleet-health", "pr-maintenance", "report-delivery"],
            sorted(section["id"] for section in migrated["sections"]),
        )
        self.assertEqual(
            {"enabled": True, "provider": "openai-codex", "model": "gpt-5.4"},
            migrated["narrator"],
        )
        self.assertEqual(ROOTS, migrated["project_roots"])
        self.assertTrue(any("ADDED section dev-activity" in note for note in notes))

    def test_migration_refuses_to_invent_project_roots(self) -> None:
        with self.assertRaisesRegex(ConfigError, "requires at least one --project-root"):
            reportctl_config.migrate_v1_to_v2(self.v1, project_roots=[])
        with self.assertRaisesRegex(ConfigError, "absolute path"):
            reportctl_config.migrate_v1_to_v2(self.v1, project_roots=["code/33GOD"])

    def test_disabled_v1_topics_are_only_kept_disabled_on_request(self) -> None:
        """Faithfully inheriting 'enabled: false' is how you migrate a dead config.

        The live v1 file has all three topics disabled -- the 2026-07-25 shape.
        Carrying that forward by default produced a config that validated,
        reported "migrated": true, and watched one section out of four. The
        operator has to ask for it now, and gets shouted at when they do.
        """
        with self.assertRaisesRegex(ConfigError, "2026-07-25"):
            self.migrate()
        migrated, notes = self.migrate(disabled_topics="preserve")
        states = {s["id"]: (s["enabled"], s["required"]) for s in migrated["sections"]}
        self.assertEqual((False, False), states["pr-maintenance"])
        self.assertEqual((False, False), states["fleet-health"])
        self.assertEqual((False, False), states["report-delivery"])
        self.assertEqual((True, True), states["dev-activity"])
        warnings = [note for note in notes if note.startswith("WARNING")]
        self.assertEqual(3, len(warnings), warnings)

    def test_enable_all_enables_every_migrated_section(self) -> None:
        migrated, _ = self.migrate(enable_all=True)
        self.assertTrue(all(section["enabled"] for section in migrated["sections"]))
        self.assertEqual(
            ["dev-activity", "report-delivery"],
            sorted(s["id"] for s in migrated["sections"] if s["required"]),
        )

    def test_unknown_v1_topic_is_an_error_not_a_silent_drop(self) -> None:
        self.v1["topics"][0]["id"] = "some-topic-nobody-mapped"
        with self.assertRaisesRegex(ConfigError, "has no v2 collector"):
            self.migrate()

    def test_unknown_v1_top_level_key_is_an_error(self) -> None:
        self.v1["surprise"] = 1
        with self.assertRaisesRegex(ConfigError, "unknown keys: surprise"):
            self.migrate()

    def test_migrating_a_v2_config_is_refused(self) -> None:
        with self.assertRaisesRegex(ConfigError, "nothing to migrate"):
            reportctl_config.migrate_v1_to_v2(v2_config(self.root), project_roots=ROOTS)

    def test_migrate_config_file_writes_a_loadable_file(self) -> None:
        source = self.root / "v1.json"
        source.write_text(json.dumps(self.v1), encoding="utf-8")
        destination = self.root / "nested" / "report.json"
        result = reportctl_config.migrate_config_file(
            source, destination, project_roots=ROOTS, enable_all=True
        )
        self.assertTrue(result["migrated"])
        loaded = reportctl_config.load_config(destination)
        self.assertEqual(2, loaded["version"])
        self.assertEqual(self.v1, json.loads(source.read_text(encoding="utf-8")))

    def test_migrate_config_file_refuses_to_clobber(self) -> None:
        source = self.root / "v1.json"
        source.write_text(json.dumps(self.v1), encoding="utf-8")
        destination = self.root / "report.json"
        destination.write_text("keep me", encoding="utf-8")
        with self.assertRaisesRegex(ConfigError, "refusing to overwrite"):
            reportctl_config.migrate_config_file(source, destination, project_roots=ROOTS)
        self.assertEqual("keep me", destination.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ConfigError, "must differ"):
            reportctl_config.migrate_config_file(source, source, project_roots=ROOTS, force=True)

    def test_module_cli_migrates_and_validates(self) -> None:
        source = self.root / "v1.json"
        source.write_text(json.dumps(self.v1), encoding="utf-8")
        destination = self.root / "report.json"
        migrate = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "migrate",
                "--config",
                str(source),
                "--out",
                str(destination),
                "--enable-all",
                "--project-root",
                ROOTS[0],
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, migrate.returncode, migrate.stderr)
        self.assertTrue(json.loads(migrate.stdout)["migrated"])
        check = subprocess.run(
            [sys.executable, str(MODULE_PATH), "validate", "--config", str(destination)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, check.returncode, check.stderr)
        self.assertEqual(2, json.loads(check.stdout)["version"])
        on_v1 = subprocess.run(
            [sys.executable, str(MODULE_PATH), "validate", "--config", str(source)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, on_v1.returncode)
        self.assertIn("schema v1", json.loads(on_v1.stderr)["error"])

    def test_reportctl_validate_passes_on_a_migrated_config(self) -> None:
        """The S1 acceptance criterion, end to end through the operator CLI."""
        source = self.root / "v1.json"
        source.write_text(json.dumps(self.v1), encoding="utf-8")
        destination = self.root / "report.json"
        reportctl_config.migrate_config_file(
            source, destination, project_roots=ROOTS, enable_all=True
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH.parent / "reportctl"),
                "--config",
                str(destination),
                "validate",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["valid"])


class FalseGreenConfigRuleTests(unittest.TestCase):
    """The two rules that keep 'every required section completed' from being vacuous."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.value = v2_config(Path(self.temporary.name))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_required_section_may_not_be_disabled(self) -> None:
        for index, section in enumerate(self.value["sections"]):
            if not section["required"]:
                continue
            invalid = copy.deepcopy(self.value)
            invalid["sections"][index]["enabled"] = False
            with self.assertRaisesRegex(ConfigError, "required while disabled"):
                reportctl_config.validate_config(invalid)

    def test_a_config_that_requires_nothing_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.value)
        for section in invalid["sections"]:
            section["required"] = False
        with self.assertRaisesRegex(ConfigError, "vacuously true"):
            reportctl_config.validate_config(invalid)

    def test_a_config_with_every_section_disabled_is_rejected(self) -> None:
        """The 2026-07-25 shape: 'All topics enabled: false' must not be loadable."""
        invalid = copy.deepcopy(self.value)
        for section in invalid["sections"]:
            section["enabled"] = False
            section["required"] = False
        with self.assertRaisesRegex(ConfigError, "vacuously true"):
            reportctl_config.validate_config(invalid)

    def test_migration_output_can_never_violate_either_rule(self) -> None:
        for intent in ("preserve", "enable"):
            migrated, _ = reportctl_config.migrate_v1_to_v2(
                copy.deepcopy(LIVE_V1), project_roots=ROOTS, disabled_topics=intent
            )
            for section in migrated["sections"]:
                self.assertFalse(
                    section["required"] and not section["enabled"],
                    f"{section['id']} migrated required-while-disabled",
                )
            self.assertTrue(
                any(s["enabled"] and s["required"] for s in migrated["sections"]),
                "migration produced a config that requires nothing",
            )

    def test_save_config_enforces_the_rules_before_writing(self) -> None:
        path = Path(self.temporary.name) / "report.json"
        reportctl_config.save_config(path, copy.deepcopy(self.value))
        before = path.read_bytes()
        broken = copy.deepcopy(self.value)
        for section in broken["sections"]:
            section["required"] = False
        with self.assertRaisesRegex(ConfigError, "vacuously true"):
            reportctl_config.save_config(path, broken)
        self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
