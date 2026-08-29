"""Tests for the fleet_health collector.

The property under test throughout is honesty: the collector may report bad
news, but it may never report success it did not achieve. Every assertion about
``status`` is an assertion that the status was *derived* from what was actually
readable.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from reportctl_contracts import ConfigError, validate_section_artifact
from test_fixtures import config as fixture_config

fleet_health = importlib.import_module("collectors.fleet_health")


UNIT_ROWS = [
    {
        "unit": "hermes-alpha-pm-gateway.service",
        "load": "loaded",
        "active": "active",
        "sub": "running",
    },
    {
        "unit": "hermes-alpha-pm-heartbeat.timer",
        "load": "loaded",
        "active": "active",
        "sub": "waiting",
    },
]

TIMER_ROWS = [
    {
        "unit": "hermes-alpha-pm-heartbeat.timer",
        "next": 1_787_100_000_000_000,
        "last": 1_787_000_000_000_000,
        "activates": "hermes-alpha-pm-heartbeat.service",
    },
    {"unit": "unrelated.timer", "next": None, "last": 0, "activates": "unrelated.service"},
]


def fake_systemctl(units: Any = None, timers: Any = None, *, fail: str = ""):
    """Stand in for ``run_command``; never touches the real service manager."""
    units = UNIT_ROWS if units is None else units
    timers = TIMER_ROWS if timers is None else timers

    def call(command: list[str], *, env: Any = None, timeout: int = 0):
        if fail:
            raise ConfigError(fail)
        payload = units if "list-units" in command else timers
        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout=json.dumps(payload), stderr=""
        )

    return call


class FleetFixture:
    """A throwaway ~/.hermes tree. Nothing here touches the real fleet."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.profiles = root / "profiles"
        self.skills = root / "skills"
        self.registry = root / "agents-registry.yaml"
        self.profiles.mkdir(parents=True)
        self.skills.mkdir(parents=True)

    def write_registry(self, body: str | None = None) -> None:
        self.registry.write_text(
            body
            if body is not None
            else (
                "schema_version: 1\n"
                "agents:\n"
                "  alpha-pm:\n"
                "    profile_name: alpha-pm\n"
                "    systemd:\n"
                "      gateway_unit: hermes-alpha-pm-gateway.service\n"
                "      heartbeat_timer: hermes-alpha-pm-heartbeat.timer\n"
            ),
            encoding="utf-8",
        )

    def add_skill(self, name: str) -> Path:
        path = self.skills / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text("# skill\n", encoding="utf-8")
        return path

    def add_broken_skill_link(self, name: str) -> None:
        (self.skills / name).symlink_to(self.root / "gone" / name)

    def add_profile(
        self,
        name: str,
        jobs: Any = (),
        *,
        cron_dir: Path | None = None,
        ticker_age: float | None = 0.0,
        raw_jobs: str | None = None,
    ) -> Path:
        profile = self.profiles / name
        profile.mkdir(parents=True, exist_ok=True)
        target = cron_dir or (profile / "cron")
        target.mkdir(parents=True, exist_ok=True)
        if cron_dir is not None:
            (profile / "cron").symlink_to(cron_dir)
        if raw_jobs is not None:
            (target / "jobs.json").write_text(raw_jobs, encoding="utf-8")
        elif jobs is not None:
            (target / "jobs.json").write_text(
                json.dumps({"jobs": list(jobs), "updated_at": "2026-08-17T00:00:00Z"}),
                encoding="utf-8",
            )
        if ticker_age is not None:
            ticker = target / "ticker_heartbeat"
            ticker.write_text("0\n", encoding="utf-8")
            stamp = ticker.stat().st_mtime - ticker_age
            os.utime(ticker, (stamp, stamp))
        return profile

    def section(self, **options: Any) -> dict[str, Any]:
        merged = {
            "hermes_home": str(self.root),
            "registry_path": str(self.registry),
            "profiles_dir": str(self.profiles),
            "skills_dir": str(self.skills),
        }
        merged.update(options)
        return {
            "id": "fleet-health",
            "title": "Hermes Fleet Health",
            "collector": "fleet_health",
            "required": False,
            "enabled": True,
            "max_age_hours": 24,
            "options": merged,
        }


