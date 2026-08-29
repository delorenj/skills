"""Stage S3/S4 regressions: manifest, publish, narrator, and the emitted event.

Every test here exists because of one specific way this pipeline's predecessor
told a lie: it enumerated section files instead of config (so a missing section
vanished), it hardcoded ``outcome.status="complete"`` in the event it published,
and it accepted a command's own claim of success. Nothing below asserts that the
happy path is pretty; they assert that the unhappy paths are *recorded*.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config, local_artifact
from test_reportctl import reportctl, reportctl_runtime  # noqa: F401  (path setup)

import narrate as narrator  # noqa: E402
import run as runner  # noqa: E402
from collectors.base import SectionResult  # noqa: E402

STUB_PREFIX = "collectors.stub_"


def register_stub(name: str, factory) -> str:
    """Install a collector module in-process, so no test touches the real machine."""
    module_name = f"{STUB_PREFIX}{name}"
    module = types.ModuleType(module_name)
    module.collect = factory
    sys.modules[module_name] = module
    return f"stub_{name}"


def complete_collector(section_cfg, report_date, config_value=None):
    return SectionResult(
        id=section_cfg["id"],
        status="complete",
        summary=f"{section_cfg['id']} read every source for {report_date}.",
        metrics={"items": 3},
        detail=[f"{section_cfg['id']} line one", f"{section_cfg['id']} line two"],
    )


def failing_collector(section_cfg, report_date, config_value=None):
    return SectionResult(
        id=section_cfg["id"],
        status="failed",
        reason="source unreachable at 127.0.0.1:9 (ECONNREFUSED)",
        summary=f"{section_cfg['id']} collected nothing.",
    )


def raising_collector(section_cfg, report_date, config_value=None):
    raise RuntimeError("collector exploded")


def leaky_collector(section_cfg, report_date, config_value=None):
    result = SectionResult(
        id=section_cfg["id"],
        status="complete",
        summary="leaky section",
        metrics={"items": 1},
        detail=["visible line"],
    )
    # A field no contract names. It must not survive into the artifact or the
    # narrator payload -- that is what the structural allowlist is for.
    result.smuggled_payload = "MARKER-DO-NOT-LEAK"  # type: ignore[attr-defined]
    return result


class PipelineCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.value = config(self.root)
        self.mirror = self.root / "mirror"
        self._env = mock.patch.dict(os.environ, {"DDR_MIRROR_DIR": str(self.mirror)})
        self._env.start()
        self.date = "2026-08-17"

    def tearDown(self) -> None:
        self._env.stop()
        self.temporary.cleanup()

    def with_collectors(self, first: str, second: str) -> dict:
        value = copy.deepcopy(self.value)
        value["sections"][0]["collector"] = first
        value["sections"][1]["collector"] = second
        return value

    def run_pipeline(self, value: dict, **kwargs):
        kwargs.setdefault("narrate_enabled", False)
        kwargs.setdefault("emit", False)
        return runner.run_report(value, self.date, **kwargs)

    def sections_dir(self, value: dict) -> Path:
        return Path(value["artifact_dir"]) / self.date / "sections"


class ManifestTests(PipelineCase):
    def test_manifest_is_enumerated_from_config_not_from_disk(self) -> None:
        value = self.with_collectors(
            register_stub("ok_a", complete_collector), register_stub("ok_b", complete_collector)
        )
        # A stray file that config knows nothing about must not become a section.
        outcome, code = self.run_pipeline(value)
        stray = self.sections_dir(value) / "ghost-section.json"
        stray.write_text(json.dumps(local_artifact("2099-01-01T00:00:00Z", "ghost-section")))
        outcome, code = self.run_pipeline(value)
        self.assertEqual(0, code)
        self.assertEqual(["dev-activity", "fleet-health"], list(outcome["manifest"]["sections"]))
        manifest = json.loads(Path(outcome["manifest"]["path"]).read_text())
        self.assertNotIn("ghost-section", [item["id"] for item in manifest["sections"]])

    def test_an_uncollected_section_is_reported_missing_not_dropped(self) -> None:
        value = self.with_collectors(
            register_stub("ok_c", complete_collector), register_stub("ok_d", complete_collector)
        )
        self.run_pipeline(value)
        (self.sections_dir(value) / "fleet-health.json").unlink()
        outcome, code = self.run_pipeline(value, wanted=["dev-activity"])
        self.assertEqual("missing", outcome["manifest"]["sections"]["fleet-health"])
        self.assertEqual("complete", outcome["manifest"]["sections"]["dev-activity"])
        # Derived from the manifest alone, independently of whether narration
        # ran: a section that was never written makes the report partial.
        self.assertEqual("partial", outcome["section_status"])
        self.assertEqual("partial", outcome["status"])
        self.assertEqual(0, code)
        manifest = json.loads(Path(outcome["manifest"]["path"]).read_text())
        entry = next(item for item in manifest["sections"] if item["id"] == "fleet-health")
        self.assertEqual("file absent", entry["reason"])

    def test_a_missing_required_section_fails_the_run(self) -> None:
        value = self.with_collectors(
            register_stub("ok_e", complete_collector), register_stub("ok_f", complete_collector)
        )
        self.run_pipeline(value)
        (self.sections_dir(value) / "dev-activity.json").unlink()
        outcome, code = self.run_pipeline(value, wanted=["fleet-health"])
        self.assertEqual("missing", outcome["manifest"]["sections"]["dev-activity"])
        # Required, and absent. "partial" would exit 0 over it.
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)

    def test_a_corrupt_artifact_is_invalid_not_ignored(self) -> None:
        value = self.with_collectors(
            register_stub("ok_g", complete_collector), register_stub("ok_h", complete_collector)
        )
        self.run_pipeline(value)
        (self.sections_dir(value) / "fleet-health.json").write_text("{not json")
        outcome, _ = self.run_pipeline(value, wanted=["dev-activity"])
        self.assertEqual("invalid", outcome["manifest"]["sections"]["fleet-health"])

    def test_a_stale_artifact_is_reported_stale(self) -> None:
        value = self.with_collectors(
            register_stub("ok_i", complete_collector), register_stub("ok_j", complete_collector)
        )
        self.run_pipeline(value)
        path = self.sections_dir(value) / "fleet-health.json"
        artifact = json.loads(path.read_text())
        artifact["fresh_until"] = "2000-01-01T00:00:00Z"
        path.write_text(json.dumps(artifact))
        outcome, _ = self.run_pipeline(value, wanted=["dev-activity"])
        self.assertEqual("stale", outcome["manifest"]["sections"]["fleet-health"])

    def test_a_crashing_collector_degrades_the_run_and_stays_in_the_manifest(self) -> None:
        value = self.with_collectors(
            register_stub("ok_k", complete_collector), register_stub("boom", raising_collector)
        )
        outcome, code = self.run_pipeline(value)
        self.assertEqual("failed", outcome["manifest"]["sections"]["fleet-health"])
        self.assertEqual(0, code)
        artifact = json.loads((self.sections_dir(value) / "fleet-health.json").read_text())
        self.assertIn("RuntimeError", artifact["reason"])


class DerivedStatusTests(PipelineCase):
    def test_optional_failure_degrades_the_run_to_partial_but_never_to_failed(self) -> None:
        value = self.with_collectors(
            register_stub("ok_l", complete_collector), register_stub("bad_a", failing_collector)
        )
        outcome, code = self.run_pipeline(value)
        # The required section completed, so this is not a failed run -- but a
        # configured section was lost, so it is not a complete one either.
        self.assertEqual("partial", outcome["section_status"])
        self.assertEqual("partial", outcome["status"])
        self.assertEqual(0, code)
        report = json.loads(Path(outcome["published"]["report_json"]).read_text())
        self.assertEqual(["fleet-health"], report["coverage"]["degraded"])

    def test_required_failure_fails_the_run_and_exits_non_zero(self) -> None:
        # The plan's failure-injection acceptance test, in miniature: the
        # required section's source is unreachable. A run that publishes a
        # report without the section it was told it could not do without has
        # not succeeded, and must not hand a cron agent a zero.
        value = self.with_collectors(
            register_stub("bad_b", failing_collector), register_stub("ok_m", complete_collector)
        )
        outcome, code = self.run_pipeline(value)
        self.assertEqual("failed", outcome["section_status"])
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)
        self.assertNotEqual(0, code)

    def test_nothing_succeeded_is_failed_and_exits_non_zero(self) -> None:
        value = self.with_collectors(
            register_stub("bad_c", failing_collector), register_stub("bad_d", failing_collector)
        )
        outcome, code = self.run_pipeline(value)
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)
        self.assertNotEqual(0, code)


class PublishTests(PipelineCase):
    def test_publish_is_verified_not_assumed(self) -> None:
        value = self.with_collectors(
            register_stub("ok_n", complete_collector), register_stub("ok_o", complete_collector)
        )
        outcome, _ = self.run_pipeline(value)
        self.assertTrue(outcome["published"]["verified"])
        marker = json.loads(Path(outcome["published"]["commit_marker"]).read_text())
        self.assertEqual(self.date, marker["report_date"])
        self.assertEqual(outcome["published"]["generation"], marker["generation"])

    def test_a_failed_pointer_swap_leaves_the_previous_generation_current(self) -> None:
        value = self.with_collectors(
            register_stub("ok_p", complete_collector), register_stub("ok_q", complete_collector)
        )
        first, _ = self.run_pipeline(value)
        marker_path = Path(first["published"]["commit_marker"])
        before = json.loads(marker_path.read_text())
        original = reportctl_runtime.os.replace

        def fail_pointer(source, destination):
            if str(destination).endswith("current.json"):
                raise OSError("forced pointer failure")
            return original(source, destination)

        with mock.patch.object(reportctl_runtime.os, "replace", side_effect=fail_pointer):
            outcome, code = self.run_pipeline(value)
        self.assertEqual(runner.EXIT_ERROR, code)
        self.assertEqual("failed", outcome["status"])
        self.assertIn("publish failed", " ".join(outcome["caveats"]))
        self.assertEqual(before, json.loads(marker_path.read_text()))
        current = marker_path.parent / "generations" / before["generation"]
        self.assertTrue((current / "report.json").is_file())

    def test_mirror_copies_exactly_the_report_pair(self) -> None:
        value = self.with_collectors(
            register_stub("ok_r", complete_collector), register_stub("ok_s", complete_collector)
        )
        outcome, _ = self.run_pipeline(value, mirror=True)
        self.assertTrue(outcome["mirror"]["ok"], outcome["mirror"])
        target = self.mirror / self.date
        self.assertEqual({"report.md", "report.json"}, {item.name for item in target.iterdir()})
        mirrored = json.loads((target / "report.json").read_text())
        published = json.loads(Path(outcome["published"]["report_json"]).read_text())
        self.assertEqual(published, mirrored)

    def test_a_mirror_failure_is_recorded_and_does_not_hide_the_report(self) -> None:
        value = self.with_collectors(
            register_stub("ok_t", complete_collector), register_stub("ok_u", complete_collector)
        )
        # A read-only mirror root: the staged pair cannot be created at all.
        # (A stray file at mirror/<date> is no longer a failure -- the new
        # publish moves whatever is there aside and installs the pair -- so the
        # blocker has to be something the process genuinely cannot write.)
        self.mirror.mkdir(parents=True, exist_ok=True)
        self.mirror.chmod(0o500)
        try:
            outcome, code = self.run_pipeline(value, mirror=True)
        finally:
            self.mirror.chmod(0o700)
        self.assertFalse(outcome["mirror"]["ok"])
        self.assertIn("mirror failed", " ".join(outcome["caveats"]))
        self.assertTrue(outcome["published"]["verified"])
        self.assertEqual(0, code)

    def test_a_second_run_publishes_a_new_generation_and_keeps_the_old_one(self) -> None:
        value = self.with_collectors(
            register_stub("ok_v", complete_collector), register_stub("ok_w", complete_collector)
        )
        first, _ = self.run_pipeline(value)
        second, _ = self.run_pipeline(value)
        self.assertNotEqual(first["published"]["generation"], second["published"]["generation"])
        old = Path(first["published"]["report_json"])
        self.assertTrue(old.is_file())
        marker = json.loads(Path(second["published"]["commit_marker"]).read_text())
        self.assertEqual(second["published"]["generation"], marker["generation"])


class EventTests(PipelineCase):
    def envelope(self, outcome: dict) -> dict:
        return json.loads(Path(outcome["event"]["path"]).read_text())

    def test_every_section_status_in_the_event_comes_from_the_manifest(self) -> None:
        value = self.with_collectors(
            register_stub("ok_x", complete_collector), register_stub("bad_e", failing_collector)
        )
        outcome, _ = self.run_pipeline(value)
        envelope = self.envelope(outcome)
        self.assertEqual(
            "bloodbank.reporting.report.completed", envelope["type"]
        )
        # The defect being fixed: the predecessor wrote "complete" for all four
        # sections on every run, no matter what happened.
        self.assertEqual(
            {"dev-activity": "complete", "fleet-health": "degraded"},
            envelope["data"]["outcome"]["sections"],
        )
        self.assertEqual("partial", envelope["data"]["outcome"]["status"])

    def test_a_fully_complete_run_is_the_only_complete_event(self) -> None:
        value = self.with_collectors(
            register_stub("ok_y", complete_collector), register_stub("ok_z", complete_collector)
        )
        bodies = {
            item["id"]: f"Narrated body for {item['id']}."
            for item in runner.report_plan(value)
            if item["id"] != "coverage-freshness"
        }
        with mock.patch.object(narrator, "invoke", narrator_reply(bodies)):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        envelope = self.envelope(outcome)
        self.assertEqual("complete", outcome["status"])
        self.assertEqual("complete", envelope["data"]["outcome"]["status"])
        self.assertEqual(
            {"dev-activity": "complete", "fleet-health": "complete"},
            envelope["data"]["outcome"]["sections"],
        )

    def test_an_unnarrated_run_never_claims_a_complete_event(self) -> None:
        # Every section completed, but the report was published as partial
        # because narration failed. The v1 envelope derives outcome.status from
        # the sections map, so the degraded narration is named as its own
        # component rather than being rounded up to "complete".
        value = self.with_collectors(
            register_stub("ok_y2", complete_collector), register_stub("ok_z2", complete_collector)
        )
        outcome, _ = self.run_pipeline(value)
        envelope = self.envelope(outcome)
        self.assertEqual("partial", outcome["status"])
        self.assertEqual("partial", envelope["data"]["outcome"]["status"])
        self.assertEqual(
            {
                "dev-activity": "complete",
                "fleet-health": "complete",
                runner.NARRATION_COMPONENT_ID: "degraded",
            },
            envelope["data"]["outcome"]["sections"],
        )
        # The schema only accepts "partial" when some component is degraded.
        self.assertIn("degraded", envelope["data"]["outcome"]["sections"].values())

    def test_the_event_status_always_equals_the_published_report_status(self) -> None:
        value = self.with_collectors(
            register_stub("ok_y3", complete_collector), register_stub("bad_y3", failing_collector)
        )
        outcome, _ = self.run_pipeline(value)
        published = json.loads(Path(outcome["published"]["report_json"]).read_text())
        envelope = self.envelope(outcome)
        self.assertEqual(outcome["status"], envelope["data"]["outcome"]["status"])
        self.assertEqual(["fleet-health"], published["coverage"]["degraded"])

    def test_a_failed_run_never_emits_a_completed_event(self) -> None:
        value = self.with_collectors(
            register_stub("bad_f", failing_collector), register_stub("bad_g", failing_collector)
        )
        outcome, _ = self.run_pipeline(value)
        envelope = self.envelope(outcome)
        self.assertEqual("bloodbank.reporting.report.failed", envelope["type"])
        self.assertNotIn("outcome", envelope["data"])
        self.assertEqual("no_section_completed", envelope["data"]["failure"]["code"])
        self.assertTrue(envelope["data"]["failure"]["redacted"])

    def test_failure_summaries_carry_no_paths_and_stay_bounded(self) -> None:
        value = self.with_collectors(
            register_stub("bad_h", failing_collector), register_stub("bad_i", failing_collector)
        )
        outcome, _ = self.run_pipeline(value)
        summary = self.envelope(outcome)["data"]["failure"]["summary"]
        self.assertNotIn("/", summary)
        self.assertLessEqual(len(summary), 500)
        self.assertIsNotNone(runner.SAFE_SUMMARY_RE.fullmatch(summary))

    def test_artifact_ids_match_the_bloodbank_pattern(self) -> None:
        value = self.with_collectors(
            register_stub("ok_aa", complete_collector), register_stub("ok_ab", complete_collector)
        )
        outcome, _ = self.run_pipeline(value)
        for value_id in self.envelope(outcome)["data"]["artifacts"].values():
            self.assertIsNotNone(runner.ARTIFACT_ID_RE.fullmatch(value_id), value_id)

    def test_no_emit_writes_the_envelope_but_publishes_nothing(self) -> None:
        value = self.with_collectors(
            register_stub("ok_ac", complete_collector), register_stub("ok_ad", complete_collector)
        )
        with mock.patch.object(runner, "emit_event") as publisher:
            outcome, _ = self.run_pipeline(value, emit=False)
        publisher.assert_not_called()
        self.assertFalse(outcome["event"]["emitted"])
        self.assertIn("skipped", outcome["event"])
        self.assertTrue(Path(outcome["event"]["path"]).is_file())

    def test_a_publish_that_fails_reports_the_event_as_unpublished(self) -> None:
        value = self.with_collectors(
            register_stub("ok_ae", complete_collector), register_stub("ok_af", complete_collector)
        )
        with mock.patch.object(
            runner, "emit_event",
            return_value={"published": False, "url": "http://127.0.0.1:3504/x",
                          "status_code": None, "error": "connection refused"},
        ):
            outcome, code = self.run_pipeline(value, emit=True)
        self.assertFalse(outcome["event"]["emitted"])
        self.assertEqual("connection refused", outcome["event"]["error"])
        self.assertEqual(0, code)
        self.assertTrue(outcome["published"]["verified"])

    def test_delivery_is_derived_from_the_mirror_not_assumed(self) -> None:
        value = self.with_collectors(
            register_stub("ok_ag", complete_collector), register_stub("ok_ah", complete_collector)
        )
        delivered, _ = self.run_pipeline(value, mirror=True)
        self.assertEqual("delivered", self.envelope(delivered)["data"]["delivery"]["status"])
        skipped, _ = self.run_pipeline(value, mirror=False)
        block = self.envelope(skipped)["data"]["delivery"]
        self.assertEqual("skipped", block["status"])
        self.assertEqual("mirror_disabled", block["reason"])
        self.assertEqual(0, block["attempts"])


def narrator_reply(bodies: dict[str, str], *, usage: dict | None = None):
    def invoke(prompt, provider, model, reasoning=None):
        invoke.prompt = prompt
        return {
            "stdout": json.dumps({"headline": "h", "lead": next(iter(bodies.values()), "")}),
            "usage": usage if usage is not None else {"model": model, "provider": provider,
                                                      "completed": True, "failed": False},
            "usage_note": None,
            "command": "/stub/hermes",
            "toolsets": narrator.toolsets(),
        }

    return invoke


class NarratorTests(PipelineCase):
    def all_bodies(self, value: dict) -> dict[str, str]:
        return {
            item["id"]: f"Narrated body for {item['id']}."
            for item in runner.report_plan(value)
            if item["id"] != "coverage-freshness"
        }

    def test_a_narrated_run_keeps_the_manifest_status_authoritative(self) -> None:
        value = self.with_collectors(
            register_stub("ok_ai", complete_collector), register_stub("bad_j", failing_collector)
        )
        bodies = self.all_bodies(value)
        bodies["fleet-health"] = "Everything is fine and every section completed."
        with mock.patch.object(narrator, "invoke", narrator_reply(bodies)):
            outcome, code = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual("llm", outcome["narration"]["mode"])
        # Narration succeeded, so nothing degrades the run except the manifest
        # itself -- and the manifest says a section failed.
        self.assertEqual("partial", outcome["status"])
        report = json.loads(Path(outcome["published"]["report_json"]).read_text())
        body = next(item for item in report["sections"] if item["id"] == "fleet-health")["body"]
        # The narrator's rosy prose survives, but the record leads it.
        self.assertTrue(body.startswith("**Status (authoritative): failed**"))
        self.assertIn("source unreachable", body)
        self.assertEqual(["fleet-health"], report["coverage"]["degraded"])
        self.assertEqual(
            "partial", self.envelope_status(outcome)
        )

    def envelope_status(self, outcome: dict) -> str:
        envelope = json.loads(Path(outcome["event"]["path"]).read_text())
        return envelope["data"]["outcome"]["status"]

    def test_the_coverage_table_is_never_written_by_the_narrator(self) -> None:
        """Retired concept, kept as its successor.

        There is no `coverage-freshness` section any more; the table it carried
        now sits in the pipeline-rendered COVERAGE block at the end. It must
        still come from the manifest on every path.
        """
        value = self.with_collectors(register_stub("cov_a", complete_collector),
                                     register_stub("cov_b", complete_collector))
        outcome, _ = self.run_pipeline(value, narrate_enabled=False)
        markdown = Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")
        self.assertIn("| section | status | generated | fresh until | reason |", markdown)
        self.assertRegex(markdown, r"\| dev-activity \| complete \|")

    def test_narrator_failure_falls_back_and_degrades_to_partial(self) -> None:
        value = self.with_collectors(
            register_stub("ok_al", complete_collector), register_stub("ok_am", complete_collector)
        )

        def explode(prompt, provider, model, reasoning=None):
            raise narrator.NarrationError("narrator exited 3: provider unreachable")

        with mock.patch.object(narrator, "invoke", explode):
            outcome, code = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual("fallback", outcome["narration"]["mode"])
        self.assertEqual("partial", outcome["status"])
        self.assertEqual(0, code)
        self.assertIn("provider unreachable", " ".join(outcome["caveats"]))
        self.assertTrue(outcome["published"]["verified"])
        markdown = Path(outcome["published"]["markdown"]).read_text()
        self.assertIn("Deterministic render", markdown)

    def test_a_narrator_that_returns_no_lead_is_a_failure_not_a_gap(self) -> None:
        """Retired concept, kept as its successor.

        The narrator used to write a body per section and omitting one was the
        failure mode. It now writes a single document, so the equivalent is an
        empty or missing lead -- which must fall back, not publish a blank.
        """
        value = self.with_collectors(register_stub("omit_a", complete_collector),
                                     register_stub("omit_b", complete_collector))

        def blank(prompt, provider, model, reasoning=None):
            return {"stdout": json.dumps({"headline": "h", "lead": "   "}),
                    "usage": {"completed": True, "failed": False},
                    "usage_note": None, "command": "/stub/hermes",
                    "toolsets": narrator.toolsets()}

        with mock.patch.object(narrator, "invoke", blank):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual("fallback", outcome["narration"]["mode"])
        self.assertIn("lead", outcome["narration"]["failure"])

    def test_disabled_narrator_is_named_in_the_caveat(self) -> None:
        value = self.with_collectors(
            register_stub("ok_ap", complete_collector), register_stub("ok_aq", complete_collector)
        )
        value["narrator"]["enabled"] = False
        outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual("fallback", outcome["narration"]["mode"])
        self.assertEqual("narrator disabled in config", outcome["narration"]["failure"])
        self.assertEqual("partial", outcome["status"])

    def test_exit_zero_with_a_failed_usage_report_is_still_a_failure(self) -> None:
        with mock.patch.object(narrator.subprocess, "run") as runner_mock:
            runner_mock.return_value = types.SimpleNamespace(
                returncode=0, stdout='{"headline": "h", "lead": ""}', stderr=""
            )
            with tempfile.TemporaryDirectory() as workdir:
                usage = Path(workdir) / f".narrator-usage-{os.getpid()}.json"

                def write_usage(*args, **kwargs):
                    usage.write_text(json.dumps({"completed": False, "failed": True}))
                    return types.SimpleNamespace(
                        returncode=0, stdout='{"headline": "h", "lead": ""}', stderr=""
                    )

                runner_mock.side_effect = write_usage
                with self.assertRaisesRegex(narrator.NarrationError, "usage report"):
                    narrator.invoke("p", "prov", "model", command="/bin/true",
                                    workdir=Path(workdir))

    def test_a_silent_success_with_no_output_is_a_failure(self) -> None:
        with mock.patch.object(narrator.subprocess, "run") as runner_mock:
            runner_mock.return_value = types.SimpleNamespace(returncode=0, stdout="  ", stderr="")
            with tempfile.TemporaryDirectory() as workdir:
                with self.assertRaisesRegex(narrator.NarrationError, "printed nothing"):
                    narrator.invoke("p", "prov", "model", command="/bin/true",
                                    workdir=Path(workdir))

    def test_a_non_zero_exit_names_the_code(self) -> None:
        with mock.patch.object(narrator.subprocess, "run") as runner_mock:
            runner_mock.return_value = types.SimpleNamespace(
                returncode=3, stdout="", stderr="provider exploded"
            )
            with tempfile.TemporaryDirectory() as workdir:
                with self.assertRaisesRegex(narrator.NarrationError, "exited 3"):
                    narrator.invoke("p", "prov", "model", command="/bin/true",
                                    workdir=Path(workdir))

    def test_the_narrator_is_invoked_with_a_contained_toolset(self) -> None:
        # `hermes -z` auto-bypasses approvals, and its default toolset includes
        # terminal/file/code_execution plus every MCP server. The payload carries
        # commit subjects and PR titles this pipeline did not write, so the
        # narrator must never be handed a shell.
        captured = {}

        def record(argv, **kwargs):
            captured["argv"] = list(argv)
            Path(kwargs["cwd"], f".narrator-usage-{os.getpid()}.json").write_text(
                json.dumps({"completed": True, "failed": False})
            )
            return types.SimpleNamespace(
                returncode=0, stdout='{"headline": "h", "lead": "b"}', stderr=""
            )

        with mock.patch.object(narrator.subprocess, "run", side_effect=record):
            with tempfile.TemporaryDirectory() as workdir:
                outcome = narrator.invoke(
                    "p", "prov", "model", command="/bin/true", workdir=Path(workdir)
                )
        argv = captured["argv"]
        self.assertIn("-t", argv)
        self.assertEqual(narrator.DEFAULT_TOOLSETS, argv[argv.index("-t") + 1])
        self.assertNotIn("--yolo", argv)
        self.assertIn("--ignore-rules", argv)
        self.assertEqual(narrator.DEFAULT_TOOLSETS, outcome["toolsets"])

    def test_the_toolset_is_recorded_in_the_narration_metrics(self) -> None:
        value = self.with_collectors(
            register_stub("ok_au", complete_collector), register_stub("ok_av", complete_collector)
        )
        with mock.patch.object(narrator, "invoke", narrator_reply(self.all_bodies(value))):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual(
            narrator.DEFAULT_TOOLSETS, outcome["narration"]["metrics"]["narrator_toolsets"]
        )

    def test_a_model_swap_is_reported_rather_than_hidden(self) -> None:
        value = self.with_collectors(
            register_stub("ok_ar", complete_collector), register_stub("ok_as", complete_collector)
        )
        bodies = self.all_bodies(value)
        usage = {"model": "something-else", "provider": "p", "completed": True, "failed": False}
        with mock.patch.object(narrator, "invoke", narrator_reply(bodies, usage=usage)):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        self.assertTrue(
            any("not the configured" in item for item in outcome["caveats"]), outcome["caveats"]
        )


class NarratorPayloadTests(PipelineCase):
    def test_only_allowlisted_fields_reach_the_prompt(self) -> None:
        value = self.with_collectors(
            register_stub("leaky", leaky_collector), register_stub("ok_at", complete_collector)
        )
        captured = {}

        def invoke(prompt, provider, model, reasoning=None):
            captured["prompt"] = prompt
            return {
                "stdout": json.dumps({"headline": "h", "lead": "body"}),
                "usage": {"model": model, "provider": provider, "completed": True,
                          "failed": False},
                "usage_note": None,
                "command": "/stub/hermes",
            }

        with mock.patch.object(narrator, "invoke", invoke):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        self.assertNotIn("MARKER-DO-NOT-LEAK", captured["prompt"])
        self.assertNotIn("smuggled_payload", captured["prompt"])
        self.assertIn("visible line", captured["prompt"])
        artifact = (
            Path(value["artifact_dir"]) / self.date / "sections" / "dev-activity.json"
        ).read_text()
        self.assertNotIn("MARKER-DO-NOT-LEAK", artifact)

    def test_oversized_payloads_are_truncated_in_band(self) -> None:
        entries = [
            {
                "id": "dev-activity",
                "title": "Developer Activity",
                "status": "complete",
                "reason": "",
                "summary": "big",
                "metrics": {"lines": 900},
                "detail": [f"line {index} " + "x" * 200 for index in range(900)],
                "caveats": [],
                "generated_at": "2026-08-17T10:00:00Z",
                "fresh_until": "2026-08-18T10:00:00Z",
            }
        ]
        payload = narrator.build_payload("2026-08-17", "run-1", entries, cap=20_000)
        self.assertLessEqual(len(json.dumps(payload).encode("utf-8")), 20_000)
        section = payload["sections"][0]
        self.assertLess(len(section.get("detail", [])), 900)
        self.assertTrue(
            any("of 900 detail lines" in item for item in section["caveats"]), section["caveats"]
        )


class TemplateTests(PipelineCase):
    def test_the_static_bottom_line_paragraph_is_gone(self) -> None:
        text = narrator.TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("BOTTOM LINE", text)
        self.assertIn("$coverage_text", text)
        self.assertIn("$overall_status", text)

    def test_the_coverage_block_is_derived_from_the_manifest(self) -> None:
        value = self.with_collectors(
            register_stub("ok_au", complete_collector), register_stub("bad_k", failing_collector)
        )
        outcome, _ = self.run_pipeline(value)
        markdown = Path(outcome["published"]["markdown"]).read_text()
        self.assertIn("1 of 2 enabled sections completed.", markdown)
        self.assertIn("Degraded: fleet-health (failed).", markdown)
        self.assertIn("Required: dev-activity (complete).", markdown)
        self.assertIn("overall status: partial", markdown)

    def test_an_unusable_template_still_renders_a_report(self) -> None:
        value = self.with_collectors(
            register_stub("ok_av", complete_collector), register_stub("ok_aw", complete_collector)
        )
        with mock.patch.object(narrator, "TEMPLATE_PATH", self.root / "absent-template.md"):
            outcome, code = self.run_pipeline(value)
        self.assertEqual(0, code)
        self.assertIn("was unusable", " ".join(outcome["caveats"]))
        self.assertTrue(Path(outcome["published"]["markdown"]).read_text().strip())


class FreshnessTests(PipelineCase):
    def test_fresh_until_comes_from_the_section_max_age(self) -> None:
        value = self.with_collectors(
            register_stub("ok_ax", complete_collector), register_stub("ok_ay", complete_collector)
        )
        value["sections"][0]["max_age_hours"] = 6
        self.run_pipeline(value)
        artifact = json.loads(
            (Path(value["artifact_dir"]) / self.date / "sections" / "dev-activity.json").read_text()
        )
        generated = dt.datetime.fromisoformat(artifact["generated_at"].replace("Z", "+00:00"))
        fresh = dt.datetime.fromisoformat(artifact["fresh_until"].replace("Z", "+00:00"))
        self.assertEqual(dt.timedelta(hours=6), fresh - generated)


if __name__ == "__main__":
    unittest.main()
