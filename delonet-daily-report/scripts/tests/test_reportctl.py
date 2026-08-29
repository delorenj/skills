from __future__ import annotations

import copy
import datetime as dt
import importlib
import importlib.machinery
import importlib.util
import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config, local_artifact, manifest, report, sourced_artifact

SCRIPT = Path(__file__).parents[1] / "reportctl"
LOADER = importlib.machinery.SourceFileLoader("reportctl", str(SCRIPT))
SPEC = importlib.util.spec_from_loader("reportctl", LOADER)
reportctl = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(reportctl)
reportctl_runtime = importlib.import_module("reportctl_runtime")
reportctl_contracts = importlib.import_module("reportctl_contracts")


class ConfigV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate(self, value: dict) -> dict:
        return importlib.import_module("reportctl_config").validate_config(value)

    def test_valid_v2_config_round_trips(self) -> None:
        self.assertEqual(2, self.validate(copy.deepcopy(self.value))["version"])

    def test_version_one_config_is_rejected(self) -> None:
        legacy = copy.deepcopy(self.value)
        legacy["version"] = 1
        with self.assertRaisesRegex(reportctl.ConfigError, "version must be 2"):
            self.validate(legacy)

    def test_topics_key_is_no_longer_accepted(self) -> None:
        legacy = copy.deepcopy(self.value)
        legacy["topics"] = []
        with self.assertRaisesRegex(reportctl.ConfigError, "unknown keys: topics"):
            self.validate(legacy)

    def test_duplicate_and_malformed_section_ids_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["sections"].append(copy.deepcopy(invalid["sections"][0]))
        with self.assertRaisesRegex(reportctl.ConfigError, "duplicate section id"):
            self.validate(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["sections"][0]["id"] = "Dev_Activity"
        with self.assertRaisesRegex(reportctl.ConfigError, "kebab-case"):
            self.validate(invalid)

    def test_collector_must_be_a_module_name(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["sections"][0]["collector"] = "../etc/passwd"
        with self.assertRaisesRegex(reportctl.ConfigError, "module name"):
            self.validate(invalid)

    def test_required_section_cannot_be_disabled(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["sections"][0]["enabled"] = False
        with self.assertRaisesRegex(reportctl.ConfigError, "required while disabled"):
            self.validate(invalid)

    def test_config_without_any_required_enabled_section_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.value)
        for section in invalid["sections"]:
            section["required"] = False
        with self.assertRaisesRegex(reportctl.ConfigError, "vacuously true"):
            self.validate(invalid)

    def test_timezone_must_be_a_real_zone(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["timezone"] = "Mars/Olympus"
        with self.assertRaisesRegex(reportctl.ConfigError, "valid IANA zone"):
            self.validate(invalid)
        other = copy.deepcopy(self.value)
        other["timezone"] = "UTC"
        self.assertEqual("UTC", self.validate(other)["timezone"])

    def test_project_roots_must_be_absolute_and_unique(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["project_roots"] = ["code/33GOD"]
        with self.assertRaisesRegex(reportctl.ConfigError, "absolute path"):
            self.validate(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["project_roots"] = ["/a", "/a"]
        with self.assertRaisesRegex(reportctl.ConfigError, "duplicate project root"):
            self.validate(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["project_roots"] = []
        with self.assertRaisesRegex(reportctl.ConfigError, "non-empty array"):
            self.validate(invalid)

    def test_narrator_block_is_strict(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["narrator"] = {"enabled": True, "provider": "openai-codex"}
        with self.assertRaisesRegex(reportctl.ConfigError, "missing keys: model"):
            self.validate(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["narrator"]["enabled"] = "yes"
        with self.assertRaisesRegex(reportctl.ConfigError, "narrator.enabled must be boolean"):
            self.validate(invalid)

    def test_options_reject_nested_structures(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["sections"][0]["options"] = {"nested": {"deep": 1}}
        with self.assertRaisesRegex(reportctl.ConfigError, "must be a string, number"):
            self.validate(invalid)

    def test_core_sections_still_require_shipped_defaults(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["core_sections"] = invalid["core_sections"][:-1]
        with self.assertRaisesRegex(reportctl.ConfigError, "coverage-freshness"):
            self.validate(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["core_sections"] = [invalid["core_sections"][-1]]
        with self.assertRaisesRegex(reportctl.ConfigError, "shipped defaults"):
            self.validate(invalid)

    def test_save_config_validates_before_replacing(self) -> None:
        module = importlib.import_module("reportctl_config")
        path = self.root / "report.json"
        module.save_config(path, copy.deepcopy(self.value))
        before = path.read_bytes()
        broken = copy.deepcopy(self.value)
        broken["version"] = 3
        with self.assertRaises(reportctl.ConfigError):
            module.save_config(path, broken)
        self.assertEqual(before, path.read_bytes())

    def test_shipped_example_config_validates(self) -> None:
        example = SCRIPT.parents[1] / "assets" / "example-config.v2.json"
        loaded = self.validate(json.loads(example.read_text(encoding="utf-8")))
        self.assertEqual(
            ["dev-activity", "fleet-health", "pr-maintenance", "report-delivery"],
            [section["id"] for section in loaded["sections"]],
        )
        self.assertEqual(
            ["dev-activity", "report-delivery"],
            reportctl_contracts.required_section_ids(loaded),
        )


class SectionArtifactV2Tests(unittest.TestCase):
    def validate(self, artifact: dict, section_id: str = "dev-activity") -> dict:
        return reportctl_contracts.validate_section_artifact(artifact, section_id)

    def test_local_artifact_without_findings_or_sources_is_valid(self) -> None:
        self.assertEqual(
            "complete", self.validate(local_artifact("2099-01-01T00:00:00Z"))["status"]
        )

    def test_sourced_artifact_is_still_valid(self) -> None:
        self.assertEqual(
            "complete", self.validate(sourced_artifact("2099-01-01T00:00:00Z"))["status"]
        )

    def test_schema_version_one_is_rejected(self) -> None:
        artifact = local_artifact("2099-01-01T00:00:00Z")
        artifact["schema_version"] = 1
        with self.assertRaisesRegex(reportctl.ConfigError, "schema_version must be 2"):
            self.validate(artifact)

    def test_non_complete_status_requires_a_reason(self) -> None:
        for status in ("partial", "stale", "failed"):
            artifact = local_artifact("2099-01-01T00:00:00Z")
            artifact["status"] = status
            with self.assertRaisesRegex(reportctl.ConfigError, "requires a non-empty reason"):
                self.validate(artifact)
            artifact["reason"] = "Candystore was unreachable."
            self.assertEqual(status, self.validate(artifact)["status"])

    def test_metrics_must_be_a_flat_scalar_map(self) -> None:
        artifact = local_artifact("2099-01-01T00:00:00Z")
        artifact["metrics"] = {"nested": {"a": 1}}
        with self.assertRaisesRegex(reportctl.ConfigError, "string, number, or boolean"):
            self.validate(artifact)
        artifact["metrics"] = {"": 1}
        with self.assertRaisesRegex(reportctl.ConfigError, "keys must be non-empty"):
            self.validate(artifact)

    def test_detail_must_be_strings(self) -> None:
        artifact = local_artifact("2099-01-01T00:00:00Z")
        artifact["detail"] = ["ok", 3]
        with self.assertRaisesRegex(reportctl.ConfigError, "array of strings"):
            self.validate(artifact)

    def test_unknown_keys_are_still_rejected(self) -> None:
        artifact = local_artifact("2099-01-01T00:00:00Z")
        artifact["extra"] = True
        with self.assertRaisesRegex(reportctl.ConfigError, "contract mismatch"):
            self.validate(artifact)

    def test_evidence_urls_must_be_public_https(self) -> None:
        artifact = sourced_artifact("2099-01-01T00:00:00Z")
        artifact["sources"][0]["url"] = "http://example.org/release"
        with self.assertRaisesRegex(reportctl.ConfigError, "sources\\[0\\] is invalid"):
            self.validate(artifact)
        artifact = sourced_artifact("2099-01-01T00:00:00Z")
        artifact["findings"][0]["source_urls"] = ["https://user@example.org/release"]
        with self.assertRaisesRegex(reportctl.ConfigError, "findings\\[0\\] is invalid"):
            self.validate(artifact)


class ArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)
        self.path = self.root / "report.json"
        self.path.write_text(json.dumps(self.value), encoding="utf-8")
        manifest_path = Path(self.value["artifact_dir"]) / "2026-08-17" / "run-manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(manifest()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SCRIPT), "--config", str(self.path), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_section(self, section_id: str, artifact: dict) -> Path:
        path = Path(reportctl.section_path(self.value, section_id, "2026-08-17"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact), encoding="utf-8")
        return path

    def archive(self, title: str, degraded: list | None = None) -> dict:
        report_file = self.root / f"{title}.json"
        markdown_file = self.root / f"{title}.md"
        report_file.write_text(json.dumps(report(self.value, title, degraded)), encoding="utf-8")
        markdown_file.write_text(f"# {title}\n", encoding="utf-8")
        return reportctl.archive_report(self.value, str(report_file), str(markdown_file))

    def test_archive_paths_are_partitioned(self) -> None:
        paths = reportctl.archive_paths(self.value, "2026-08-17")
        self.assertTrue(paths["archive_root"].endswith("/2026/08/2026-08-17"))
        self.assertTrue(paths["commit_marker"].endswith("/current.json"))
        self.assertTrue(paths["manifest"].endswith("/2026-08-17/run-manifest.json"))

    def test_archive_writes_validated_json_and_markdown_atomically(self) -> None:
        output = self.archive("Daily Developer Report")
        self.assertEqual("# Daily Developer Report\n", Path(output["markdown"]).read_text())
        archived = json.loads(Path(output["report_json"]).read_text())
        self.assertEqual("report.md", archived["markdown_path"])
        self.assertTrue(Path(output["commit_marker"]).exists())
        self.assertEqual("run-1", json.loads(Path(output["manifest"]).read_text())["run_id"])

    def test_archive_requires_matching_manifest_identity(self) -> None:
        manifest_path = Path(self.value["artifact_dir"]) / "2026-08-17" / "run-manifest.json"
        drifted = manifest()
        drifted["run_id"] = "different"
        manifest_path.write_text(json.dumps(drifted))
        with self.assertRaisesRegex(reportctl.ConfigError, "match exactly"):
            self.archive("Mismatch")

    def test_archive_rejects_empty_markdown(self) -> None:
        report_file, markdown_file = self.root / "e.json", self.root / "e.md"
        report_file.write_text(json.dumps(report(self.value)))
        markdown_file.write_text("   \n")
        with self.assertRaisesRegex(reportctl.ConfigError, "non-empty"):
            reportctl.archive_report(self.value, str(report_file), str(markdown_file))

    def test_archive_concurrency_keeps_pair_consistent(self) -> None:
        errors: list[Exception] = []

        def worker(title: str) -> None:
            try:
                self.archive(title)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(title,)) for title in ("Alpha", "Beta")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual([], errors)
        paths = reportctl.archive_paths(self.value, "2026-08-17")
        marker = json.loads(Path(paths["commit_marker"]).read_text())
        root = Path(paths["archive_root"]) / "generations" / marker["generation"]
        self.assertIn(json.loads((root / "report.json").read_text())["title"],
                      (root / "report.md").read_text())

    def test_archive_second_commit_failure_never_publishes_marker(self) -> None:
        first = self.archive("Old")
        old_marker = json.loads(Path(first["commit_marker"]).read_text())
        original = reportctl_runtime.os.replace

        def fail_pointer(source, destination):
            if str(destination).endswith("current.json"):
                raise OSError("forced pointer failure")
            return original(source, destination)

        with mock.patch.object(reportctl_runtime.os, "replace", side_effect=fail_pointer):
            with self.assertRaises(OSError):
                self.archive("Failure")
        paths = reportctl.archive_paths(self.value, "2026-08-17")
        self.assertEqual(old_marker, json.loads(Path(paths["commit_marker"]).read_text()))
        old_root = Path(paths["archive_root"]) / "generations" / old_marker["generation"]
        self.assertEqual("# Old\n", (old_root / "report.md").read_text())

    def test_artifact_health_reports_missing_stale_and_invalid(self) -> None:
        health = {item["id"]: item for item in reportctl.artifact_health(self.value, "2026-08-17")}
        self.assertEqual("missing", health["dev-activity"]["status"])
        self.assertEqual("missing", health["fleet-health"]["status"])
        self.write_section("dev-activity", local_artifact("2000-01-01T00:00:00Z"))
        self.write_section("fleet-health", {"schema_version": 2, "broken": True})
        health = {item["id"]: item for item in reportctl.artifact_health(self.value, "2026-08-17")}
        self.assertEqual("stale", health["dev-activity"]["status"])
        self.assertEqual("invalid", health["fleet-health"]["status"])

    def test_artifact_health_never_drops_a_disabled_section_silently(self) -> None:
        paused = copy.deepcopy(self.value)
        paused["sections"][1]["enabled"] = False
        ids = [item["id"] for item in reportctl.artifact_health(paused, "2026-08-17")]
        self.assertEqual(["dev-activity"], ids)
        with self.assertRaisesRegex(reportctl.ConfigError, "YYYY-MM-DD"):
            reportctl.artifact_health(self.value, "../../etc")

    def test_manifest_and_report_cover_enabled_sections_exactly(self) -> None:
        value = manifest()
        self.assertEqual(value, reportctl_contracts.validate_run_manifest(value, self.value))
        duplicate = copy.deepcopy(value)
        duplicate["sections"].append(copy.deepcopy(duplicate["sections"][0]))
        with self.assertRaisesRegex(reportctl.ConfigError, "exactly once"):
            reportctl_contracts.validate_run_manifest(duplicate, self.value)
        bad = report(self.value)
        bad["coverage"] = {"complete": ["dev-activity"], "degraded": ["dev-activity"]}
        with self.assertRaisesRegex(reportctl.ConfigError, "partition"):
            reportctl_contracts.validate_daily_report(bad, self.value)


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)
        self.path = self.root / "report.json"
        self.path.write_text(json.dumps(self.value), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SCRIPT), "--config", str(self.path), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validate_exits_zero(self) -> None:
        result = self.run_cli("validate")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_removed_cron_subcommands_are_gone(self) -> None:
        for command in ("plan", "reconcile", "health", "topic"):
            result = self.run_cli(command)
            self.assertEqual(2, result.returncode)
            self.assertIn("invalid choice", result.stderr)

    def test_paths_and_status_are_wired(self) -> None:
        paths = self.run_cli("paths", "--date", "2026-08-17")
        self.assertEqual(0, paths.returncode, paths.stderr)
        self.assertTrue(json.loads(paths.stdout)["archive_root"].endswith("2026-08-17"))
        status = self.run_cli("status", "--date", "2026-08-17")
        self.assertEqual(0, status.returncode, status.stderr)
        body = json.loads(status.stdout)
        self.assertFalse(body["healthy"])
        self.assertEqual("failed", body["derived_status"])

    def use_absent_collectors(self) -> None:
        """Point both sections at modules that do not exist.

        The shipped collectors read the live machine; a unit test must not.
        An absent module is also the honest worst case: it proves a broken
        collector degrades the run instead of crashing or vanishing from it.
        """
        broken = copy.deepcopy(self.value)
        for index, section in enumerate(broken["sections"]):
            section["collector"] = f"definitely_absent_{index}"
        self.path.write_text(json.dumps(broken), encoding="utf-8")

    def test_collect_degrades_when_a_collector_module_is_absent(self) -> None:
        self.use_absent_collectors()
        result = self.run_cli("collect", "--date", "2026-08-17")
        self.assertEqual(3, result.returncode, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(
            ["dev-activity", "fleet-health"], [item["id"] for item in body["sections"]]
        )
        for item in body["sections"]:
            self.assertEqual("failed", item["status"])
            self.assertIn("ModuleNotFoundError", item["reason"])
            written = json.loads(Path(item["path"]).read_text())
            self.assertEqual("failed", written["status"])
            self.assertTrue(written["reason"])

    def test_run_publishes_an_honest_failure_and_exits_non_zero(self) -> None:
        self.use_absent_collectors()
        result = self.run_cli(
            "run", "--date", "2026-08-17", "--no-emit", "--no-mirror", "--no-narrate"
        )
        self.assertEqual(3, result.returncode, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual("failed", body["status"])
        self.assertEqual(
            {"dev-activity": "failed", "fleet-health": "failed"},
            body["manifest"]["sections"],
        )
        # The failed run is still published, and it is still verifiable.
        self.assertTrue(body["published"]["verified"], body["published"]["problems"])
        markdown = Path(body["published"]["markdown"]).read_text()
        self.assertIn("failed", markdown)
        # verify refuses a published report in which nothing succeeded.
        gate = self.run_cli("verify", "--date", "2026-08-17")
        self.assertEqual(3, gate.returncode)
        self.assertTrue(
            any("no section completed" in item for item in json.loads(gate.stdout)["problems"])
        )

    def test_collect_rejects_unknown_sections(self) -> None:
        result = self.run_cli("collect", "--date", "2026-08-17", "--section", "nope")
        self.assertEqual(2, result.returncode)
        self.assertIn("unknown section", result.stderr)

    def test_verify_exits_non_zero_when_nothing_is_published(self) -> None:
        result = self.run_cli("verify", "--date", "2026-08-17")
        self.assertEqual(3, result.returncode)
        body = json.loads(result.stdout)
        self.assertFalse(body["ok"])
        self.assertIn("no published report", body["problems"][0])

    def test_bad_config_path_is_an_error_not_a_success(self) -> None:
        result = self.run_cli("validate", )
        self.assertEqual(0, result.returncode)
        missing = subprocess.run(
            [str(SCRIPT), "--config", str(self.root / "absent.json"), "validate"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, missing.returncode)
        self.assertIn("cannot read JSON", missing.stderr)


class RunCommandTests(unittest.TestCase):
    def test_subprocess_failures_are_structured(self) -> None:
        with mock.patch.object(
            reportctl_runtime.subprocess, "run", side_effect=FileNotFoundError()
        ):
            with self.assertRaisesRegex(reportctl.ConfigError, "missing executable"):
                reportctl_runtime.run_command(["git"])
        with mock.patch.object(
            reportctl_runtime.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 30)
        ):
            with self.assertRaisesRegex(reportctl.ConfigError, "timed out"):
                reportctl_runtime.run_command(["git"])
        error = subprocess.CalledProcessError(9, ["git"], stderr="x" * 5000)
        with mock.patch.object(reportctl_runtime.subprocess, "run", side_effect=error):
            with self.assertRaises(reportctl.ConfigError) as raised:
                reportctl_runtime.run_command(["git"])
        message = str(raised.exception)
        self.assertIn("exit 9", message)
        self.assertLess(len(message), 700)

    def test_run_command_succeeds_for_a_real_command(self) -> None:
        completed = reportctl_runtime.run_command(["true"])
        self.assertEqual(0, completed.returncode)


class DateDefaultTests(unittest.TestCase):
    def test_default_date_is_yesterday(self) -> None:
        cli = importlib.import_module("reportctl_cli")
        self.assertEqual(
            (dt.date.today() - dt.timedelta(days=1)).isoformat(), cli.default_date()
        )


if __name__ == "__main__":
    unittest.main()