def job(**overrides: Any) -> dict[str, Any]:
    base = {
        "id": "job1",
        "name": "nightly-thing",
        "prompt": "SENSITIVE-PROMPT-BODY-DO-NOT-LEAK",
        "skills": ["good-skill"],
        "skill": "good-skill",
        "base_url": "https://internal.example/SHOULD-NOT-LEAK",
        "schedule": {"kind": "cron", "expr": "0 6 * * *", "display": "0 6 * * *"},
        "enabled": True,
        "state": "scheduled",
        "next_run_at": "2099-01-01T06:00:00+00:00",
        "last_run_at": "2026-08-18T06:01:15+00:00",
        "last_status": "ok",
        "last_error": None,
    }
    base.update(overrides)
    return base


class FleetHealthTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fleet = FleetFixture(Path(self.temporary.name) / "hermes")

    def run_collect(self, section: dict[str, Any], **kwargs: Any):
        with mock.patch.object(fleet_health, "run_command", fake_systemctl(**kwargs)):
            return fleet_health.collect(section, "2026-08-17", None)

    def artifact(self, result) -> dict[str, Any]:
        artifact = result.to_artifact("run-1", 24)
        return validate_section_artifact(artifact, "fleet-health")

    # --- happy path -------------------------------------------------------- #

    def test_happy_path_reads_every_source_and_reports_complete(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile("alpha-pm", [job()])
        result = self.run_collect(self.fleet.section())
        artifact = self.artifact(result)

        self.assertEqual("complete", artifact["status"])
        self.assertNotIn("reason", artifact)
        metrics = artifact["metrics"]
        self.assertEqual(4, metrics["sources_read"])
        self.assertEqual(0, metrics["sources_failed"])
        self.assertEqual(1, metrics["agents_registered"])
        self.assertEqual(1, metrics["timers_total"])
        self.assertEqual(1, metrics["timers_active"])
        self.assertEqual(0, metrics["timers_failed"])
        self.assertEqual(1, metrics["cron_jobs_total"])
        self.assertEqual(1, metrics["cron_jobs_enabled"])
        self.assertEqual(0, metrics["jobs_with_missing_skill"])
        self.assertEqual(0, metrics["profiles_with_stale_ticker"])
        self.assertEqual(2, metrics["units_total"])

    def test_every_required_metric_is_present(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        for key in (
            "agents_registered",
            "timers_active",
            "timers_failed",
            "cron_jobs_total",
            "cron_jobs_enabled",
            "jobs_with_missing_skill",
            "profiles_with_stale_ticker",
        ):
            self.assertIn(key, artifact["metrics"])

    # --- source unreachable ------------------------------------------------ #

    def test_every_source_unreachable_yields_failed_not_an_exception(self) -> None:
        section = self.fleet.section(
            registry_path=str(self.fleet.root / "nope.yaml"),
            profiles_dir=str(self.fleet.root / "nope"),
        )
        result = self.run_collect(section, fail="Failed to connect to bus")
        artifact = self.artifact(result)

        self.assertEqual("failed", artifact["status"])
        self.assertIn("every fleet source was unreachable", artifact["reason"])
        self.assertEqual(4, artifact["metrics"]["sources_failed"])
        self.assertNotIn("detail", artifact)

    def test_systemd_unreachable_alone_degrades_to_partial(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile("alpha-pm", [job()])
        artifact = self.artifact(
            self.run_collect(self.fleet.section(), fail="missing executable: systemctl")
        )

        self.assertEqual("partial", artifact["status"])
        self.assertIn("systemd-units", artifact["reason"])
        self.assertIn("systemd-timers", artifact["reason"])
        self.assertEqual(2, artifact["metrics"]["sources_read"])
        self.assertEqual(0, artifact["metrics"]["timers_total"])
        self.assertTrue(any("systemd-units unavailable" in item for item in artifact["caveats"]))

    def test_registry_unreadable_alone_degrades_to_partial(self) -> None:
        self.fleet.add_profile("alpha-pm", [])
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual("partial", artifact["status"])
        self.assertIn("agents-registry", artifact["reason"])
        self.assertEqual(0, artifact["metrics"]["agents_registered"])

    def test_malformed_registry_is_partial_not_zero_agents_reported_as_complete(self) -> None:
        self.fleet.write_registry("just a string, not a mapping\n")
        self.fleet.add_profile("alpha-pm", [])
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        self.assertEqual("partial", artifact["status"])
        self.assertIn("agents-registry", artifact["reason"])

    # --- partial data ------------------------------------------------------ #

    def test_unreadable_jobs_file_is_partial_and_named(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", raw_jobs="{ this is not json")
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual("partial", artifact["status"])
        self.assertIn("unreadable cron jobs", artifact["reason"])
        self.assertEqual(1, artifact["metrics"]["profiles_unreadable_jobs"])
        self.assertTrue(any("alpha-pm" in item for item in artifact["caveats"]))

    def test_jobs_file_without_a_jobs_array_is_partial(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", raw_jobs=json.dumps({"updated_at": "now"}))
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        self.assertEqual("partial", artifact["status"])
        self.assertEqual(1, artifact["metrics"]["profiles_unreadable_jobs"])

    def test_profile_without_a_cron_dir_is_recorded_not_dropped(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        (self.fleet.profiles / "bare-pm").mkdir()
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual("complete", artifact["status"])
        self.assertEqual(2, artifact["metrics"]["profiles_scanned"])
        self.assertEqual(1, artifact["metrics"]["profiles_without_cron_dir"])

    # --- the 2026-08-18 failure -------------------------------------------- #

    def test_last_status_ok_is_never_treated_as_evidence(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile("alpha-pm", [job()])
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual(1, artifact["metrics"]["jobs_claiming_ok_unverified"])
        self.assertTrue(any("unverified" in line for line in artifact["detail"]))
        self.assertTrue(
            any("not treated as evidence of success" in item for item in artifact["caveats"])
        )

    def test_an_output_file_does_not_upgrade_an_unverified_claim(self) -> None:
        """The run that lied on 2026-08-18 wrote an output file while doing nothing."""
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        profile = self.fleet.add_profile("alpha-pm", [job()])
        output = profile / "cron" / "output" / "job1"
        output.mkdir(parents=True)
        (output / "2026-08-18_06-01-15.md").write_text("skills skipped\n", encoding="utf-8")

        artifact = self.artifact(self.run_collect(self.fleet.section()))
        self.assertEqual(1, artifact["metrics"]["jobs_claiming_ok_unverified"])
        self.assertEqual(0, artifact["metrics"]["jobs_claiming_ok_contradicted"])

    def test_a_dangling_skill_symlink_contradicts_an_ok_claim(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_broken_skill_link("good-skill")
        self.fleet.add_profile("alpha-pm", [job()])
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual(1, artifact["metrics"]["jobs_with_missing_skill"])
        self.assertEqual(1, artifact["metrics"]["jobs_claiming_ok_contradicted"])
        self.assertEqual(0, artifact["metrics"]["jobs_claiming_ok_unverified"])
        self.assertTrue(any("not installed" in line for line in artifact["detail"]))

    def test_a_directory_without_skill_md_does_not_count_as_an_installed_skill(self) -> None:
        self.fleet.write_registry()
        (self.fleet.skills / "good-skill").mkdir()
        self.fleet.add_profile("alpha-pm", [job()])
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        self.assertEqual(1, artifact["metrics"]["jobs_with_missing_skill"])

    def test_a_skill_nested_one_category_deep_resolves(self) -> None:
        self.fleet.write_registry()
        category = self.fleet.skills / "devops"
        (category / "good-skill").mkdir(parents=True)
        (category / "good-skill" / "SKILL.md").write_text("# s\n", encoding="utf-8")
        self.fleet.add_profile("alpha-pm", [job()])
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        self.assertEqual(0, artifact["metrics"]["jobs_with_missing_skill"])

    def test_stale_ticker_is_detected_for_profiles_with_jobs(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile("alpha-pm", [job()], ticker_age=4_000.0)
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual(1, artifact["metrics"]["profiles_with_stale_ticker"])
        self.assertTrue(any("ticker last moved" in line for line in artifact["detail"]))

    def test_absent_ticker_counts_as_stale(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile("alpha-pm", [job()], ticker_age=None)
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual(1, artifact["metrics"]["profiles_with_stale_ticker"])
        self.assertTrue(any("ticker absent" in line for line in artifact["detail"]))

    def test_a_next_run_in_the_past_is_flagged(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile(
            "alpha-pm", [job(next_run_at="2020-01-01T06:00:00+00:00")]
        )
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual(1, artifact["metrics"]["jobs_with_past_next_run"])
        self.assertTrue(any("next run is in the past" in line for line in artifact["detail"]))

    def test_failed_and_missing_units_are_counted(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        units = [
            {
                "unit": "hermes-alpha-pm-gateway.service",
                "load": "loaded",
                "active": "failed",
                "sub": "failed",
            },
            {
                "unit": "hermes-ghost-pm.service",
                "load": "not-found",
                "active": "inactive",
                "sub": "dead",
            },
            {
                "unit": "hermes-alpha-pm-heartbeat.timer",
                "load": "loaded",
                "active": "failed",
                "sub": "dead",
            },
        ]
        artifact = self.artifact(self.run_collect(self.fleet.section(), units=units))

        self.assertEqual(2, artifact["metrics"]["units_failed"])
        self.assertEqual(1, artifact["metrics"]["units_not_found"])
        self.assertEqual(1, artifact["metrics"]["timers_failed"])
        self.assertEqual(0, artifact["metrics"]["timers_active"])
        self.assertEqual(1, artifact["metrics"]["gateway_units_inactive"])

    def test_a_registry_unit_systemd_has_never_heard_of_is_reported(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        artifact = self.artifact(self.run_collect(self.fleet.section(), units=[]))
        self.assertEqual(1, artifact["metrics"]["gateway_units_unknown"])
        self.assertTrue(any("unknown to systemd" in line for line in artifact["detail"]))

    def test_a_registered_agent_without_a_profile_directory_is_reported(self) -> None:
        self.fleet.write_registry(
            "agents:\n  ghost-pm:\n    profile_name: ghost-pm\n    systemd: {}\n"
        )
        self.fleet.add_profile("alpha-pm", [])
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        self.assertEqual(1, artifact["metrics"]["agent_profile_dirs_missing"])
        self.assertTrue(any("profile dir ghost-pm absent" in line for line in artifact["detail"]))

    def test_two_profiles_sharing_one_cron_dir_are_reported(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        shared = Path(self.temporary.name) / "shared-cron"
        self.fleet.add_profile("alpha-pm", [job()], cron_dir=shared)
        self.fleet.add_profile("alpha-pm.bak", [job()], cron_dir=shared)
        artifact = self.artifact(self.run_collect(self.fleet.section()))

        self.assertEqual(1, artifact["metrics"]["duplicate_cron_dirs"])
        self.assertTrue(any("shares its cron dir" in line for line in artifact["detail"]))

    # --- bounding and safety ----------------------------------------------- #

    def test_no_raw_source_payload_reaches_the_artifact(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile(
            "alpha-pm", [job(last_error="TOKEN-SHAPED-ERROR-TEXT", last_status="error")]
        )
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        body = json.dumps(artifact)

        self.assertNotIn("SENSITIVE-PROMPT-BODY-DO-NOT-LEAK", body)
        self.assertNotIn("SHOULD-NOT-LEAK", body)
        self.assertNotIn("TOKEN-SHAPED-ERROR-TEXT", body)
        self.assertIn("last_error recorded", body)

    def test_detail_is_capped_and_says_so(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile(
            "alpha-pm", [job(id=f"job{index}", name=f"job-{index}") for index in range(60)]
        )
        artifact = self.artifact(self.run_collect(self.fleet.section(max_detail_lines=20)))

        self.assertEqual(21, len(artifact["detail"]))
        self.assertIn("detail truncated: showing 20 of", artifact["detail"][-1])

    def test_collect_never_raises_when_a_source_reader_explodes(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        with mock.patch.object(
            fleet_health, "_read_profiles", side_effect=RuntimeError("disk on fire")
        ):
            result = self.run_collect(self.fleet.section())
        artifact = self.artifact(result)

        self.assertEqual("failed", artifact["status"])
        self.assertIn("RuntimeError: disk on fire", artifact["reason"])

    def test_a_malformed_job_entry_is_reported_not_crashed_on(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", raw_jobs=json.dumps({"jobs": ["not-an-object", 7]}))
        artifact = self.artifact(self.run_collect(self.fleet.section()))
        self.assertEqual("partial", artifact["status"])
        self.assertIn("malformed", artifact["reason"])
        self.assertEqual(2, artifact["metrics"]["cron_jobs_total"])
        self.assertEqual(2, artifact["metrics"]["cron_jobs_unreadable"])
        self.assertEqual(0, artifact["metrics"]["cron_jobs_enabled"])

    def test_garbage_options_fall_back_to_defaults_instead_of_failing(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        section = self.fleet.section(
            ticker_stale_seconds="soon", systemctl_timeout_seconds=-4, max_detail_lines=0
        )
        artifact = self.artifact(self.run_collect(section))
        self.assertEqual("complete", artifact["status"])

    def test_unparseable_systemctl_json_is_a_source_failure(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])

        def broken(command: list[str], *, env: Any = None, timeout: int = 0):
            return subprocess.CompletedProcess(command, 0, stdout="{not json", stderr="")

        with mock.patch.object(fleet_health, "run_command", broken):
            result = fleet_health.collect(self.fleet.section(), "2026-08-17", None)
        artifact = self.artifact(result)
        self.assertEqual("partial", artifact["status"])
        self.assertIn("unparseable JSON", artifact["reason"])

    def test_monotonic_timer_stamps_are_reported_as_unknown_not_guessed(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        timers = [{"unit": "hermes-alpha-pm-heartbeat.timer", "next": 42, "last": 0}]
        artifact = self.artifact(self.run_collect(self.fleet.section(), timers=timers))
        self.assertEqual(1, artifact["metrics"]["timers_without_next_elapse"])
        self.assertEqual(1, artifact["metrics"]["timers_never_triggered"])

    # --- contract ---------------------------------------------------------- #

    def test_the_runner_keyword_calling_convention_works(self) -> None:
        """``reportctl collect`` calls ``entry(section, date=..., config=...)``."""
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        with mock.patch.object(fleet_health, "run_command", fake_systemctl()):
            result = fleet_health.collect(self.fleet.section(), date="2026-08-17", config={})
        self.assertEqual("2026-08-17", result.metrics["report_date"])

    def test_the_section_id_is_taken_from_config_not_from_the_collector(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        section = self.fleet.section()
        section["id"] = "renamed-fleet"
        result = self.run_collect(section)
        self.assertEqual("renamed-fleet", result.id)

    def write_config(self) -> Path:
        """A real schema v2 config whose fleet-health section points at the fixture."""
        root = Path(self.temporary.name)
        config = fixture_config(root)
        for section in config["sections"]:
            if section["collector"] == "fleet_health":
                section["options"] = self.fleet.section()["options"]
        path = root / "report.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_cli_reads_the_config_section_and_prints_a_valid_artifact(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_skill("good-skill")
        self.fleet.add_profile("alpha-pm", [job()])
        buffer = io.StringIO()
        with mock.patch.object(fleet_health, "run_command", fake_systemctl()):
            with redirect_stdout(buffer):
                code = fleet_health.main(
                    ["--date", "2026-08-17", "--config", str(self.write_config())]
                )
        artifact = json.loads(buffer.getvalue())

        validate_section_artifact(artifact, "fleet-health")
        self.assertEqual("complete", artifact["status"])
        self.assertEqual(1, artifact["metrics"]["cron_jobs_total"])
        self.assertEqual(0, code)

    def test_cli_exits_non_zero_when_the_collection_was_not_complete(self) -> None:
        self.fleet.write_registry()
        self.fleet.add_profile("alpha-pm", [])
        buffer = io.StringIO()
        with mock.patch.object(fleet_health, "run_command", fake_systemctl(fail="no bus")):
            with redirect_stdout(buffer):
                code = fleet_health.main(
                    ["--date", "2026-08-17", "--config", str(self.write_config())]
                )
        artifact = json.loads(buffer.getvalue())

        validate_section_artifact(artifact, "fleet-health")
        self.assertEqual("partial", artifact["status"])
        self.assertEqual(3, code, "a degraded collection must not exit 0")

    def test_cli_reports_a_broken_config_as_a_failed_artifact(self) -> None:
        bad = Path(self.temporary.name) / "config.json"
        bad.write_text("{ not json", encoding="utf-8")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = fleet_health.main(["--date", "2026-08-17", "--config", str(bad)])
        artifact = json.loads(buffer.getvalue())

        validate_section_artifact(artifact, "fleet-health")
        self.assertEqual("failed", artifact["status"])
        self.assertIn("config unusable", artifact["reason"])
        self.assertEqual(3, code)


if __name__ == "__main__":
    unittest.main()
