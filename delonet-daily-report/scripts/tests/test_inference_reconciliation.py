from __future__ import annotations

import copy
import datetime as dt
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config
from test_reportctl import reportctl

reportctl_inference = __import__("reportctl_inference")


def native_jobs(value: dict) -> list[dict]:
    return [
        {
            "id": f"native-{index}",
            **job,
            "provider": None,
            "model": None,
            "base_url": None,
            "repeat": {"times": job["repeat_times"], "completed": job["repeat_completed"]},
        }
        for index, job in enumerate(reportctl.desired_jobs(value), 1)
    ]


def created_job(action: dict, *, staged: bool, enabled: bool) -> dict:
    return reportctl.normalize_job(
        {
            **action,
            "id": "new-job",
            "schedule": (
                {
                    "kind": "once",
                    "run_at": "2099-12-31T23:59:59+00:00",
                    "display": "once at 2099-12-31 23:59:59 UTC",
                }
                if staged
                else action["schedule"]
            ),
            "prompt": reportctl_inference.STAGING_PROMPT if staged else action["prompt"],
            "enabled": enabled,
            "provider": None,
            "model": None,
            "base_url": None,
            "repeat": {
                "times": 1 if staged else action["repeat_times"],
                "completed": 0,
            },
        }
    )


class InferenceReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = config(__import__("pathlib").Path("/tmp/ddr-inference-test"))

    def test_native_snapshots_are_idempotent_and_mismatch_recreates_once(self) -> None:
        observed = native_jobs(self.value)
        self.assertEqual([], reportctl.reconciliation_plan(self.value, observed))
        observed[0]["provider_snapshot"] = "openrouter"
        observed[0]["model_snapshot"] = None
        first = reportctl.reconciliation_plan(self.value, observed)
        second = reportctl.reconciliation_plan(self.value, observed)
        self.assertEqual(first, second)
        recreates = [action for action in first if action["action"] == "recreate"]
        self.assertEqual(1, len(recreates))
        self.assertEqual(observed[0]["id"], recreates[0]["id"])
        self.assertEqual("openai-codex", recreates[0]["provider_snapshot"])
        self.assertEqual("gpt-5.4", recreates[0]["model_snapshot"])
        repaired = copy.deepcopy(observed)
        repaired[0]["provider_snapshot"] = "openai-codex"
        repaired[0]["model_snapshot"] = "gpt-5.4"
        self.assertEqual([], reportctl.reconciliation_plan(self.value, repaired))

    def test_report_config_requires_explicit_inference_pin(self) -> None:
        invalid = copy.deepcopy(self.value)
        invalid.pop("inference")
        with self.assertRaisesRegex(reportctl.ConfigError, "missing keys.*inference"):
            reportctl.validate_config(invalid)

    def test_paused_recreate_has_no_due_window_for_concurrent_ticker(self) -> None:
        value = copy.deepcopy(self.value)
        value["topics"][0]["enabled"] = False
        observed = native_jobs(value)
        target = next(job for job in observed if job["name"].startswith("ddr:journal:"))
        target["provider_snapshot"] = "openrouter"
        target["model_snapshot"] = None
        action = next(
            item
            for item in reportctl.reconciliation_plan(value, observed)
            if item["name"] == target["name"]
        )
        self.assertEqual("recreate", action["action"])
        self.assertFalse(action["enabled"])
        old = reportctl.normalize_job(target)
        staged = created_job(action, staged=True, enabled=False)
        self.assertEqual(reportctl_inference.STAGING_SCHEDULE, staged["schedule"])
        created = created_job(action, staged=False, enabled=False)
        stable_states = [[old], [], [], [staged], [created]]

        def command_result(command, **_kwargs):
            stdout = "Created job: new-job\n" if command[2] == "create" else ""
            return subprocess.CompletedProcess(command, 0, stdout, "")

        with (
            mock.patch.object(reportctl, "read_stable_live_jobs", side_effect=stable_states),
            mock.patch.object(
                reportctl_inference, "run_command", side_effect=command_result
            ) as run,
        ):
            reportctl.apply_plan([action], value)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(
            ["remove", "create", "pause", "edit"],
            [command[2] for command in commands],
        )
        self.assertNotIn("run", [part for command in commands for part in command])
        self.assertNotIn("--provider", commands[1])
        self.assertNotIn("--model", commands[1])
        staging_at = dt.datetime.fromisoformat(commands[1][3].replace("Z", "+00:00"))
        self.assertGreater(staging_at, dt.datetime.now(dt.UTC) + dt.timedelta(days=3650))
        self.assertEqual(reportctl_inference.STAGING_PROMPT, commands[1][4])
        self.assertEqual("pause", commands[2][2])
        self.assertEqual("1", commands[1][commands[1].index("--repeat") + 1])
        self.assertEqual("0", commands[3][commands[3].index("--repeat") + 1])

    def test_finite_repeat_is_recreated_and_infinite_is_idempotent(self) -> None:
        observed = native_jobs(self.value)
        observed[0]["repeat"] = {"times": 3, "completed": 1}
        plan = reportctl.reconciliation_plan(self.value, observed)
        recreate = next(item for item in plan if item["name"] == observed[0]["name"])
        self.assertEqual("recreate", recreate["action"])
        normalized = [reportctl.normalize_job(job) for job in observed]
        issues = reportctl.recurrence_issues(normalized)
        self.assertEqual(observed[0]["name"], issues[0]["name"])
        self.assertIn("repeat.times=3", issues[0]["reason"])
        repaired = copy.deepcopy(observed)
        repaired[0]["repeat"] = {"times": None, "completed": 0}
        self.assertEqual([], reportctl.reconciliation_plan(self.value, repaired))

    def test_live_read_preserves_finite_repeat_and_coalesces_to_four_recreates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = copy.deepcopy(self.value)
            value["daily"]["workdir"] = str(root)
            base = value["topics"][0]
            value["topics"] = []
            for topic_id in ("nightly-pr-maintenance", "hermes-fleet-health", "report-delivery-health"):
                topic = copy.deepcopy(base)
                topic["id"] = topic_id
                topic["title"] = topic_id
                value["topics"].append(topic)
            raw_jobs = []
            for index, desired in enumerate(reportctl.desired_jobs(value), 1):
                raw = {
                    **desired,
                    "id": f"native-{index}",
                    "schedule": {"kind": "cron", "expr": desired["schedule"]},
                    "repeat": {"times": 1, "completed": 0},
                    "provider": None,
                    "model": None,
                    "base_url": None,
                }
                raw.pop("repeat_times")
                raw.pop("repeat_completed")
                raw_jobs.append(raw)
            (root / "cron").mkdir()
            (root / "cron/jobs.json").write_text(json.dumps({"jobs": raw_jobs}))
            with mock.patch.dict(os.environ, {"HERMES_HOME": str(root)}, clear=False):
                live = reportctl.read_live_jobs()
                self.assertEqual(live, [reportctl.normalize_job(job) for job in live])
                self.assertTrue(all(job["repeat_times"] == 1 for job in live))
                plan = reportctl.reconciliation_plan(value, live)
                self.assertEqual(4, len(plan))
                self.assertEqual({"recreate"}, {action["action"] for action in plan})
                self.assertEqual(
                    {job["name"] for job in live}, {action["name"] for action in plan}
                )
                self.assertEqual(live, reportctl.observed_jobs(None))

                repaired = copy.deepcopy(raw_jobs)
                for job in repaired:
                    job["repeat"] = {"times": None, "completed": 0}
                (root / "cron/jobs.json").write_text(json.dumps({"jobs": repaired}))
                self.assertEqual([], reportctl.reconciliation_plan(value, reportctl.read_live_jobs()))

    def test_legacy_missing_or_null_repeat_normalizes_to_infinite(self) -> None:
        desired = reportctl.desired_jobs(self.value)[0]
        base = {"id": "legacy", **desired}
        base.pop("repeat_times")
        base.pop("repeat_completed")
        self.assertIsNone(reportctl.normalize_job(base)["repeat_times"])
        base["repeat"] = None
        self.assertIsNone(reportctl.normalize_job(base)["repeat_times"])

    def test_infinite_post_run_progress_is_history_not_drift(self) -> None:
        observed = native_jobs(self.value)
        observed[0]["repeat"] = {"times": None, "completed": 7}
        once = reportctl.normalize_job(observed[0])
        twice = reportctl.normalize_job(once)
        self.assertEqual(7, twice["repeat_completed"])
        self.assertEqual([], reportctl.recurrence_issues([twice]))
        self.assertEqual([], reportctl.reconciliation_plan(self.value, observed))

    def test_safe_prerun_scripts_are_controller_owned(self) -> None:
        value = copy.deepcopy(self.value)
        value["topics"][0]["script"] = "ddr-journal-ai-agents.py"
        value["daily"]["script"] = "ddr-daily-input.py"
        reportctl.validate_config(value)
        actions = reportctl.reconciliation_plan(value, [])
        commands = {action["name"]: reportctl.action_command(action) for action in actions}
        self.assertIn("ddr-journal-ai-agents.py", commands["ddr:journal:ai-agents"])
        self.assertIn("ddr-daily-input.py", commands["ddr:daily"])
        value["topics"][0]["script"] = "../escape.py"
        with self.assertRaisesRegex(reportctl.ConfigError, "safe scripts-directory"):
            reportctl.validate_config(value)

    def test_enabled_create_resumes_only_after_staging_and_desired_postchecks(self) -> None:
        action = reportctl.reconciliation_plan(self.value, [native_jobs(self.value)[0]])[0]
        staged = created_job(action, staged=True, enabled=False)
        edited = created_job(action, staged=False, enabled=False)
        resumed = created_job(action, staged=False, enabled=True)

        def command_result(command, **_kwargs):
            stdout = "Created job: new-job\n" if command[2] == "create" else ""
            return subprocess.CompletedProcess(command, 0, stdout, "")

        with (
            mock.patch.object(
                reportctl,
                "read_stable_live_jobs",
                side_effect=[[], [staged], [edited], [resumed]],
            ),
            mock.patch.object(
                reportctl_inference, "run_command", side_effect=command_result
            ) as run,
        ):
            reportctl.apply_plan([action], self.value)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(
            ["create", "pause", "edit", "resume"],
            [command[2] for command in commands],
        )

    def test_recreate_race_aborts_before_create(self) -> None:
        observed = native_jobs(self.value)
        observed[0]["provider_snapshot"] = "openrouter"
        action = reportctl.reconciliation_plan(self.value, observed)[0]
        old = reportctl.normalize_job(observed[0])
        intruder = {**old, "id": "intruder"}
        with (
            mock.patch.object(reportctl, "read_stable_live_jobs", side_effect=[[old], [intruder]]),
            mock.patch.object(
                reportctl_inference,
                "run_command",
                return_value=subprocess.CompletedProcess([], 0, "", ""),
            ) as run,
        ):
            with self.assertRaisesRegex(reportctl.ConfigError, "changed unexpectedly"):
                reportctl.apply_plan([action], self.value)
        self.assertEqual(1, run.call_count)
        self.assertEqual("remove", run.call_args.args[0][2])

    def test_fresh_create_requires_expected_snapshots(self) -> None:
        action = reportctl.reconciliation_plan(self.value, [native_jobs(self.value)[0]])[0]
        self.assertEqual("create", action["action"])
        bad = created_job(action, staged=True, enabled=False)
        bad["provider_snapshot"] = None
        bad["model_snapshot"] = None
        with (
            mock.patch.object(
                reportctl, "read_stable_live_jobs", side_effect=[[], [bad], [bad], []]
            ),
            mock.patch.object(
                reportctl_inference,
                "run_command",
                side_effect=lambda command, **_kwargs: subprocess.CompletedProcess(
                    command,
                    0,
                    "Created job: new-job\n" if command[2] == "create" else "",
                    "",
                ),
            ) as run,
        ):
            with self.assertRaisesRegex(reportctl.ConfigError, "unexpected inference"):
                reportctl.apply_plan([action], self.value)
        self.assertEqual(
            ["create", "pause", "pause", "remove"],
            [call.args[0][2] for call in run.call_args_list],
        )

    def test_cleanup_failure_is_aggregated(self) -> None:
        action = reportctl.reconciliation_plan(self.value, [native_jobs(self.value)[0]])[0]
        bad = created_job(action, staged=True, enabled=False)
        bad["provider_snapshot"] = None

        def fail_remove(command, **_kwargs):
            if command[2] == "remove":
                raise reportctl.ConfigError("forced remove failure")
            stdout = "Created job: new-job\n" if command[2] == "create" else ""
            return subprocess.CompletedProcess(command, 0, stdout, "")

        with (
            mock.patch.object(reportctl, "read_stable_live_jobs", side_effect=[[], [bad], [bad]]),
            mock.patch.object(reportctl_inference, "run_command", side_effect=fail_remove),
        ):
            with self.assertRaisesRegex(
                reportctl.ConfigError, "cleanup failed.*forced remove failure"
            ):
                reportctl.apply_plan([action], self.value)

    def test_health_inference_flags_null_and_mismatch(self) -> None:
        observed = [reportctl.normalize_job(job) for job in native_jobs(self.value)]
        observed[0]["provider_snapshot"] = None
        observed[1]["model_snapshot"] = "wrong-model"
        issues = reportctl.inference_issues(self.value, observed, reportctl.managed)
        self.assertEqual(2, len(issues))
        self.assertIn("provider_snapshot=null", issues[0]["reason"])
        self.assertIn("model_snapshot=wrong-model", issues[1]["reason"])


if __name__ == "__main__":
    unittest.main()
