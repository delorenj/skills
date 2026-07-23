from __future__ import annotations

import copy
import datetime as dt
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config, valid_artifact

SCRIPT = Path(__file__).parents[1] / "reportctl"
LOADER = importlib.machinery.SourceFileLoader("reportctl", str(SCRIPT))
SPEC = importlib.util.spec_from_loader("reportctl", LOADER)
reportctl = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(reportctl)
reportctl_runtime = importlib.import_module("reportctl_runtime")


def observed_from_desired(value: dict) -> list[dict]:
    return [
        {"id": f"job-{index}", **job} for index, job in enumerate(reportctl.desired_jobs(value), 1)
    ]


class ReportctlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)
        self.path = self.root / "report.json"
        self.path.write_text(json.dumps(self.value), encoding="utf-8")
        manifest_path = Path(self.value["artifact_dir"]) / "2026-07-15" / "run-manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(self.valid_manifest()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SCRIPT), "--config", str(self.path), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validation_rejects_duplicate_topics_and_credentials(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid["topics"].append(copy.deepcopy(invalid["topics"][0]))
        with self.assertRaisesRegex(reportctl.ConfigError, "duplicate topic"):
            reportctl.validate_config(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["topics"][0]["sources"] = ["https://user:password@example.org/private"]
        with self.assertRaisesRegex(reportctl.ConfigError, "without userinfo"):
            reportctl.validate_config(invalid)
        for source in ("https://user@example.org/news", "https://example.org/news?api_key=literal"):
            invalid = copy.deepcopy(self.value)
            invalid["topics"][0]["sources"] = [source]
            with self.assertRaisesRegex(reportctl.ConfigError, "userinfo or query"):
                reportctl.validate_config(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["topics"][0]["prompt"] = "Fetch with api_key=literal-secret"
        with self.assertRaisesRegex(reportctl.ConfigError, "secret-like"):
            reportctl.validate_config(invalid)
        for token in (
            "ghp_abcdefghijklmnopqrstuvwxyz1234567890",
            "github_pat_abcdefghijklmnopqrstuvwxyz123456",
            "sk-abcdefghijklmnopqrstuvwxyz123456",
            "xoxb-1234567890-secret",
            "AKIAABCDEFGHIJKLMNOP",
        ):
            invalid = copy.deepcopy(self.value)
            invalid["topics"][0]["prompt"] = f"Use {token}"
            with self.assertRaisesRegex(reportctl.ConfigError, "secret-like"):
                reportctl.validate_config(invalid)
        safe = copy.deepcopy(self.value)
        safe["topics"][0]["prompt"] = "Track token economy research"
        reportctl.validate_config(safe)

    def test_plan_is_stable_and_idempotent(self) -> None:
        desired = observed_from_desired(self.value)
        self.assertEqual([], reportctl.reconciliation_plan(self.value, desired))
        drifted = copy.deepcopy(desired)
        drifted[0]["schedule"] = "0 0 * * *"
        first = reportctl.reconciliation_plan(self.value, drifted)
        second = reportctl.reconciliation_plan(self.value, drifted)
        self.assertEqual(first, second)
        self.assertEqual("edit", first[0]["action"])
        create_plan = reportctl.reconciliation_plan(self.value, [])
        applied = [
            {
                "id": f"applied-{index}",
                **{key: value for key, value in action.items() if key != "action"},
            }
            for index, action in enumerate(create_plan)
        ]
        self.assertEqual([], reportctl.reconciliation_plan(self.value, applied))

    def test_daily_runs_at_seven_am_eastern_and_timezone_is_enforced(self) -> None:
        jobs = reportctl.desired_jobs(self.value)
        daily = next(job for job in jobs if job["name"] == "ddr:daily")
        self.assertEqual("0 7 * * *", daily["schedule"])
        invalid = copy.deepcopy(self.value)
        invalid["timezone"] = "UTC"
        with self.assertRaisesRegex(reportctl.ConfigError, "America/New_York"):
            reportctl.validate_config(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["daily"]["schedule"] = "0 8 * * *"
        with self.assertRaisesRegex(reportctl.ConfigError, "07:00"):
            reportctl.validate_config(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["topics"][0]["schedule"] = "every 2h"
        with self.assertRaisesRegex(reportctl.ConfigError, "daily cron"):
            reportctl.validate_config(invalid)
        with mock.patch.object(
            reportctl_runtime.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0, "", ""),
        ) as run:
            reportctl.apply_plan(
                [{"action": "pause", "id": "job-1", "name": "ddr:daily"}], self.value
            )
            self.assertEqual("America/New_York", run.call_args.kwargs["env"]["HERMES_TIMEZONE"])

    def test_native_hermes_shape_and_skill_drift(self) -> None:
        native = []
        for index, job in enumerate(reportctl.desired_jobs(self.value), 1):
            native.append(
                {
                    **job,
                    "id": f"native-{index}",
                    "schedule": {"kind": "cron", "expr": job["schedule"]},
                    "workdir": None,
                }
            )
        snapshot = self.root / "jobs.json"
        snapshot.write_text(json.dumps({"jobs": native, "updated_at": "now"}))
        observed = reportctl.observed_jobs(str(snapshot))
        self.assertEqual([], reportctl.reconciliation_plan(self.value, observed))
        observed[0]["skills"] = []
        plan = reportctl.reconciliation_plan(self.value, observed)
        self.assertEqual(["delonet-daily-report"], plan[0]["changes"]["skills"])
        self.assertIn("--skill", reportctl.action_command(plan[0]))

    def test_apply_rejects_external_snapshot_and_refreshes_canonical_store(self) -> None:
        snapshot = self.root / "snapshot.json"
        snapshot.write_text("[]")
        result = self.run_cli("reconcile", "--apply", "--jobs", str(snapshot))
        self.assertEqual(2, result.returncode)
        self.assertIn("rejects external", result.stderr)
        home = self.root / "hermes"
        (home / "cron").mkdir(parents=True)
        (home / "skills" / "delonet-daily-report").mkdir(parents=True)
        (home / "skills" / "delonet-daily-report" / "SKILL.md").write_text(
            "---\nname: delonet-daily-report\n---\n"
        )
        (home / "config.yaml").write_text(
            "timezone: America/New_York\nmodel:\n  provider: openai-codex\n  default: gpt-5.4\n"
        )
        native = [
            {**job, "id": f"live-{index}", "schedule": {"kind": "cron", "expr": job["schedule"]}}
            for index, job in enumerate(reportctl.desired_jobs(self.value), 1)
        ]
        (home / "cron" / "jobs.json").write_text(json.dumps({"jobs": native}))
        with (
            mock.patch.dict(
                os.environ, {"HERMES_HOME": str(home), "HERMES_TIMEZONE": ""}, clear=False
            ),
            mock.patch.object(reportctl, "apply_plan") as apply,
        ):
            self.assertEqual([], reportctl.reconcile_live(self.value))
            apply.assert_not_called()
            (home / "cron" / "jobs.json").write_text(json.dumps({"jobs": []}))
            with mock.patch.object(
                reportctl, "jobs_fingerprint", side_effect=["before", "changed"]
            ):
                with self.assertRaisesRegex(reportctl.ConfigError, "changed during"):
                    reportctl.reconcile_live(self.value)

    def test_duplicate_and_stale_jobs_are_removed_without_touching_foreign_jobs(self) -> None:
        jobs = observed_from_desired(self.value)
        jobs.extend(
            [
                {**jobs[0], "id": "zzz-duplicate"},
                {
                    "id": "old",
                    "name": "ddr:journal:deleted",
                    "schedule": "1 1 * * *",
                    "prompt": "old",
                    "enabled": True,
                },
                {
                    "id": "foreign",
                    "name": "backup:daily",
                    "schedule": "2 2 * * *",
                    "prompt": "keep",
                    "enabled": True,
                },
            ]
        )
        plan = reportctl.reconciliation_plan(self.value, jobs)
        self.assertEqual(["remove-duplicate", "remove-stale"], [item["action"] for item in plan])
        self.assertNotIn("foreign", {item.get("id") for item in plan})

    def test_topic_add_pause_resume_remove_is_atomic(self) -> None:
        added = self.run_cli(
            "topic",
            "add",
            "security",
            "Security",
            "--prompt",
            "Track advisories",
            "--schedule",
            "30 6 * * *",
            "--source",
            "https://example.org/security",
        )
        self.assertEqual(0, added.returncode, added.stderr)
        self.assertEqual(2, len(json.loads(self.path.read_text())["topics"]))
        self.assertEqual(0, self.run_cli("topic", "pause", "security").returncode)
        self.assertFalse(json.loads(self.path.read_text())["topics"][1]["enabled"])
        self.assertEqual(0, self.run_cli("topic", "resume", "security").returncode)
        self.assertEqual(0, self.run_cli("topic", "remove", "security").returncode)
        self.assertEqual(
            ["ai-agents"], [item["id"] for item in json.loads(self.path.read_text())["topics"]]
        )

    def test_duplicate_add_does_not_modify_config(self) -> None:
        before = self.path.read_bytes()
        result = self.run_cli(
            "topic", "add", "ai-agents", "Again", "--prompt", "No", "--schedule", "0 0 * * *"
        )
        self.assertEqual(2, result.returncode)
        self.assertEqual(before, self.path.read_bytes())

    def test_stale_section_health(self) -> None:
        date = dt.date.today().isoformat()
        section = Path(reportctl.section_path(self.value, "ai-agents", date))
        section.parent.mkdir(parents=True)
        section.write_text(json.dumps(valid_artifact("2000-01-01T00:00:00Z")), encoding="utf-8")
        health = reportctl.artifact_health(self.value, date)
        self.assertEqual("stale", health[0]["status"])

    def test_strict_nested_contract_and_malformed_health(self) -> None:
        malformed = valid_artifact("2099-01-01T00:00:00Z")
        malformed["findings"][0]["unexpected"] = True
        with self.assertRaisesRegex(reportctl.ConfigError, "contract mismatch"):
            reportctl.validate_section_artifact(malformed, "ai-agents")
        date = dt.date.today().isoformat()
        section = Path(reportctl.section_path(self.value, "ai-agents", date))
        section.parent.mkdir(parents=True)
        section.write_text(json.dumps(malformed), encoding="utf-8")
        self.assertEqual("invalid", reportctl.artifact_health(self.value, date)[0]["status"])
        insecure = valid_artifact("2099-01-01T00:00:00Z")
        insecure["sources"][0]["url"] = "http://example.org/release"
        with self.assertRaisesRegex(reportctl.ConfigError, "invalid"):
            reportctl.validate_section_artifact(insecure, "ai-agents")
        insecure = valid_artifact("2099-01-01T00:00:00Z")
        insecure["findings"][0]["source_urls"] = ["https://example.org/release?token=public"]
        with self.assertRaisesRegex(reportctl.ConfigError, "invalid"):
            reportctl.validate_section_artifact(insecure, "ai-agents")
        leaked = valid_artifact("2099-01-01T00:00:00Z")
        leaked["summary"] = "github_pat_abcdefghijklmnopqrstuvwxyz123456"
        with self.assertRaisesRegex(reportctl.ConfigError, "secret-like"):
            reportctl.validate_section_artifact(leaked, "ai-agents")

    def test_manifest_and_report_cover_active_topics_exactly(self) -> None:
        manifest = {
            "schema_version": 1,
            "run_id": "run-1",
            "report_date": "2026-07-15",
            "started_at": "2026-07-15T10:00:00Z",
            "completed_at": "2026-07-15T10:01:00Z",
            "sections": [{"id": "ai-agents", "status": "complete", "path": "/tmp/ai.json"}],
        }
        self.assertEqual(manifest, reportctl.validate_run_manifest(manifest, self.value))
        duplicate = copy.deepcopy(manifest)
        duplicate["sections"].append(copy.deepcopy(duplicate["sections"][0]))
        with self.assertRaisesRegex(reportctl.ConfigError, "exactly once"):
            reportctl.validate_run_manifest(duplicate, self.value)
        report = self.daily_report("Coverage")
        report["coverage"] = {"complete": ["ai-agents"], "degraded": ["ai-agents"]}
        with self.assertRaisesRegex(reportctl.ConfigError, "partition"):
            reportctl.validate_daily_report(report, self.value)
        report = self.daily_report("Unknown")
        report["coverage"]["complete"] = ["unknown"]
        with self.assertRaisesRegex(reportctl.ConfigError, "partition"):
            reportctl.validate_daily_report(report, self.value)

    def test_core_sections_feed_aggregator_prompt(self) -> None:
        defaults = json.loads(
            (SCRIPT.parent.parent / "assets" / "default-core-sections.json").read_text()
        )
        self.assertEqual(defaults, self.value["core_sections"])
        prompt = reportctl.daily_prompt(self.value)
        positions = [prompt.index(section["id"]) for section in self.value["core_sections"]]
        self.assertEqual(sorted(positions), positions)
        invalid = copy.deepcopy(self.value)
        invalid["core_sections"] = invalid["core_sections"][:-1]
        with self.assertRaisesRegex(reportctl.ConfigError, "coverage-freshness"):
            reportctl.validate_config(invalid)
        invalid = copy.deepcopy(self.value)
        invalid["core_sections"] = [invalid["core_sections"][-1]]
        with self.assertRaisesRegex(reportctl.ConfigError, "shipped defaults"):
            reportctl.validate_config(invalid)

    def test_secret_redaction_is_recursive(self) -> None:
        value = {
            "api_token": "literal",
            "message": "Authorization: Bearer abc.defgh",
            "nested": [{"password": "hunter2"}],
            "secret_env": ["TOKEN_NAME"],
        }
        redacted = reportctl.redact(value)
        self.assertEqual("[REDACTED]", redacted["api_token"])
        self.assertNotIn("abc.defgh", redacted["message"])
        self.assertEqual("[REDACTED]", redacted["nested"][0]["password"])
        self.assertEqual(["TOKEN_NAME"], redacted["secret_env"])
        self.assertNotIn("literal", reportctl.redact("https://example.org/?api_key=literal"))

    def test_archive_paths_are_partitioned(self) -> None:
        paths = reportctl.archive_paths(self.value, "2026-07-15")
        self.assertTrue(paths["archive_root"].endswith("/2026/07/2026-07-15"))
        self.assertTrue(paths["commit_marker"].endswith("/current.json"))
        self.assertTrue(paths["manifest"].endswith("/2026-07-15/run-manifest.json"))

    def test_archive_writes_validated_json_and_markdown_atomically(self) -> None:
        report = self.daily_report("Daily Company Rollup")
        report_file, markdown_file = self.root / "input.json", self.root / "input.md"
        report_file.write_text(json.dumps(report), encoding="utf-8")
        markdown_file.write_text("# Daily Company Rollup\n", encoding="utf-8")
        output = reportctl.archive_report(self.value, str(report_file), str(markdown_file))
        self.assertEqual("# Daily Company Rollup\n", Path(output["markdown"]).read_text())
        archived = json.loads(Path(output["report_json"]).read_text())
        self.assertEqual("report.md", archived["markdown_path"])
        self.assertTrue(Path(output["commit_marker"]).exists())
        self.assertEqual("run-1", json.loads(Path(output["manifest"]).read_text())["run_id"])

    def test_archive_requires_matching_manifest_and_secret_free_markdown(self) -> None:
        report_file, markdown_file = self.root / "match.json", self.root / "match.md"
        report_file.write_text(json.dumps(self.daily_report("Match")))
        markdown_file.write_text("# Match\n")
        manifest_path = Path(self.value["artifact_dir"]) / "2026-07-15" / "run-manifest.json"
        bad = self.valid_manifest()
        bad["run_id"] = "different"
        manifest_path.write_text(json.dumps(bad))
        with self.assertRaisesRegex(reportctl.ConfigError, "match exactly"):
            reportctl.archive_report(self.value, str(report_file), str(markdown_file))
        manifest_path.write_text(json.dumps(self.valid_manifest()))
        markdown_file.write_text("# Match\nsk-abcdefghijklmnopqrstuvwxyz123456\n")
        with self.assertRaisesRegex(reportctl.ConfigError, "Markdown contains"):
            reportctl.archive_report(self.value, str(report_file), str(markdown_file))

    def daily_report(self, title: str) -> dict:
        return {
            "schema_version": 1,
            "run_id": "run-1",
            "report_date": "2026-07-15",
            "title": title,
            "generated_at": "2026-07-15T11:00:00Z",
            "sections": [
                {
                    "id": section["id"],
                    "title": section["title"],
                    "body": f"Body for {section['title']}",
                    "source_urls": [],
                }
                for section in self.value["core_sections"]
            ]
            + [{"id": "ai-agents", "title": "AI Agents", "body": "Topic body", "source_urls": []}],
            "coverage": {"complete": ["ai-agents"], "degraded": []},
            "markdown_path": "/pending/report.md",
        }

    def valid_manifest(self) -> dict:
        return {
            "schema_version": 1,
            "run_id": "run-1",
            "report_date": "2026-07-15",
            "started_at": "2026-07-15T10:00:00Z",
            "completed_at": "2026-07-15T10:01:00Z",
            "sections": [{"id": "ai-agents", "status": "complete", "path": "/tmp/ai.json"}],
        }

    def test_archive_second_commit_failure_never_publishes_marker(self) -> None:
        report_file, markdown_file = self.root / "fail.json", self.root / "fail.md"
        report_file.write_text(json.dumps(self.daily_report("Old")))
        markdown_file.write_text("# Old\n")
        first = reportctl.archive_report(self.value, str(report_file), str(markdown_file))
        old_marker = json.loads(Path(first["commit_marker"]).read_text())
        report_file.write_text(json.dumps(self.daily_report("Failure")))
        markdown_file.write_text("# Failure\n")
        original = reportctl_runtime.os.replace

        def fail_second(source, destination):
            if str(destination).endswith("current.json"):
                raise OSError("forced pointer failure")
            return original(source, destination)

        with mock.patch.object(reportctl_runtime.os, "replace", side_effect=fail_second):
            with self.assertRaises(OSError):
                reportctl.archive_report(self.value, str(report_file), str(markdown_file))
        paths = reportctl.archive_paths(self.value, "2026-07-15")
        self.assertEqual(old_marker, json.loads(Path(paths["commit_marker"]).read_text()))
        old_root = Path(paths["archive_root"]) / "generations" / old_marker["generation"]
        self.assertEqual("# Old\n", (old_root / "report.md").read_text())
        self.assertEqual("Old", json.loads((old_root / "report.json").read_text())["title"])

    def test_archive_concurrency_keeps_pair_consistent(self) -> None:
        errors = []

        def worker(title):
            try:
                report_file, markdown_file = self.root / f"{title}.json", self.root / f"{title}.md"
                report_file.write_text(json.dumps(self.daily_report(title)))
                markdown_file.write_text(f"# {title}\n")
                reportctl.archive_report(self.value, str(report_file), str(markdown_file))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(title,)) for title in ("Alpha", "Beta")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual([], errors)
        paths = reportctl.archive_paths(self.value, "2026-07-15")
        marker = json.loads(Path(paths["commit_marker"]).read_text())
        root = Path(paths["archive_root"]) / "generations" / marker["generation"]
        archived = json.loads((root / "report.json").read_text())
        markdown = (root / "report.md").read_text()
        self.assertIn(archived["title"], markdown)

    def test_health_skips_paused_and_rejects_traversal_date(self) -> None:
        paused = copy.deepcopy(self.value)
        paused["topics"][0]["enabled"] = False
        self.assertEqual([], reportctl.artifact_health(paused, "2026-07-15"))
        with self.assertRaisesRegex(reportctl.ConfigError, "YYYY-MM-DD"):
            reportctl.artifact_health(self.value, "../../etc")

    def test_timezone_preflight_reads_profile_config(self) -> None:
        home = self.root / "hermes"
        home.mkdir()
        (home / "config.yaml").write_text(
            "timezone: America/New_York\nmodel:\n  provider: openai-codex\n  default: gpt-5.4\n"
        )
        (home / "skills" / "delonet-daily-report").mkdir(parents=True)
        (home / "skills" / "delonet-daily-report" / "SKILL.md").write_text("skill")
        with mock.patch.dict(
            os.environ, {"HERMES_HOME": str(home), "HERMES_TIMEZONE": ""}, clear=False
        ):
            reportctl.timezone_preflight(self.value)
            os.environ["HERMES_TIMEZONE"] = "UTC"
            with self.assertRaisesRegex(reportctl.ConfigError, "no conflicting"):
                reportctl.timezone_preflight(self.value)
            os.environ["HERMES_TIMEZONE"] = ""
            (home / "config.yaml").write_text(
                "timezone: America/New_York\nmodel:\n  provider: openrouter\n  default: gpt-5.4\n"
            )
            with self.assertRaisesRegex(reportctl.ConfigError, "profile inference"):
                reportctl.timezone_preflight(self.value)
            (home / "config.yaml").write_text(
                "timezone: UTC\nmodel:\n  provider: openai-codex\n  default: gpt-5.4\n"
            )
            with self.assertRaisesRegex(reportctl.ConfigError, "profile timezone"):
                reportctl.timezone_preflight(self.value)

    def test_subprocess_failures_are_structured(self) -> None:
        with mock.patch.object(
            reportctl_runtime.subprocess, "run", side_effect=FileNotFoundError()
        ):
            with self.assertRaisesRegex(reportctl.ConfigError, "missing executable"):
                reportctl.run_command(["hermes"])
        with mock.patch.object(
            reportctl_runtime.subprocess, "run", side_effect=subprocess.TimeoutExpired("hermes", 30)
        ):
            with self.assertRaisesRegex(reportctl.ConfigError, "timed out"):
                reportctl.run_command(["hermes"])
        error = subprocess.CalledProcessError(
            1, ["hermes"], stderr="failed github_pat_abcdefghijklmnopqrstuvwxyz123456"
        )
        with mock.patch.object(reportctl_runtime.subprocess, "run", side_effect=error):
            with self.assertRaises(reportctl.ConfigError) as raised:
                reportctl.run_command(["hermes"])
        self.assertNotIn("github_pat_", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
