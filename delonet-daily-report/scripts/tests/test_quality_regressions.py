"""Regressions for the failure this package exists to prevent.

On 2026-08-18 a scheduled job logged "completed successfully" over a command
that exited 2, and the event it emitted hardcoded ``outcome.status="complete"``
on every run. Every test here asserts that some status is *derived* rather than
assumed, or that a gap is *recorded* rather than dropped.
"""

from __future__ import annotations

import copy
import importlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config, local_artifact, manifest, report
from test_reportctl import SCRIPT, reportctl, reportctl_contracts, reportctl_runtime

base = importlib.import_module("collectors.base")


class DerivedStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_complete_requires_every_required_section(self) -> None:
        self.assertEqual(
            "complete",
            reportctl.derive_status(
                self.value, {"dev-activity": "complete", "fleet-health": "complete"}
            ),
        )

    def test_optional_section_failure_degrades_the_report_to_partial(self) -> None:
        # Spec rule: "Non-required sections that fail degrade the report to
        # partial but never to failed." A run that lost a configured section is
        # missing information, so it may not call itself complete -- that is the
        # quiet form of the false-green this package exists to prevent.
        self.assertEqual(
            "partial",
            reportctl.derive_status(
                self.value, {"dev-activity": "complete", "fleet-health": "failed"}
            ),
        )

    def test_an_optional_section_that_never_ran_is_partial_not_complete(self) -> None:
        for status in ("missing", "invalid", "stale", "partial"):
            with self.subTest(status=status):
                self.assertEqual(
                    "partial",
                    reportctl.derive_status(
                        self.value, {"dev-activity": "complete", "fleet-health": status}
                    ),
                )

    def test_required_section_failure_fails_the_run(self) -> None:
        # Changed deliberately on 2026-08-18. This used to assert "partial", and
        # "partial" exits 0 -- so with Candystore down the required dev-activity
        # section died and a cron agent recorded success over the run. A section
        # the operator declared required is one the report cannot be the report
        # without, so losing it fails the run and the exit code says so.
        self.assertEqual(
            "failed",
            reportctl.derive_status(
                self.value, {"dev-activity": "failed", "fleet-health": "complete"}
            ),
        )
        # The trigger is "did not run", not "is not complete". Every status here
        # means this run holds no usable collection for a required section.
        for status in ("failed", "missing", "invalid", "stale"):
            with self.subTest(status=status):
                self.assertEqual(
                    "failed",
                    reportctl.derive_status(
                        self.value, {"dev-activity": status, "fleet-health": "complete"}
                    ),
                )

    def test_a_required_section_that_ran_partially_is_degraded_not_failed(self) -> None:
        # "partial" is a collector that read some of its sources and said which
        # one it could not read: a degraded report, not an absent one. Failing
        # the run for it is what latched the pipeline shut, because the
        # report-delivery self-check reports its findings through that status.
        # See scripts/tests/test_status_semantics.py.
        self.assertEqual(
            "partial",
            reportctl.derive_status(
                self.value, {"dev-activity": "partial", "fleet-health": "complete"}
            ),
        )

    def test_nothing_succeeded_is_failed(self) -> None:
        self.assertEqual(
            "failed",
            reportctl.derive_status(
                self.value, {"dev-activity": "failed", "fleet-health": "missing"}
            ),
        )

    def test_absent_section_status_counts_as_not_complete(self) -> None:
        # dev-activity is required and has no status at all here, which is the
        # strongest form of "did not complete".
        self.assertEqual("failed", reportctl.derive_status(self.value, {"fleet-health": "complete"}))


class VerifyPublishedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)
        self.path = self.root / "report.json"
        self.path.write_text(json.dumps(self.value), encoding="utf-8")
        self.manifest_path = Path(self.value["artifact_dir"]) / "2026-08-17" / "run-manifest.json"
        self.manifest_path.parent.mkdir(parents=True)
        self.manifest_path.write_text(json.dumps(manifest()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def publish(self, title: str = "Report", degraded: list | None = None) -> dict:
        report_file, markdown_file = self.root / "r.json", self.root / "r.md"
        report_file.write_text(json.dumps(report(self.value, title, degraded)), encoding="utf-8")
        markdown_file.write_text(f"# {title}\n", encoding="utf-8")
        return reportctl.archive_report(self.value, str(report_file), str(markdown_file))

    def test_absent_report_fails_verification(self) -> None:
        outcome = reportctl.verify_published(self.value, "2026-08-17")
        self.assertFalse(outcome["ok"])
        self.assertIn("no published report", outcome["problems"][0])

    def test_published_report_passes_verification(self) -> None:
        self.publish()
        outcome = reportctl.verify_published(self.value, "2026-08-17")
        self.assertTrue(outcome["ok"], outcome["problems"])
        self.assertEqual("complete", outcome["status"])
        self.assertEqual([], outcome["degraded"])

    def test_failed_required_section_publishes_but_the_gate_refuses_it(self) -> None:
        # The generation is written and stays readable -- the failure is on the
        # record, not hidden -- but verification refuses to certify it, and says
        # which required section is missing rather than the generic "no section
        # completed". A gate that passes this is a gate a cron agent walks
        # through while its primary data source is dead.
        self.manifest_path.write_text(
            json.dumps(manifest({"dev-activity": "failed", "fleet-health": "complete"}))
        )
        self.publish(degraded=["dev-activity"])
        outcome = reportctl.verify_published(self.value, "2026-08-17")
        self.assertTrue(outcome["coherent"], outcome["problems"])
        self.assertFalse(outcome["ok"])
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(["dev-activity"], outcome["degraded"])
        self.assertEqual(["dev-activity"], outcome["required_gaps"])
        self.assertTrue(
            any("required section(s) dev-activity" in item for item in outcome["problems"]),
            outcome["problems"],
        )

    def test_optional_failure_is_listed_as_degraded(self) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest({"dev-activity": "complete", "fleet-health": "failed"}))
        )
        self.publish(degraded=["fleet-health"])
        outcome = reportctl.verify_published(self.value, "2026-08-17")
        # The generation is valid and verifiable -- it just does not get to call
        # itself complete while one of its configured sections is missing.
        self.assertTrue(outcome["ok"], outcome["problems"])
        self.assertEqual("partial", outcome["status"])
        self.assertEqual(["fleet-health"], outcome["degraded"])

    def test_corrupt_report_fails_verification(self) -> None:
        output = self.publish()
        Path(output["report_json"]).write_text("{not json")
        outcome = reportctl.verify_published(self.value, "2026-08-17")
        self.assertFalse(outcome["ok"])
        self.assertTrue(any("report.json is invalid" in item for item in outcome["problems"]))

    def test_missing_generation_file_fails_verification(self) -> None:
        output = self.publish()
        Path(output["markdown"]).unlink()
        outcome = reportctl.verify_published(self.value, "2026-08-17")
        self.assertFalse(outcome["ok"])
        self.assertTrue(any("missing report.md" in item for item in outcome["problems"]))

    def test_pointer_for_the_wrong_date_fails_verification(self) -> None:
        self.publish()
        paths = reportctl.archive_paths(self.value, "2026-08-17")
        marker_path = Path(paths["commit_marker"])
        marker = json.loads(marker_path.read_text())
        marker["report_date"] = "2026-08-16"
        marker_path.write_text(json.dumps(marker))
        outcome = reportctl.verify_published(self.value, "2026-08-17")
        self.assertFalse(outcome["ok"])

    def test_require_complete_flag_rejects_an_honest_partial(self) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest({"dev-activity": "complete", "fleet-health": "failed"}))
        )
        self.publish(degraded=["fleet-health"])
        import subprocess

        lenient = subprocess.run(
            [str(SCRIPT), "--config", str(self.path), "verify", "--date", "2026-08-17"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, lenient.returncode, lenient.stderr)
        strict = subprocess.run(
            [str(SCRIPT), "--config", str(self.path), "verify", "--date", "2026-08-17",
             "--require-complete"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(3, strict.returncode)
        self.assertIn("require-complete", json.loads(strict.stdout)["problems"][-1])

    def test_pointer_fsync_failure_retains_referenced_generation(self) -> None:
        first = self.publish("Old")
        old_marker = json.loads(Path(first["commit_marker"]).read_text())
        archive_root = Path(reportctl.archive_paths(self.value, "2026-08-17")["archive_root"])
        original_fsync_dir = reportctl_runtime.fsync_dir

        def fail_after_pointer_replace(path: Path) -> None:
            if Path(path) == archive_root:
                marker = json.loads((archive_root / "current.json").read_text())
                if marker["generation"] != old_marker["generation"]:
                    raise OSError("forced pointer directory fsync failure")
            original_fsync_dir(path)

        with mock.patch.object(
            reportctl_runtime, "fsync_dir", side_effect=fail_after_pointer_replace
        ):
            with self.assertRaisesRegex(OSError, "pointer directory fsync"):
                self.publish("New")
        marker = json.loads((archive_root / "current.json").read_text())
        current = archive_root / "generations" / marker["generation"]
        self.assertNotEqual(old_marker["generation"], marker["generation"])
        self.assertEqual("New", json.loads((current / "report.json").read_text())["title"])


class SectionResultTests(unittest.TestCase):
    def test_to_artifact_produces_a_valid_local_artifact(self) -> None:
        result = base.SectionResult(
            id="dev-activity",
            summary="14 commits across 3 repositories.",
            metrics={"commits": 14},
            detail=["=== 33GOD ==="],
        )
        artifact = result.to_artifact("run-1", 24)
        self.assertEqual(2, artifact["schema_version"])
        self.assertEqual("complete", artifact["status"])
        self.assertNotIn("findings", artifact)
        self.assertNotIn("sources", artifact)
        self.assertEqual({"commits": 14}, artifact["metrics"])

    def test_fresh_until_is_derived_from_max_age(self) -> None:
        result = base.SectionResult(
            id="dev-activity", summary="ok", generated_at="2026-08-17T10:00:00Z"
        )
        artifact = result.to_artifact("run-1", 6)
        self.assertEqual("2026-08-17T16:00:00Z", artifact["fresh_until"])

    def test_non_complete_status_never_ships_without_a_reason(self) -> None:
        artifact = base.SectionResult(id="dev-activity", status="failed", summary="down").to_artifact(
            "run-1", 24
        )
        self.assertEqual("failed", artifact["status"])
        self.assertTrue(artifact["reason"])
        self.assertIn(artifact["reason"], artifact["caveats"])

    def test_unknown_status_degrades_to_failed(self) -> None:
        artifact = base.SectionResult(
            id="dev-activity", status="totally-fine", summary="s"
        ).to_artifact("run-1", 24)
        self.assertEqual("failed", artifact["status"])
        self.assertTrue(any("unknown status" in item for item in artifact["caveats"]))

    def test_empty_summary_is_recorded_not_invented(self) -> None:
        artifact = base.SectionResult(id="dev-activity").to_artifact("run-1", 24)
        self.assertIn("no summary", artifact["summary"])
        self.assertIn("collector produced no summary", artifact["caveats"])

    def test_byte_cap_truncation_is_always_recorded(self) -> None:
        detail = [f"line {index} " + "x" * 200 for index in range(200)]
        artifact = base.SectionResult(
            id="dev-activity", summary="lots", detail=detail
        ).to_artifact("run-1", 24, byte_cap=8_000)
        self.assertLess(len(json.dumps(artifact).encode("utf-8")), 8_001)
        self.assertLess(len(artifact.get("detail", [])), len(detail))
        truncation = [item for item in artifact["caveats"] if "detail truncated" in item]
        self.assertEqual(1, len(truncation))
        self.assertIn(f"of {len(detail)} lines", truncation[0])

    def test_uncapped_result_is_left_alone(self) -> None:
        artifact = base.SectionResult(
            id="dev-activity", summary="small", detail=["a", "b"]
        ).to_artifact("run-1", 24)
        self.assertEqual(["a", "b"], artifact["detail"])
        self.assertEqual([], artifact["caveats"])


class AllowlistTests(unittest.TestCase):
    def test_only_named_keys_survive_at_every_depth(self) -> None:
        payload = {
            "summary": "kept",
            "secret_env": "dropped",
            "sections": [{"summary": "kept", "authorization": "dropped"}],
        }
        bounded = base.allowlist(payload, {"summary", "sections"})
        self.assertEqual(
            {"summary": "kept", "sections": [{"summary": "kept"}]}, bounded
        )

    def test_metric_maps_keep_their_data_keys_but_only_scalar_leaves(self) -> None:
        payload = {"metrics": {"commits": 14, "nested": {"a": 1}}, "drop": 1}
        bounded = base.allowlist(payload, {"metrics"})
        self.assertEqual({"metrics": {"commits": 14}}, bounded)

    def test_allowlist_copies_rather_than_mutating(self) -> None:
        payload = {"summary": "kept", "drop": 1}
        bounded = base.allowlist(payload, {"summary"})
        bounded["summary"] = "changed"
        self.assertEqual("kept", payload["summary"])
        self.assertIn("drop", payload)

    def test_narrator_bound_rejects_oversize_input(self) -> None:
        with self.assertRaisesRegex(reportctl.ConfigError, "exceeds the"):
            base.bound_for_narrator({"summary": "x" * 5_000}, cap=1_000)


class RunCollectorTests(unittest.TestCase):
    def test_exception_becomes_a_failed_result(self) -> None:
        def boom(section):
            raise RuntimeError("candystore unreachable")

        result = base.run_collector(boom, {"id": "dev-activity"})
        self.assertEqual("failed", result.status)
        self.assertIn("candystore unreachable", result.reason)
        self.assertIn("RuntimeError", result.reason)

    def test_missing_module_becomes_a_failed_result_not_a_crash(self) -> None:
        def importer(section):
            importlib.import_module("collectors.definitely_not_here")

        result = base.run_collector(importer, {"id": "fleet-health"})
        self.assertEqual("failed", result.status)
        self.assertIn("ModuleNotFoundError", result.reason)

    def test_wrong_return_type_is_failed(self) -> None:
        result = base.run_collector(lambda section: {"status": "complete"}, {"id": "x"})
        self.assertEqual("failed", result.status)
        self.assertIn("expected SectionResult", result.reason)

    def test_id_mismatch_is_corrected_and_recorded(self) -> None:
        result = base.run_collector(
            lambda section: base.SectionResult(id="wrong", summary="s"), {"id": "dev-activity"}
        )
        self.assertEqual("dev-activity", result.id)
        self.assertTrue(any("wrong" in item for item in result.caveats))

    def test_successful_result_passes_through_unchanged(self) -> None:
        expected = base.SectionResult(id="dev-activity", summary="s")
        self.assertIs(expected, base.run_collector(lambda section: expected, {"id": "dev-activity"}))


class DeletedSurfaceTests(unittest.TestCase):
    def test_retired_modules_are_gone(self) -> None:
        for name in ("reportctl_inference", "reportctl_profile", "reportctl_security"):
            with self.assertRaises(ModuleNotFoundError):
                importlib.import_module(name)
            self.assertFalse((SCRIPT.parent / f"{name}.py").exists())

    def test_no_shipped_module_imports_the_retired_scanner(self) -> None:
        for path in SCRIPT.parent.rglob("*.py"):
            if "tests" in path.parts:
                continue
            self.assertNotIn("reportctl_security", path.read_text(encoding="utf-8"), str(path))
        self.assertNotIn("reportctl_security", SCRIPT.read_text(encoding="utf-8"))

    def test_runtime_no_longer_carries_cron_reconciliation_helpers(self) -> None:
        for name in (
            "hermes_home",
            "profile_config",
            "timezone_state",
            "inference_state",
            "profile_skill_installed",
            "timezone_preflight",
            "daily_next_run_valid",
        ):
            self.assertFalse(hasattr(reportctl_runtime, name), name)

    def test_runtime_keeps_exactly_the_helpers_the_pipeline_needs(self) -> None:
        for name in (
            "archive_paths",
            "fsync_dir",
            "atomic_write",
            "atomic_write_text",
            "file_lock",
            "publish_archive_pair",
            "run_command",
        ):
            self.assertTrue(hasattr(reportctl_runtime, name), name)


class SchemaTests(unittest.TestCase):
    CONTRACTS = Path(__file__).parents[2] / "assets" / "contracts"

    def test_evidence_url_patterns_reject_userinfo_and_queries(self) -> None:
        patterns: list[str] = []

        def collect(value) -> None:
            if isinstance(value, dict):
                if value.get("format") == "uri" and "pattern" in value:
                    patterns.append(value["pattern"])
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        for name in ("section-artifact.schema.json", "daily-report.schema.json"):
            collect(json.loads((self.CONTRACTS / name).read_text()))
        self.assertGreaterEqual(len(patterns), 3)
        for pattern in patterns:
            self.assertIsNotNone(re.fullmatch(pattern, "https://example.org/releases/1"))
            self.assertIsNone(re.fullmatch(pattern, "https://user@example.org/releases/1"))
            self.assertIsNone(re.fullmatch(pattern, "https://example.org/releases/1?token=public"))

    def test_section_artifact_schema_is_v2_and_requires_a_reason(self) -> None:
        schema = json.loads((self.CONTRACTS / "section-artifact.schema.json").read_text())
        self.assertEqual(2, schema["properties"]["schema_version"]["const"])
        self.assertNotIn("findings", schema["required"])
        self.assertNotIn("sources", schema["required"])
        self.assertIn("metrics", schema["properties"])
        self.assertIn("detail", schema["properties"])
        self.assertEqual([{"if": mock.ANY, "then": {"required": ["reason"]}}], schema["allOf"])

    def test_config_schema_is_v2_and_forbids_a_disabled_required_section(self) -> None:
        schema = json.loads((self.CONTRACTS / "config.schema.json").read_text())
        self.assertEqual(2, schema["properties"]["version"]["const"])
        self.assertNotIn("topics", schema["properties"])
        for key in ("sections", "narrator", "project_roots"):
            self.assertIn(key, schema["properties"])
        rule = schema["properties"]["sections"]["items"]["allOf"][0]
        self.assertEqual({"const": True}, rule["then"]["properties"]["enabled"])

    def test_shipped_example_matches_the_documented_section_set(self) -> None:
        example = json.loads(
            (Path(__file__).parents[2] / "assets" / "example-config.v2.json").read_text()
        )
        self.assertEqual(2, example["version"])
        self.assertEqual(
            [("dev-activity", True), ("fleet-health", False),
             ("pr-maintenance", False), ("report-delivery", True)],
            [(section["id"], section["required"]) for section in example["sections"]],
        )
        self.assertTrue(all(Path(root).is_absolute() for root in example["project_roots"]))


class LegacyArtifactTests(unittest.TestCase):
    def test_a_v1_artifact_no_longer_validates(self) -> None:
        legacy = copy.deepcopy(local_artifact("2099-01-01T00:00:00Z"))
        legacy["schema_version"] = 1
        legacy.pop("metrics")
        legacy.pop("detail")
        legacy["findings"] = []
        legacy["sources"] = []
        with self.assertRaises(reportctl.ConfigError):
            reportctl_contracts.validate_section_artifact(legacy, "dev-activity")


if __name__ == "__main__":
    unittest.main()
