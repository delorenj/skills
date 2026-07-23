from __future__ import annotations

import copy
import datetime as dt
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config
from test_reportctl import reportctl, reportctl_runtime


class QualityRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)
        manifest_path = Path(self.value["artifact_dir"]) / "2026-07-15" / "run-manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(self.manifest()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def manifest(self) -> dict:
        return {
            "schema_version": 1,
            "run_id": "run-1",
            "report_date": "2026-07-15",
            "started_at": "2026-07-15T10:00:00Z",
            "completed_at": "2026-07-15T10:01:00Z",
            "sections": [{"id": "ai-agents", "status": "complete", "path": "/tmp/ai.json"}],
        }

    def report(self, title: str) -> dict:
        sections = [
            {
                "id": section["id"],
                "title": section["title"],
                "body": f"Body for {section['title']}",
                "source_urls": [],
            }
            for section in self.value["core_sections"]
        ]
        sections.append(
            {"id": "ai-agents", "title": "AI Agents", "body": "Topic body", "source_urls": []}
        )
        return {
            "schema_version": 1,
            "run_id": "run-1",
            "report_date": "2026-07-15",
            "title": title,
            "generated_at": "2026-07-15T11:00:00Z",
            "sections": sections,
            "coverage": {"complete": ["ai-agents"], "degraded": []},
            "markdown_path": "/pending/report.md",
        }

    def archive(self, title: str) -> dict:
        report_path = self.root / f"{title}.json"
        markdown_path = self.root / f"{title}.md"
        report_path.write_text(json.dumps(self.report(title)), encoding="utf-8")
        markdown_path.write_text(f"# {title}\n", encoding="utf-8")
        return reportctl.archive_report(self.value, str(report_path), str(markdown_path))

    def test_pointer_fsync_failure_retains_referenced_generation(self) -> None:
        first = self.archive("Old")
        old_marker = json.loads(Path(first["commit_marker"]).read_text())
        archive_root = Path(reportctl.archive_paths(self.value, "2026-07-15")["archive_root"])
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
                self.archive("New")
        marker = json.loads((archive_root / "current.json").read_text())
        current = archive_root / "generations" / marker["generation"]
        self.assertNotEqual(old_marker["generation"], marker["generation"])
        self.assertEqual("New", json.loads((current / "report.json").read_text())["title"])
        self.assertEqual("# New\n", (current / "report.md").read_text())

    def test_initial_live_read_race_executes_no_actions(self) -> None:
        home = self.root / "hermes"
        (home / "cron").mkdir(parents=True)
        (home / "skills" / "delonet-daily-report").mkdir(parents=True)
        (home / "skills" / "delonet-daily-report" / "SKILL.md").write_text("skill")
        (home / "config.yaml").write_text(
            "timezone: America/New_York\nmodel:\n  provider: openai-codex\n  default: gpt-5.4\n"
        )
        jobs_path = home / "cron" / "jobs.json"
        jobs_path.write_text(json.dumps({"jobs": []}))
        original_read = reportctl.read_live_jobs

        def read_then_mutate() -> list[dict]:
            jobs = original_read()
            jobs_path.write_text(json.dumps({"jobs": [{"id": "foreign", "name": "other"}]}))
            return jobs

        with (
            mock.patch.dict(
                os.environ, {"HERMES_HOME": str(home), "HERMES_TIMEZONE": ""}, clear=False
            ),
            mock.patch.object(reportctl, "read_live_jobs", side_effect=read_then_mutate),
            mock.patch.object(reportctl, "apply_plan") as apply,
        ):
            with self.assertRaisesRegex(reportctl.ConfigError, "changed during initial read"):
                reportctl.reconcile_live(self.value)
            apply.assert_not_called()

    def test_each_missing_desired_job_produces_one_unique_create(self) -> None:
        value = copy.deepcopy(self.value)
        for topic_id, enabled in (("security", True), ("paused-topic", False)):
            topic = copy.deepcopy(value["topics"][0])
            topic.update({"id": topic_id, "title": topic_id.title(), "enabled": enabled})
            value["topics"].append(topic)
        desired_names = {job["name"] for job in reportctl.desired_jobs(value)}
        creates = [
            action
            for action in reportctl.reconciliation_plan(value, [])
            if action["action"] == "create"
        ]
        create_names = [action["name"] for action in creates]
        self.assertEqual(len(desired_names), len(creates))
        self.assertEqual(desired_names, set(create_names))
        self.assertEqual(len(create_names), len(set(create_names)))
        self.assertTrue(all(reportctl.managed(name) for name in create_names))

    def test_next_run_must_be_the_next_future_daily_occurrence(self) -> None:
        spring_now = dt.datetime(2026, 3, 9, 10, 0, tzinfo=dt.UTC)
        self.assertTrue(
            reportctl.daily_next_run_valid("2026-03-09T11:00:00Z", self.value, spring_now)
        )
        fall_now = dt.datetime(2026, 11, 2, 11, 0, tzinfo=dt.UTC)
        self.assertTrue(
            reportctl.daily_next_run_valid("2026-11-02T12:00:00Z", self.value, fall_now)
        )
        self.assertFalse(
            reportctl.daily_next_run_valid("2020-01-01T12:00:00Z", self.value, spring_now)
        )
        self.assertFalse(
            reportctl.daily_next_run_valid("2030-03-09T12:00:00Z", self.value, spring_now)
        )

    def test_daily_prompt_names_only_active_topics(self) -> None:
        value = copy.deepcopy(self.value)
        paused = copy.deepcopy(value["topics"][0])
        paused.update({"id": "paused-topic", "title": "Paused Topic", "enabled": False})
        value["topics"].append(paused)
        prompt = reportctl.daily_prompt(value)
        self.assertIn("active topics [ai-agents]", prompt)
        self.assertNotIn("paused-topic", prompt)

    def test_schema_urls_reject_userinfo_and_queries(self) -> None:
        contracts = Path(__file__).parents[2] / "assets" / "contracts"
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

        for name in (
            "config.schema.json",
            "section-artifact.schema.json",
            "daily-report.schema.json",
        ):
            collect(json.loads((contracts / name).read_text()))
        self.assertGreaterEqual(len(patterns), 4)
        for pattern in patterns:
            self.assertIsNotNone(re.fullmatch(pattern, "https://example.org/releases/1"))
            self.assertIsNone(re.fullmatch(pattern, "https://user@example.org/releases/1"))
            self.assertIsNone(re.fullmatch(pattern, "https://example.org/releases/1?token=public"))


if __name__ == "__main__":
    unittest.main()
